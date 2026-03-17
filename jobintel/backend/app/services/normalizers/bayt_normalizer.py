"""
Bayt normalizer – converts raw Bayt actor output to StandardJob.

Based on: shahidirfan/bayt-jobs-scraper

Key output fields:
  jobId, title, company, companyProfileUrl, url, location,
  postedAtRelative, employmentType, careerLevel, experience,
  salary, descriptionText, descriptionHtml, skillsText,
  preferredCandidate, scrapedAt
"""

from datetime import datetime
from typing import Any, Optional

from app.core.logging import get_logger
from app.schemas.standard_job import StandardJob

logger = get_logger(__name__)


def _parse_date(value: Any) -> Optional[datetime]:
    """Best-effort ISO date parsing."""
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def normalize_bayt_job(
    raw: dict[str, Any],
    actor_id: str,
    domain: Optional[str] = None,
) -> StandardJob:
    """Normalize a raw Bayt scraper record."""

    # Build unique job_id from Bayt's jobId
    job_id_raw = raw.get("jobId")
    job_id = f"bayt_{job_id_raw}" if job_id_raw else None

    # Description – prefer descriptionText, fall back to listingSummary
    description = (
        raw.get("descriptionText")
        or raw.get("description")
        or raw.get("listingSummary")
    )

    return StandardJob(
        title=raw.get("title") or "Unknown",
        company_name=raw.get("company") or raw.get("companyName") or "Unknown",
        job_url=raw.get("url") or raw.get("jobUrl") or "",
        source_platform="bayt",
        actor_id=actor_id,
        job_id=job_id,
        location_raw=raw.get("location"),
        posted_at=_parse_date(raw.get("scrapedAt")),
        domain=domain,
        salary_raw=raw.get("salary"),
        employment_type=raw.get("employmentType") or raw.get("employment_type"),
        description_raw=description,
    )
