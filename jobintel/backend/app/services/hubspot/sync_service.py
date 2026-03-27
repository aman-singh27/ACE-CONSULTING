"""
HubSpot sync service for batch syncing companies, jobs, deals, and contacts.
"""

import time
import traceback
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.company import Company
from app.models.company_contact import CompanyContact
from app.models.job_posting import JobPosting
from app.services.hubspot.hubspot_client import (
    hubspot_client,
    get_hubspot_api_key,
    create_hubspot_client,
)
from app.services.dedup.name_sanitizer import is_url_like

logger = get_logger(__name__)

# Constants
BD_SIGNAL_TAGS = {"spiking", "new_entrant", "salary_signal"}
MAX_COMPANIES_PER_SYNC = 500
def _normalize_email(email: str | None) -> str | None:
    """Normalize and validate email for HubSpot upsert keys."""
    if not email:
        return None
    normalized = email.strip().lower()
    if not normalized or " " in normalized or normalized.count("@") != 1:
        return None
    local_part, domain_part = normalized.split("@", 1)
    if not local_part or not domain_part:
        return None
    return normalized


def _split_contact_name(full_name: str | None) -> tuple[str, str]:
    """Split a full name into firstname/lastname best-effort values."""
    parts = (full_name or "").strip().split(" ", 1)
    if not parts or not parts[0]:
        return "", ""
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], parts[1]


def _build_contact_properties(
    contact: CompanyContact, normalized_email: str | None = None
) -> Dict[str, str]:
    """Build a HubSpot-safe contact properties payload."""
    firstname, lastname = _split_contact_name(contact.full_name)
    properties: Dict[str, str] = {
        "firstname": firstname,
        "lastname": lastname,
        "jobtitle": contact.title or "",
    }

    if normalized_email:
        properties["email"] = normalized_email
    if contact.phone:
        properties["phone"] = contact.phone
    if contact.linkedin_url:
        # HubSpot's standard contact LinkedIn URL field.
        properties["hs_linkedin_url"] = contact.linkedin_url

    return properties


def _format_bd_tags(tags: list[str]) -> str:
    """Format BD tags into a human-readable string for HubSpot."""
    if not tags:
        return "No signals"

    TAG_LABELS = {
        "spiking": "🔥 Hiring Spike",
        "struggling": "⚠️ Struggling to Fill",
        "new_entrant": "🆕 New Entrant",
        "salary_signal": "💰 Salary Signal",
        "contact_available": "📞 Contact Available",
        "ghost_poster": "👻 Ghost Poster",
    }

    formatted = []
    for tag in tags:
        label = TAG_LABELS.get(tag, tag.replace("_", " ").title())
        formatted.append(label)

    return " | ".join(formatted)


def _signal_strength(tags: list[str]) -> str:
    """Return a plain-English signal strength label based on tag count."""
    HIGH_VALUE_TAGS = {"spiking", "salary_signal", "new_entrant"}
    high_count = sum(1 for t in tags if t in HIGH_VALUE_TAGS)

    if high_count >= 2:
        return "🔴 High Priority — multiple strong signals"
    elif high_count == 1:
        return "🟡 Medium Priority — one strong signal"
    elif tags:
        return "🟢 Low Priority — weak signals only"
    else:
        return "⚪ No signals"


def _build_note_body(
    company_name: str,
    jobs: List[JobPosting],
    bd_tags: List[str]
) -> str:
    """
    Build a clean plain-text note body for HubSpot.
    Format:

    === JobIntel Hiring Signal Report ===
    Company: {company_name}
    BD Tags: {", ".join(bd_tags) or "None"}
    Synced: {today's date}

    Recent Job Postings (last 7 days):
    • {job.title} — {job.location_raw or "Location N/A"} — {platform} — {relative_date}
    • ...
    (up to 10 jobs, sorted by posted_at desc)

    If no jobs: show "No recent job postings found."
    """
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    note_lines = [
        "=== JobIntel Hiring Signal Report ===",
        f"Company: {company_name}",
        f"BD Signals: {_format_bd_tags(bd_tags)}",
        f"Synced: {today}",
        "",
        f"Signal Strength: {_signal_strength(bd_tags)}",
        "",
        "Recent Job Postings (last 7 days):",
    ]

    if not jobs:
        note_lines.append("No recent job postings found.")
    else:
        for job in jobs[:10]:  # Cap at 10 jobs
            try:
                if job.posted_at is None:
                    relative_date = "date unknown"
                else:
                    # Ensure timezone-aware for comparison
                    posted = job.posted_at
                    if posted.tzinfo is None:
                        posted = posted.replace(tzinfo=timezone.utc)
                    days_ago = (datetime.now(timezone.utc) - posted).days
                    if days_ago == 0:
                        relative_date = "today"
                    elif days_ago == 1:
                        relative_date = "yesterday"
                    elif days_ago <= 6:
                        relative_date = f"{days_ago} days ago"
                    else:
                        relative_date = posted.strftime("%b %d")
            except Exception:
                relative_date = "date unknown"

            location = job.location_raw or "Location N/A"
            note_lines.append(
                f"• {job.title} — {location} — {job.source_platform} — {relative_date}"
            )

    return "\n".join(note_lines)


async def sync_companies_to_hubspot(
    db: AsyncSession,
    hours_back: int = 24,
    force_all: bool = False
) -> Dict[str, Any]:
    """
    Syncs all companies updated in the last {hours_back} hours
    to HubSpot using batch operations.
    
    Args:
        db: Database session
        hours_back: How many hours back to look for updates (default 24)
        force_all: If True, sync ALL companies regardless of update time
        
    Returns:
        Summary dict with sync results
    """
    start_time = time.time()
    now_utc = datetime.now(timezone.utc)
    
    # Get the current HubSpot API key from database or environment
    api_key = await get_hubspot_api_key(db)
    hubspot_client_instance = create_hubspot_client(api_key)

    try:
        if force_all:
            logger.info("Force sync: syncing ALL companies")
        else:
            logger.info("Starting HubSpot sync for companies updated in last %d hours", hours_back)

        # STEP 1 — Fetch companies to sync
        cutoff_time = now_utc - timedelta(hours=hours_back)

        # If force_all is True, sync all companies. Otherwise use time filter.
        if force_all:
            logger.info("Force mode: syncing ALL companies (ignoring time filter)")
            stmt = (
                select(Company)
                .where(
                    ~Company.company_name.ilike("%confidential%"),
                    ~Company.company_name.ilike("%unknown%"),
                )
                .order_by(Company.hiring_velocity_score.desc())
                .limit(MAX_COMPANIES_PER_SYNC)
            )
        elif hours_back == 1:
            logger.info("Testing mode: syncing ALL companies (ignoring time filter)")
            stmt = (
                select(Company)
                .where(
                    ~Company.company_name.ilike("%confidential%"),
                    ~Company.company_name.ilike("%unknown%"),
                )
                .order_by(Company.hiring_velocity_score.desc())
                .limit(MAX_COMPANIES_PER_SYNC)
            )
        else:
            stmt = (
                select(Company)
                .where(
                    Company.last_active_at >= cutoff_time,
                    ~Company.company_name.ilike("%confidential%"),
                    ~Company.company_name.ilike("%unknown%"),
                )
                .order_by(Company.hiring_velocity_score.desc())
                .limit(MAX_COMPANIES_PER_SYNC)
            )

        result = await db.execute(stmt)
        companies = result.scalars().all()

        if not companies:
            logger.info("No companies found to sync")
            return {
                "companies_synced": 0,
                "notes_created": 0,
                "deals_created": 0,
                "contacts_synced": 0,
                "duration_seconds": round(time.time() - start_time, 1),
                "synced_at": now_utc.isoformat(),
            }

        company_ids = [c.id for c in companies]
        logger.info("Found %d companies to sync", len(companies))
        
        if companies:
            logger.info("Sample company IDs: %s", [str(c.id) for c in companies[:3]])
            logger.info("Sample company names: %s", [c.company_name for c in companies[:3]])

        # STEP 2 — Fetch recent jobs for these companies
        jobs_stmt = (
            select(JobPosting)
            .where(
                JobPosting.company_id.in_(company_ids),
                JobPosting.posted_at >= (now_utc - timedelta(days=7)),
                JobPosting.is_duplicate == False,
            )
            .order_by(JobPosting.posted_at.desc())
        )

        jobs_result = await db.execute(jobs_stmt)
        all_jobs = jobs_result.scalars().all()

        jobs_by_company: Dict[str, List[JobPosting]] = {}
        for job in all_jobs:
            key = str(job.company_id)
            if key not in jobs_by_company:
                jobs_by_company[key] = []
            if len(jobs_by_company[key]) < 10:  # Cap at 10 per company
                jobs_by_company[key].append(job)

        # STEP 3 — Fetch contacts for these companies
        contacts_stmt = select(CompanyContact).where(
            CompanyContact.company_id.in_(company_ids)
        )

        contacts_result = await db.execute(contacts_stmt)
        all_contacts = contacts_result.scalars().all()

        contacts_by_company: Dict[str, List[CompanyContact]] = {}
        for contact in all_contacts:
            key = str(contact.company_id)
            if key not in contacts_by_company:
                contacts_by_company[key] = []
            contacts_by_company[key].append(contact)

        # STEP 4 — Build company upsert payloads
        company_upsert_records = []

        for company in companies:
            logger.debug("Processing company: %s", company.company_name)

            # Skip companies with URL-like names (bad data from scrapers)
            if is_url_like(company.company_name or ""):
                logger.warning("Skipping company with URL name: %s", company.company_name)
                continue

            # Get first contact email and phone if available
            primary_contact_email = ""
            primary_contact_phone = ""
            company_contacts = contacts_by_company.get(str(company.id), [])
            if company_contacts:
                primary_contact = company_contacts[0]
                primary_contact_email = primary_contact.email or ""
                primary_contact_phone = primary_contact.phone or ""

            properties = {
                "name": company.company_name,
                "domain": company.domains_active[0] if company.domains_active else "",
                "country": company.countries[0] if company.countries else "",
                "jobintel_id": str(company.id),
                "hiring_velocity_score": str(company.hiring_velocity_score or 0),
                "bd_tags": _format_bd_tags(company.bd_tags or []),
                "bd_tag_count": str(len(company.bd_tags or [])),
                "total_postings_7d": str(company.total_postings_7d or 0),
                # Locations and countries
                "jobintel_locations": ", ".join(company.locations or []),
                "jobintel_countries": ", ".join(company.countries or []),
                "primary_contact_email": primary_contact_email,
                "primary_contact_phone": primary_contact_phone,
                "description": (
                    f"Platforms: {', '.join(company.platforms_seen_on or [])}\n"
                    f"Locations: {', '.join(company.locations or [])}\n"
                    f"Countries: {', '.join(company.countries or [])}\n"
                    f"Total jobs (30d): {company.total_postings_30d}"
                ),
            }

            company_upsert_records.append({
                "idProperty": "jobintel_id",
                "id": str(company.id),
                "properties": properties,
            })

        # STEP 5 — Batch upsert companies
        results = await hubspot_client_instance.batch_upsert_companies(company_upsert_records)

        logger.info(
            "Batch upsert attempted for %d companies, got %d results",
            len(company_upsert_records), len(results)
        )

        if not results:
            logger.warning("Batch upsert returned no results - likely a validation error")
            # Log the first record to see what might be wrong
            if company_upsert_records:
                logger.warning("Sample upsert record: %s", company_upsert_records[0])
            return {
                "error": "Batch upsert returned no results from HubSpot",
                "companies_synced": 0,
                "notes_created": 0,
                "deals_created": 0,
                "contacts_synced": 0,
                "duration_seconds": round(time.time() - start_time, 1),
                "synced_at": now_utc.isoformat(),
            }

        # Map by position — results are returned in same order as inputs
        # Each company_upsert_records[i] corresponds to results[i]
        # company_upsert_records[i]["id"] is str(company.id) (our jobintel_id)
        jobintel_id_to_hubspot_id: dict[str, str] = {}
        for i, result in enumerate(results):
            if i < len(company_upsert_records):
                our_id = company_upsert_records[i]["id"]  # this is str(company.id)
                if isinstance(result, dict) and result.get("id"):
                    jobintel_id_to_hubspot_id[our_id] = result["id"]

        logger.info(
            "Mapped %d company IDs to HubSpot IDs",
            len(jobintel_id_to_hubspot_id)
        )

        # STEP 6 — Build and batch create notes
        note_inputs = []
        note_company_pairs = []  # (hubspot_id, note_idx) to map after creation

        for company in companies:
            hubspot_id = jobintel_id_to_hubspot_id.get(str(company.id))
            if not hubspot_id:
                continue

            jobs = jobs_by_company.get(str(company.id), [])
            note_body = _build_note_body(
                company.company_name,
                jobs,
                company.bd_tags or []
            )

            note_inputs.append({
                "properties": {
                    "hs_note_body": note_body,
                    "hs_timestamp": str(int(time.time() * 1000)),
                }
            })
            note_company_pairs.append(hubspot_id)

        note_ids = await hubspot_client_instance.batch_create_notes(note_inputs)

        # STEP 7 — Batch associate notes to companies
        association_pairs = list(zip(note_company_pairs, note_ids))
        await hubspot_client_instance.batch_associate_notes(association_pairs)
        logger.info("Created and associated %d notes", len(note_ids))

        # STEP 8 — Build and create deals for BD signal companies
        deal_inputs = []
        deal_company_hubspot_ids = []

        for company in companies:
            hubspot_id = jobintel_id_to_hubspot_id.get(str(company.id))
            if not hubspot_id:
                continue

            tags = set(company.bd_tags or [])
            if not tags.intersection(BD_SIGNAL_TAGS):
                continue

            if company.hubspot_deal_id:
                continue  # already has a deal

            deal_name = f"{company.company_name} – BD Opportunity"

            deal_inputs.append({
                "properties": {
                    "dealname": deal_name,
                    "dealstage": "appointmentscheduled",
                    "pipeline": "default",
                    "description": (
                        f"BD signals: {', '.join(tags)}\n"
                        f"Jobs last 7d: {company.total_postings_7d}\n"
                        f"Velocity score: {company.hiring_velocity_score}"
                    ),
                }
            })
            deal_company_hubspot_ids.append((company.id, hubspot_id))

        deal_results = []
        if deal_inputs:
            deal_results = await hubspot_client_instance.batch_create_deals(deal_inputs)

            deal_pairs = [
                (hs_id, r["id"])
                for (_, hs_id), r in zip(deal_company_hubspot_ids, deal_results)
            ]

            await hubspot_client_instance.batch_associate_deals(deal_pairs)
            logger.info("Created %d deals", len(deal_results))

        # STEP 9 — Batch upsert contacts
        contact_upsert_records: List[Dict[str, Any]] = []
        contact_meta: List[Dict[str, Any]] = []
        phone_only_create_records: List[Dict[str, Any]] = []
        phone_only_meta: List[Dict[str, Any]] = []
        existing_contact_id_map: Dict[Any, str] = {}
        seen_emails: set[str] = set()
        invalid_email_count = 0

        for company in companies:
            hubspot_id = jobintel_id_to_hubspot_id.get(str(company.id))
            if not hubspot_id:
                continue

            company_contacts = contacts_by_company.get(str(company.id), [])
            for contact in company_contacts:
                normalized_email = _normalize_email(contact.email)
                if contact.email and not normalized_email:
                    invalid_email_count += 1

                if normalized_email:
                    if normalized_email not in seen_emails:
                        contact_upsert_records.append({
                            "idProperty": "email",
                            "id": normalized_email,
                            "properties": _build_contact_properties(
                                contact,
                                normalized_email=normalized_email,
                            ),
                        })
                        seen_emails.add(normalized_email)

                    contact_meta.append({
                        "email": normalized_email,
                        "hs_company_id": hubspot_id,
                        "contact_id": contact.id,
                    })
                    continue

                if contact.phone:
                    if contact.hubspot_contact_id:
                        existing_contact_id_map[contact.id] = contact.hubspot_contact_id
                        continue

                    phone_only_create_records.append(
                        {"properties": _build_contact_properties(contact)}
                    )
                    phone_only_meta.append({
                        "hs_company_id": hubspot_id,
                        "contact_id": contact.id,
                    })
                else:
                    logger.debug(
                        "Skipping contact %s for company %s (no valid email or phone)",
                        contact.id,
                        company.company_name,
                    )

        if invalid_email_count:
            logger.info(
                "Skipped %d invalid email values during HubSpot contact sync",
                invalid_email_count,
            )

        email_to_hubspot_id: Dict[str, str] = {}
        contact_id_to_hubspot_id: Dict[Any, str] = dict(existing_contact_id_map)
        contact_assoc_pairs: set[tuple[str, str]] = set()
        contacts_synced = 0

        if contact_upsert_records:
            contact_results = await hubspot_client_instance.batch_upsert_contacts(
                contact_upsert_records
            )

            for i, result in enumerate(contact_results):
                hubspot_contact_id = result.get("id")
                if not hubspot_contact_id:
                    continue

                result_props = result.get("properties") or {}
                result_email = _normalize_email(result_props.get("email"))
                if not result_email and i < len(contact_upsert_records):
                    result_email = contact_upsert_records[i]["id"]

                if result_email:
                    email_to_hubspot_id[result_email] = hubspot_contact_id

            for meta in contact_meta:
                hubspot_contact_id = email_to_hubspot_id.get(meta["email"])
                if hubspot_contact_id:
                    contact_assoc_pairs.add((meta["hs_company_id"], hubspot_contact_id))
                    contact_id_to_hubspot_id[meta["contact_id"]] = hubspot_contact_id

            contacts_synced += len(email_to_hubspot_id)

        if phone_only_create_records:
            phone_create_results = await hubspot_client_instance.batch_create_contacts(
                phone_only_create_records
            )

            for i, result in enumerate(phone_create_results):
                if i >= len(phone_only_meta):
                    break

                hubspot_contact_id = result.get("id")
                if not hubspot_contact_id:
                    continue

                meta = phone_only_meta[i]
                contact_assoc_pairs.add((meta["hs_company_id"], hubspot_contact_id))
                contact_id_to_hubspot_id[meta["contact_id"]] = hubspot_contact_id
                contacts_synced += 1

        if contact_assoc_pairs:
            await hubspot_client_instance.batch_associate_contacts(
                list(contact_assoc_pairs)
            )

        logger.info(
            "Synced %d contacts total (%d email upserts, %d phone-only creates), associated %d",
            contacts_synced,
            len(email_to_hubspot_id),
            len(phone_only_meta),
            len(contact_assoc_pairs),
        )

        # STEP 10 — Write HubSpot IDs back to DB
        # Update company HubSpot IDs
        for company in companies:
            hubspot_id = jobintel_id_to_hubspot_id.get(str(company.id))
            if hubspot_id:
                company.hubspot_company_id = hubspot_id
                company.hubspot_synced_at = now_utc

        # Update deal IDs
        for (company_id, _), deal_result in zip(deal_company_hubspot_ids, deal_results):
            # Find the company by ID
            for company in companies:
                if company.id == company_id:
                    company.hubspot_deal_id = deal_result["id"]
                    break

        # Update contact HubSpot IDs
        if contact_id_to_hubspot_id:
            for contacts_list in contacts_by_company.values():
                for contact in contacts_list:
                    hubspot_contact_id = contact_id_to_hubspot_id.get(contact.id)
                    if hubspot_contact_id:
                        contact.hubspot_contact_id = hubspot_contact_id

        await db.commit()
        logger.info("Wrote HubSpot IDs back to DB")

        # STEP 11 — Return summary
        return {
            "companies_synced": len(jobintel_id_to_hubspot_id),  # Count of successfully synced companies
            "notes_created": len(note_ids),
            "deals_created": len(deal_results),
            "contacts_synced": contacts_synced,
            "duration_seconds": round(time.time() - start_time, 1),
            "synced_at": now_utc.isoformat(),
        }

    except Exception as e:
        logger.error("HubSpot sync failed: %s", str(e))
        logger.error("Full traceback: %s", traceback.format_exc())

        return {
            "error": str(e),
            "companies_synced": 0,
            "notes_created": 0,
            "deals_created": 0,
            "contacts_synced": 0,
            "duration_seconds": round(time.time() - start_time, 1),
            "synced_at": now_utc.isoformat(),
        }


async def sync_single_company_to_hubspot(
    db: AsyncSession,
    company_id: str
) -> Dict[str, Any]:
    """
    Sync a single company to HubSpot.
    Returns a summary dict with sync results.
    """
    start_time = time.time()
    now_utc = datetime.now(timezone.utc)
    
    # Get the current HubSpot API key from database or environment
    api_key = await get_hubspot_api_key(db)
    hubspot_client_instance = create_hubspot_client(api_key)

    try:
        logger.info("Starting HubSpot sync for single company: %s", company_id)

        # STEP 1 — Fetch the company
        stmt = select(Company).where(Company.id == company_id)
        result = await db.execute(stmt)
        company = result.scalar_one_or_none()

        if not company:
            return {
                "error": f"Company {company_id} not found",
                "company_synced": False,
                "deal_created": False,
                "contacts_synced": 0,
                "duration_seconds": round(time.time() - start_time, 1),
            }

        # Skip companies with URL-like names (bad data from scrapers)
        if is_url_like(company.company_name or ""):
            logger.warning("Skipping single company sync — URL name: %s", company.company_name)
            return {
                "error": f"Company name is a URL: {company.company_name}",
                "company_synced": False,
                "deal_created": False,
                "contacts_synced": 0,
                "duration_seconds": round(time.time() - start_time, 1),
            }

        # STEP 2 — Fetch recent jobs for this company
        jobs_stmt = (
            select(JobPosting)
            .where(
                JobPosting.company_id == company_id,
                JobPosting.posted_at >= (now_utc - timedelta(days=7)),
                JobPosting.is_duplicate == False,
            )
            .order_by(JobPosting.posted_at.desc())
            .limit(10)
        )

        jobs_result = await db.execute(jobs_stmt)
        jobs = jobs_result.scalars().all()

        # STEP 3 — Fetch contacts for this company
        contacts_stmt = select(CompanyContact).where(
            CompanyContact.company_id == company_id
        )
        contacts_result = await db.execute(contacts_stmt)
        contacts = contacts_result.scalars().all()

        # STEP 4 — Upsert company to HubSpot
        # Get first contact email and phone if available
        primary_contact_email = ""
        primary_contact_phone = ""
        if contacts:
            primary_contact = contacts[0]
            primary_contact_email = primary_contact.email or ""
            primary_contact_phone = primary_contact.phone or ""

        properties = {
            "name": company.company_name,
            "domain": company.domains_active[0] if company.domains_active else "",
            "country": company.countries[0] if company.countries else "",
            "jobintel_id": str(company.id),
            "hiring_velocity_score": str(company.hiring_velocity_score or 0),
            "bd_tags": _format_bd_tags(company.bd_tags or []),
            "bd_tag_count": str(len(company.bd_tags or [])),
            "total_postings_7d": str(company.total_postings_7d or 0),
            # Locations and countries
            "jobintel_locations": ", ".join(company.locations or []),
            "jobintel_countries": ", ".join(company.countries or []),
            "primary_contact_email": primary_contact_email,
            "primary_contact_phone": primary_contact_phone,
            "description": (
                f"Platforms: {', '.join(company.platforms_seen_on or [])}\n"
                f"Locations: {', '.join(company.locations or [])}\n"
                f"Countries: {', '.join(company.countries or [])}\n"
                f"Total jobs (30d): {company.total_postings_30d}"
            ),
        }

        company_upsert_records = [{
            "idProperty": "jobintel_id",
            "id": str(company.id),
            "properties": properties,
        }]

        results = await hubspot_client_instance.batch_upsert_companies(company_upsert_records)
        hubspot_company_id = results[0]["id"] if results else None

        if not hubspot_company_id:
            return {
                "error": "Failed to upsert company to HubSpot",
                "company_synced": False,
                "deal_created": False,
                "contacts_synced": 0,
                "duration_seconds": round(time.time() - start_time, 1),
            }

        # STEP 5 — Create note for the company
        note_body = _build_note_body(
            company.company_name,
            jobs,
            company.bd_tags or []
        )

        note_inputs = [{
            "properties": {
                "hs_note_body": note_body,
                "hs_timestamp": str(int(time.time() * 1000)),
            }
        }]

        note_ids = await hubspot_client_instance.batch_create_notes(note_inputs)
        if note_ids:
            await hubspot_client_instance.batch_associate_notes([(hubspot_company_id, note_ids[0])])

        # STEP 6 — Create deal if BD signals present and no existing deal
        deal_created = False
        if not company.hubspot_deal_id:
            tags = set(company.bd_tags or [])
            if tags.intersection(BD_SIGNAL_TAGS):
                deal_name = f"{company.company_name} – BD Opportunity"

                deal_inputs = [{
                    "properties": {
                        "dealname": deal_name,
                        "dealstage": "appointmentscheduled",
                        "pipeline": "default",
                        "description": (
                            f"BD signals: {', '.join(tags)}\n"
                            f"Jobs last 7d: {company.total_postings_7d}\n"
                            f"Velocity score: {company.hiring_velocity_score}"
                        ),
                    }
                }]

                deal_results = await hubspot_client_instance.batch_create_deals(deal_inputs)
                if deal_results:
                    await hubspot_client_instance.batch_associate_deals([(hubspot_company_id, deal_results[0]["id"])])
                    deal_created = True

        # STEP 7 — Upsert contacts
        contact_upsert_records: List[Dict[str, Any]] = []
        contact_meta_single: List[Dict[str, Any]] = []
        phone_only_create_records: List[Dict[str, Any]] = []
        phone_only_meta: List[Dict[str, Any]] = []
        existing_contact_id_map: Dict[Any, str] = {}
        seen_emails: set[str] = set()
        invalid_email_count = 0

        for contact in contacts:
            normalized_email = _normalize_email(contact.email)
            if contact.email and not normalized_email:
                invalid_email_count += 1

            if normalized_email:
                if normalized_email not in seen_emails:
                    contact_upsert_records.append({
                        "idProperty": "email",
                        "id": normalized_email,
                        "properties": _build_contact_properties(
                            contact,
                            normalized_email=normalized_email,
                        ),
                    })
                    seen_emails.add(normalized_email)

                contact_meta_single.append({
                    "email": normalized_email,
                    "contact_id": contact.id,
                })
            else:
                # Phone-only contact — HubSpot requires email as idProperty for batch upsert
                if contact.phone:
                    if contact.hubspot_contact_id:
                        existing_contact_id_map[contact.id] = contact.hubspot_contact_id
                        continue

                    phone_only_create_records.append(
                        {"properties": _build_contact_properties(contact)}
                    )
                    phone_only_meta.append({"contact_id": contact.id})
                else:
                    logger.debug(
                        "Skipping contact %s for company %s (no valid email or phone)",
                        contact.id,
                        company.company_name,
                    )

        if invalid_email_count:
            logger.info(
                "Skipped %d invalid email values during single-company contact sync",
                invalid_email_count,
            )

        email_to_hubspot_id: Dict[str, str] = {}
        contact_id_to_hubspot_id: Dict[Any, str] = dict(existing_contact_id_map)
        contact_assoc_pairs: set[tuple[str, str]] = set()
        contacts_synced = 0

        if contact_upsert_records:
            contact_results = await hubspot_client_instance.batch_upsert_contacts(
                contact_upsert_records
            )

            for i, result in enumerate(contact_results):
                hubspot_contact_id = result.get("id")
                if not hubspot_contact_id:
                    continue

                result_props = result.get("properties") or {}
                result_email = _normalize_email(result_props.get("email"))
                if not result_email and i < len(contact_upsert_records):
                    result_email = contact_upsert_records[i]["id"]

                if result_email:
                    email_to_hubspot_id[result_email] = hubspot_contact_id

            for meta in contact_meta_single:
                hubspot_contact_id = email_to_hubspot_id.get(meta["email"])
                if hubspot_contact_id:
                    contact_assoc_pairs.add((hubspot_company_id, hubspot_contact_id))
                    contact_id_to_hubspot_id[meta["contact_id"]] = hubspot_contact_id

            contacts_synced += len(email_to_hubspot_id)

        if phone_only_create_records:
            phone_create_results = await hubspot_client_instance.batch_create_contacts(
                phone_only_create_records
            )

            for i, result in enumerate(phone_create_results):
                if i >= len(phone_only_meta):
                    break

                hubspot_contact_id = result.get("id")
                if not hubspot_contact_id:
                    continue

                meta = phone_only_meta[i]
                contact_assoc_pairs.add((hubspot_company_id, hubspot_contact_id))
                contact_id_to_hubspot_id[meta["contact_id"]] = hubspot_contact_id
                contacts_synced += 1

        if contact_assoc_pairs:
            await hubspot_client_instance.batch_associate_contacts(
                list(contact_assoc_pairs)
            )

        logger.info(
            "Single-company sync: %d contacts total (%d email upserts, %d phone-only creates), associated %d",
            contacts_synced,
            len(email_to_hubspot_id),
            len(phone_only_meta),
            len(contact_assoc_pairs),
        )

        # STEP 8 — Write HubSpot IDs back to DB
        company.hubspot_company_id = hubspot_company_id
        company.hubspot_synced_at = now_utc

        if deal_created and 'deal_results' in locals() and deal_results:
            company.hubspot_deal_id = deal_results[0]["id"]

        # Update contact HubSpot IDs
        if contact_id_to_hubspot_id:
            for contact in contacts:
                hubspot_contact_id = contact_id_to_hubspot_id.get(contact.id)
                if hubspot_contact_id:
                    contact.hubspot_contact_id = hubspot_contact_id

        await db.commit()

        return {
            "company_synced": True,
            "deal_created": deal_created,
            "contacts_synced": contacts_synced,
            "duration_seconds": round(time.time() - start_time, 1),
        }

    except Exception as e:
        logger.error("Single company HubSpot sync failed: %s", str(e))
        logger.error("Full traceback: %s", traceback.format_exc())

        return {
            "error": str(e),
            "company_synced": False,
            "deal_created": False,
            "contacts_synced": 0,
            "duration_seconds": round(time.time() - start_time, 1),
        }
