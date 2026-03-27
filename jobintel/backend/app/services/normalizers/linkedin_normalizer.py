"""
LinkedIn normalizer – converts raw LinkedIn actor output to StandardJob.

Based on: cheap_scraper/linkedin-job-scraper

Key output fields:
  jobId, jobTitle, companyName, location, jobUrl, publishedAt,
  salaryInfo (["$93000.00","$130000.00"]), contractType,
  experienceLevel, jobDescription, companyAddress, sector, workType
"""

from datetime import datetime
from typing import Any, Optional

from app.core.logging import get_logger
from app.schemas.standard_job import StandardJob
from app.services.dedup.name_sanitizer import is_url_like, sanitize_company_name

logger = get_logger(__name__)

MAX_DESCRIPTION_LENGTH = 5000


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


def _parse_salary_value(val: Any) -> Optional[float]:
    """Parse a salary string like '$93,000.00' or '93000' into a float."""
    if val is None:
        return None
    s = str(val).replace("$", "").replace(",", "").replace(" ", "").strip()
    try:
        return float(s)
    except (ValueError, TypeError):
        return None


def _parse_salary(salary_info: Any) -> tuple[Optional[float], Optional[float], Optional[str]]:
    """Extract min/max salary from LinkedIn salaryInfo field.

    LinkedIn returns salaryInfo as a list of strings like ["$93000.00", "$130000.00"].
    Returns (min, max, raw_string).
    """
    if not salary_info:
        return None, None, None

    raw_str = str(salary_info)

    if isinstance(salary_info, (list, tuple)):
        min_val = _parse_salary_value(salary_info[0]) if len(salary_info) >= 1 else None
        max_val = _parse_salary_value(salary_info[1]) if len(salary_info) >= 2 else None
        return min_val, max_val, raw_str

    return None, None, raw_str


def _extract_location_parts(raw: dict[str, Any]) -> tuple[Optional[str], Optional[str], Optional[str]]:
    """Extract city, country, region from companyAddress if enrichCompanyData was enabled,
    or fallback to parsing the raw location string if possible."""
    
    # 1. Try structured address
    addr = raw.get("companyAddress")
    if addr and isinstance(addr, dict):
        city = addr.get("addressLocality")
        region = addr.get("addressRegion")
        country = addr.get("addressCountry")
        if city or country or region:
            return city, country, region

    # 2. Try parsing raw location string like "Dubai, Dubai, United Arab Emirates"
    raw_loc = raw.get("location")
    if not raw_loc or not isinstance(raw_loc, str):
        return None, None, None
        
    parts = [p.strip() for p in raw_loc.split(",")]
    if len(parts) == 1:
        # Just a country or city
        return None, parts[0], None
    elif len(parts) == 2:
        # e.g. "Dubai, United Arab Emirates"
        return parts[0], parts[1], None
    elif len(parts) >= 3:
        # e.g. "Dubai, Dubai Emirate, United Arab Emirates"
        return parts[0], parts[-1], parts[1]
        
    return None, None, None


def normalize_linkedin_job(
    raw: dict[str, Any],
    actor_id: str,
    domain: Optional[str] = None,
) -> StandardJob:
    """Normalize a raw LinkedIn scraper record."""

    salary_min, salary_max, salary_raw = _parse_salary(raw.get("salaryInfo"))

    # Description – prefer jobDescription, truncate to limit
    description = raw.get("jobDescription") or raw.get("description") or ""
    if len(description) > MAX_DESCRIPTION_LENGTH:
        description = description[:MAX_DESCRIPTION_LENGTH]

    # Location parts from companyAddress (when enrichCompanyData=true)
    loc_city, loc_country, loc_region = _extract_location_parts(raw)

    # Build unique job_id from LinkedIn's jobId
    job_id_raw = raw.get("jobId")
    job_id = f"linkedin_{job_id_raw}" if job_id_raw else None

    # Extract and sanitize company name — scrapers sometimes return URLs
    raw_company = raw.get("companyName") or raw.get("company") or "Unknown"
    company_name = sanitize_company_name(raw_company)
    if company_name != raw_company:
        logger.warning("LinkedIn: sanitized URL company name: %s → %s", raw_company, company_name)

    return StandardJob(
        title=raw.get("jobTitle") or raw.get("title") or "Unknown",
        company_name=company_name,
        job_url=raw.get("jobUrl") or raw.get("url") or "",
        source_platform="linkedin",
        actor_id=actor_id,
        job_id=job_id,
        location_raw=raw.get("location"),
        location_city=loc_city,
        location_country=loc_country,
        location_region=loc_region,
        posted_at=_parse_date(raw.get("publishedAt") or raw.get("postedAt")),
        domain=domain,
        salary_raw=salary_raw,
        salary_min=salary_min,
        salary_max=salary_max,
        employment_type=raw.get("contractType") or raw.get("employmentType"),
        description_raw=description or None,
    )
