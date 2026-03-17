"""
Dedup service – core logic for duplication detection.
"""

from typing import Literal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.job_posting import JobPosting
from app.schemas.standard_job import StandardJob
from app.services.dedup.fingerprint import generate_fingerprint, generate_job_id

logger = get_logger(__name__)

# Constants for dedup outcomes
DUPLICATE_EXACT = "exact_duplicate"
DUPLICATE_CROSS = "cross_platform_duplicate"
NEW_RECORD = "new_record"

DedupResult = Literal["exact_duplicate", "cross_platform_duplicate", "new_record"]


async def check_duplicates(db: AsyncSession, job: StandardJob) -> DedupResult:
    """Implement Level 1 and Level 2 deduplication checks.

    1. Checks exact match by job_id
    2. Checks fuzzy match by fingerprint_hash
    3. Populates those hashes on the job object
    """
    # ── Level 1: Exact Duplicate ──────────────────────────────
    job_id = generate_job_id(job)
    job.job_id = job_id  # Ensure the job has it set for writing

    result = await db.execute(select(JobPosting.id).where(JobPosting.job_id == job_id))
    if result.first():
        return DUPLICATE_EXACT

    # ── Level 2: Cross Platform Duplicate ─────────────────────
    fingerprint = generate_fingerprint(job)
    job.fingerprint_hash = fingerprint  # Ensure the job has it set for writing

    # Generate normalized title for database storage if needed
    from app.services.dedup.company_normalizer import normalize_title, normalize_company
    job.title_normalized = normalize_title(job.title)
    job.company_normalized = normalize_company(job.company_name)

    result_fp = await db.execute(
        select(JobPosting.id).where(JobPosting.fingerprint_hash == fingerprint)
    )
    if result_fp.first():
        return DUPLICATE_CROSS

    # ── New Record ───────────────────────────────────────────
    return NEW_RECORD
