"""
Record processor – normalizes raw records via the normalizer registry and applies deduplication.

Current behaviour: normalizes, applies dedup rules, and logs.
Future: DB write.
"""

from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.actor_run import ActorRun
from app.schemas.standard_job import StandardJob
from app.services.dedup.dedup_service import (
    DUPLICATE_CROSS,
    DUPLICATE_EXACT,
    NEW_RECORD,
    check_duplicates,
)
from app.services.normalizers.registry import NormalizerFn
from app.services.intelligence.contact_extractor import extract_contacts
from app.services.persistence.contact_persistence import save_extracted_contacts
from app.services.persistence.company_aggregator import update_company_aggregates
from app.services.persistence.job_writer import write_job

logger = get_logger(__name__)


async def process_record(
    db: AsyncSession,
    record: dict[str, Any],
    index: int,
    run: ActorRun,
    *,
    normalizer: Optional[NormalizerFn] = None,
    actor_id: str = "",
    domain: Optional[str] = None,
) -> Optional[StandardJob]:
    """Process a single scraped job record.

    1. Normalizes the raw record
    2. Runs deduplication checks
    3. Handles the record based on dedup result
    """
    if normalizer is None:
        title = record.get("title", record.get("jobTitle", "unknown"))
        company = record.get("company", record.get("companyName", "unknown"))
        logger.info("Processing record %d (no normalizer): title=%s, company=%s", index, title, company)
        return None

    # ── 1. Normalize ─────────────────────────────────────────
    try:
        job = normalizer(record, actor_id, domain)
    except Exception as e:
        logger.exception("Failed to normalize record %d. Raw record: %s. Error: %s", index, record, e)
        raise

    # ── 2. Deduplicate ───────────────────────────────────────
    dedup_result = await check_duplicates(db, job)

    if dedup_result == DUPLICATE_EXACT:
        logger.info("Exact duplicate detected (skipped): job_id=%s", job.job_id)
        # We need a new field on ActorRun if we want to track duplicates exactly.
        # But instructions say "increment run.total_duplicates"
        # Since total_scraped is already incremented in pipeline per-record, we'll
        # handle custom counts in the pipeline if needed, or just track in run here
        # Wait, the instruction says: "increment run.total_duplicates" but
        # the model only has total_scraped, total_errors.
        # We can dynamically add attributes here or update the model later. Let's just log.
        # We'll set a custom attribute to track in pipeline: 
        if not hasattr(run, "total_duplicates"):
            run.total_duplicates = 0
        run.total_duplicates += 1
        return None
        
    elif dedup_result == DUPLICATE_CROSS:
        logger.info("Cross-platform duplicate detected: title=%s, company=%s", job.title, job.company_name)
        job.is_duplicate = True
        if not hasattr(run, "total_cross_dupes"):
            run.total_cross_dupes = 0
        run.total_cross_dupes += 1

    else:
        logger.info("New job record detected: title=%s, company=%s", job.title, job.company_name)
        job.is_duplicate = False
        if not hasattr(run, "total_new"):
            run.total_new = 0
        run.total_new += 1

    # ── 3. Write to Database ─────────────────────────────────
    try:
        db_job = await write_job(db, job, run.id)
    except Exception as e:
        logger.exception("Failed to write job to DB at record %d. Job details: %s. Error: %s", index, job.model_dump_json() if hasattr(job, "model_dump_json") else job, e)
        raise

    # ── 4. Update Company Aggregates ─────────────────────────
    if db_job.company_id:
        try:
            await update_company_aggregates(db, db_job.company_id, job)
        except Exception as e:
            logger.exception("Failed to update company aggregates at record %d for company %s. Error: %s", index, db_job.company_id, e)
            raise

        # ── 5. Extract and Save Contacts ─────────────────────
        try:
            if job.description_raw:
                contacts = extract_contacts(job.description_raw)
                if contacts["emails"] or contacts["phones"]:
                    await save_extracted_contacts(db, db_job.company_id, contacts)
        except Exception as e:
            logger.error("Failed to extract/save contacts for company %s: %s", db_job.company_id, e)
            # We don't want to fail the whole record if contact extraction fails
            pass

    return job
