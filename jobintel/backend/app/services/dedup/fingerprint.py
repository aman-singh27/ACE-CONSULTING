"""
Fingerprinting logic to generate exact and cross-platform unique identifiers.
"""

from typing import Optional

from app.schemas.standard_job import StandardJob
from app.services.dedup.company_normalizer import normalize_company, normalize_title
from app.services.dedup.hashing import sha256_hash


def generate_job_id(job: StandardJob) -> str:
    """Generate Level 1 exact duplicate hash.

    Logic: SHA256(source_platform + job_url)
    """
    url = job.job_url or ""
    hash_input = f"{job.source_platform}:{url}"
    return sha256_hash(hash_input)


def generate_fingerprint(job: StandardJob) -> str:
    """Generate Level 2 cross-platform fuzzy duplicate hash.

    Logic: SHA256(company_normalized + title_normalized + location_country + date_bucket)
    """
    # 1. Normalize core identity pieces
    comp_norm = normalize_company(job.company_name)
    title_norm = normalize_title(job.title)

    # 2. Country defaults to empty if missing
    country = (job.location_country or "").lower().strip()

    # 3. Date bucket (YYYY-MM-DD resolution)
    # If no date provided, fingerprint is weaker but still works for same-moment scrapes
    date_str = ""
    if job.posted_at:
        date_str = job.posted_at.strftime("%Y-%m-%d")

    # 4. Hash combination
    hash_input = f"{comp_norm}|{title_norm}|{country}|{date_str}"
    return sha256_hash(hash_input)
