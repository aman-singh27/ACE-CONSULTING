"""
NaukriGulf normalizer – converts raw NaukriGulf actor output to StandardJob.

Based on: shahidirfan/nukrigulf-job-scraper

Key output fields:
  job_id, job_title, company, company_id, company_url, location,
  experience_min_years, experience_max_years, salary, job_type,
  job_url, date_posted, description_text, summary, vacancies
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


def _safe_int(value: Any) -> Optional[int]:
    """Convert to int or return None."""
    if value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def normalize_naukrigulf_job(
    raw: dict[str, Any],
    actor_id: str,
    domain: Optional[str] = None,
) -> StandardJob:
    """Normalize a raw NaukriGulf scraper record."""

    # Build unique job_id from NaukriGulf's job_id
    job_id_raw = raw.get("job_id")
    job_id = f"naukrigulf_{job_id_raw}" if job_id_raw else None

    return StandardJob(
        title=raw.get("job_title") or raw.get("title") or "Unknown",
        company_name=raw.get("company") or raw.get("company_name") or "Unknown",
        job_url=raw.get("job_url") or raw.get("url") or "",
        source_platform="naukrigulf",
        actor_id=actor_id,
        job_id=job_id,
        location_raw=raw.get("location"),
        posted_at=_parse_date(raw.get("date_posted")),
        domain=domain,
        salary_raw=raw.get("salary"),
        employment_type=raw.get("job_type") or raw.get("employment_type"),
        experience_years_min=_safe_int(raw.get("experience_min_years")),
        experience_years_max=_safe_int(raw.get("experience_max_years")),
        description_raw=raw.get("description_text") or raw.get("description"),
    )
