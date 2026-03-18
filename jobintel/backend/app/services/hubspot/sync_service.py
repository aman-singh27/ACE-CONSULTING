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
from app.services.hubspot.hubspot_client import hubspot_client

logger = get_logger(__name__)

# Constants
BD_SIGNAL_TAGS = {"spiking", "new_entrant", "salary_signal"}
MAX_COMPANIES_PER_SYNC = 500


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
        f"BD Tags: {', '.join(bd_tags) or 'None'}",
        f"Synced: {today}",
        "",
        "Recent Job Postings (last 7 days):",
    ]

    if not jobs:
        note_lines.append("No recent job postings found.")
    else:
        for job in jobs[:10]:  # Cap at 10 jobs
            days_ago = (datetime.now(timezone.utc) - job.posted_at).days
            if days_ago == 0:
                relative_date = "today"
            elif days_ago == 1:
                relative_date = "yesterday"
            elif days_ago <= 6:
                relative_date = f"{days_ago} days ago"
            else:
                relative_date = job.posted_at.strftime("%b %d")

            location = job.location_raw or "Location N/A"
            note_lines.append(
                f"• {job.title} — {location} — {job.source_platform} — {relative_date}"
            )

    return "\n".join(note_lines)


async def sync_companies_to_hubspot(
    db: AsyncSession,
    hours_back: int = 24
) -> Dict[str, Any]:
    """
    Syncs all companies updated in the last {hours_back} hours
    to HubSpot using batch operations.
    Returns a summary dict.
    """
    start_time = time.time()
    now_utc = datetime.now(timezone.utc)

    try:
        logger.info("Starting HubSpot sync for companies updated in last %d hours", hours_back)

        # STEP 1 — Fetch companies to sync
        cutoff_time = now_utc - timedelta(hours=hours_back)

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
            if job.company_id not in jobs_by_company:
                jobs_by_company[job.company_id] = []
            if len(jobs_by_company[job.company_id]) < 10:  # Cap at 10 per company
                jobs_by_company[job.company_id].append(job)

        # STEP 3 — Fetch contacts for these companies
        contacts_stmt = select(CompanyContact).where(
            CompanyContact.company_id.in_(company_ids)
        )

        contacts_result = await db.execute(contacts_stmt)
        all_contacts = contacts_result.scalars().all()

        contacts_by_company: Dict[str, List[CompanyContact]] = {}
        for contact in all_contacts:
            if contact.company_id not in contacts_by_company:
                contacts_by_company[contact.company_id] = []
            contacts_by_company[contact.company_id].append(contact)

        # STEP 4 — Build company upsert payloads
        company_upsert_records = []

        for company in companies:
            logger.debug("Processing company: %s", company.company_name)

            properties = {
                "name": company.company_name,
                "domain": company.website or "",
                "industry": company.industry_apollo or "",
                "numberofemployees": company.employee_count or "",
                "country": company.countries[0] if company.countries else "",
                "jobintel_id": str(company.id),
                "hiring_velocity_score": str(company.hiring_velocity_score or 0),
                "bd_tags": ", ".join(company.bd_tags or []),
                "total_postings_7d": str(company.total_postings_7d or 0),
                "description": (
                    f"Platforms: {', '.join(company.platforms_seen_on or [])}\n"
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
        results = await hubspot_client.batch_upsert_companies(company_upsert_records)

        jobintel_id_to_hubspot_id = {
            r["properties"]["jobintel_id"]: r["id"] for r in results
        }

        logger.info("Upserted %d companies to HubSpot", len(results))

        # STEP 6 — Build and batch create notes
        note_inputs = []
        note_company_pairs = []  # (hubspot_id, note_idx) to map after creation

        for company in companies:
            hubspot_id = jobintel_id_to_hubspot_id.get(str(company.id))
            if not hubspot_id:
                continue

            jobs = jobs_by_company.get(company.id, [])
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

        note_ids = await hubspot_client.batch_create_notes(note_inputs)

        # STEP 7 — Batch associate notes to companies
        association_pairs = list(zip(note_company_pairs, note_ids))
        await hubspot_client.batch_associate_notes(association_pairs)
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
            deal_results = await hubspot_client.batch_create_deals(deal_inputs)

            deal_pairs = [
                (hs_id, r["id"])
                for (_, hs_id), r in zip(deal_company_hubspot_ids, deal_results)
            ]

            await hubspot_client.batch_associate_deals(deal_pairs)
            logger.info("Created %d deals", len(deal_results))

        # STEP 9 — Batch upsert contacts
        contact_upsert_records = []
        contact_company_map = []  # list of (company_id, email) to resolve associations after

        for company in companies:
            hubspot_id = jobintel_id_to_hubspot_id.get(str(company.id))
            if not hubspot_id:
                continue

            contacts = contacts_by_company.get(company.id, [])
            for contact in contacts:
                if not contact.email:
                    continue

                name_parts = (contact.full_name or "").split(" ", 1)
                contact_upsert_records.append({
                    "idProperty": "email",
                    "id": contact.email,
                    "properties": {
                        "email": contact.email,
                        "firstname": name_parts[0] if name_parts else "",
                        "lastname": name_parts[1] if len(name_parts) > 1 else "",
                        "jobtitle": contact.title or "",
                        "linkedin__url": contact.linkedin_url or "",
                    },
                })
                contact_company_map.append((contact.email, hubspot_id, contact.id))

        contact_results = []
        if contact_upsert_records:
            contact_results = await hubspot_client.batch_upsert_contacts(contact_upsert_records)
            logger.info("Upserted %d contacts", len(contact_results))

            # Build email to HubSpot contact ID mapping
            email_to_hubspot_contact = {
                r["properties"]["email"]: r["id"]
                for r in contact_results
                if r.get("properties", {}).get("email")
            }

            # Build association pairs
            contact_assoc_pairs = []
            for email, hs_company_id, _ in contact_company_map:
                hs_contact_id = email_to_hubspot_contact.get(email)
                if hs_contact_id:
                    contact_assoc_pairs.append((hs_company_id, hs_contact_id))

            if contact_assoc_pairs:
                await hubspot_client.batch_associate_contacts(contact_assoc_pairs)

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
        for email, _, contact_id in contact_company_map:
            hs_contact_id = email_to_hubspot_contact.get(email)
            if hs_contact_id:
                # Find the contact by ID and update
                for company_contacts in contacts_by_company.values():
                    for contact in company_contacts:
                        if contact.id == contact_id:
                            contact.hubspot_contact_id = hs_contact_id
                            break

        await db.commit()
        logger.info("Wrote HubSpot IDs back to DB")

        # STEP 11 — Return summary
        return {
            "companies_synced": len(results),
            "notes_created": len(note_ids),
            "deals_created": len(deal_results),
            "contacts_synced": len(contact_results),
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
        properties = {
            "name": company.company_name,
            "domain": company.website or "",
            "industry": company.industry_apollo or "",
            "numberofemployees": company.employee_count or "",
            "country": company.countries[0] if company.countries else "",
            "jobintel_id": str(company.id),
            "hiring_velocity_score": str(company.hiring_velocity_score or 0),
            "bd_tags": ", ".join(company.bd_tags or []),
            "total_postings_7d": str(company.total_postings_7d or 0),
            "description": (
                f"Platforms: {', '.join(company.platforms_seen_on or [])}\n"
                f"Countries: {', '.join(company.countries or [])}\n"
                f"Total jobs (30d): {company.total_postings_30d}"
            ),
        }

        company_upsert_records = [{
            "idProperty": "jobintel_id",
            "id": str(company.id),
            "properties": properties,
        }]

        results = await hubspot_client.batch_upsert_companies(company_upsert_records)
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

        note_ids = await hubspot_client.batch_create_notes(note_inputs)
        if note_ids:
            await hubspot_client.batch_associate_notes([(hubspot_company_id, note_ids[0])])

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

                deal_results = await hubspot_client.batch_create_deals(deal_inputs)
                if deal_results:
                    await hubspot_client.batch_associate_deals([(hubspot_company_id, deal_results[0]["id"])])
                    deal_created = True

        # STEP 7 — Upsert contacts
        contact_upsert_records = []
        contact_emails = []

        for contact in contacts:
            if not contact.email:
                continue

            name_parts = (contact.full_name or "").split(" ", 1)
            contact_upsert_records.append({
                "idProperty": "email",
                "id": contact.email,
                "properties": {
                    "email": contact.email,
                    "firstname": name_parts[0] if name_parts else "",
                    "lastname": name_parts[1] if len(name_parts) > 1 else "",
                    "jobtitle": contact.title or "",
                    "linkedin__url": contact.linkedin_url or "",
                },
            })
            contact_emails.append(contact.email)

        contacts_synced = 0
        if contact_upsert_records:
            contact_results = await hubspot_client.batch_upsert_contacts(contact_upsert_records)
            contacts_synced = len(contact_results)

            # Build email to HubSpot contact ID mapping
            email_to_hubspot_contact = {
                r["properties"]["email"]: r["id"]
                for r in contact_results
                if r.get("properties", {}).get("email")
            }

            # Associate contacts to company
            contact_assoc_pairs = [
                (hubspot_company_id, hs_contact_id)
                for email, hs_contact_id in email_to_hubspot_contact.items()
            ]

            if contact_assoc_pairs:
                await hubspot_client.batch_associate_contacts(contact_assoc_pairs)

        # STEP 8 — Write HubSpot IDs back to DB
        company.hubspot_company_id = hubspot_company_id
        company.hubspot_synced_at = now_utc

        if deal_created and 'deal_results' in locals() and deal_results:
            company.hubspot_deal_id = deal_results[0]["id"]

        # Update contact HubSpot IDs
        for contact in contacts:
            if contact.email and contact.email in email_to_hubspot_contact:
                contact.hubspot_contact_id = email_to_hubspot_contact[contact.email]

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