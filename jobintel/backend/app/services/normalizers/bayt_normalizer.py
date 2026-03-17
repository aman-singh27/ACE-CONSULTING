import re
from datetime import datetime
from typing import Any, Optional

from app.core.logging import get_logger
from app.schemas.standard_job import StandardJob

logger = get_logger(__name__)


def _extract_company_from_description(description: str) -> Optional[str]:
    """Helper to extract company name from description using common patterns."""
    if not description:
        return None
        
    patterns = [
        # Explicit markers - very high confidence
        r"Location of posting\s*-\s*([^.\n\r]{2,50})",
        r"check our website\s*\(www\.([^.\s/]{2,40})\.com\)",
        # Career site markers
        r"([^.\n\r]{2,50})\s+will never ask for money",
        r"About\s+([A-Z][^.\n\r]{2,50})\b", # Must start with Capital
        # Hiring markers
        r"([A-Z][^.\n\r]{2,40})\s+is seeking",
        r"([A-Z][^.\n\r]{2,40})\s+is looking for",
        r"At\s+([A-Z][^.\n\r]{2,40})\b", # At {Company}
    ]
    
    blacklist = [
        "innovation", "problem-solving", "collaborating", "hiring", "reputable", 
        "dynamic", "leading", "established", "client", "customer", "successful",
        "position", "role", "team", "brand", "company", "organization", "we", "us",
        "our", "the", "this", "finding", "abuse", "sexual", "harassment", "policy",
        "may", "arise", "rate", "one", "of", "within", "as", "part", "a", "an",
        "about", "is", "are", "to", "for", "in", "with", "by", "from", "at", "be"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, description) # Removed IGNORECASE for some
        if not match and "About" not in pattern:
            # Try again with IGNORECASE for non-capital sensitive patterns
            match = re.search(pattern, description, re.IGNORECASE)
            
        if match:
            name = match.group(1).strip()
            # Basic cleanup
            name = re.sub(r"\s+", " ", name)
            
            words = name.split()
            if len(words) > 5: 
                continue
            if len(name) < 3 or len(name) > 50:
                continue
                
            # Check blacklist
            lower_name = name.lower()
            if any(term in lower_name for term in blacklist):
                continue
                
            if "..." in name or "http" in name or "@" in name:
                continue
                
            return name
    return None


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
    """Normalize a raw Bayt scraper record with smart company extraction."""

    # 1. Primary Company Extraction
    company = raw.get("company") or raw.get("companyName") or raw.get("company_name")
    is_placeholder = False
    
    if company:
        placeholders = ["confidential", "unknown", "top company", "leading company", "a client of bayt", "a reputable company"]
        if company.lower().strip() in placeholders:
            is_placeholder = True
    else:
        is_placeholder = True

    # 2. Description Extraction
    description = (
        raw.get("descriptionText")
        or raw.get("description")
        or raw.get("listingSummary")
    )
    
    # 3. Smart Fallbacks
    if is_placeholder:
        # A. Check Title for @ pattern (e.g. "Site Logistics Coordinator @Siemens Mobility Egypt")
        title = raw.get("title") or ""
        if "@" in title:
            parts = title.rsplit("@", 1)
            if len(parts) > 1:
                potential = parts[1].strip()
                if potential and 3 <= len(potential) <= 50:
                    company = potential
                    is_placeholder = False

        # B. Try slug from profile URL (often shows the real name/brand)
        if is_placeholder:
            profile_url = raw.get("companyProfileUrl") or ""
            if "bayt.com/en/company/" in profile_url:
                slug = profile_url.split("/company/")[-1].split("/")[0]
                if slug and not any(p in slug for p in ["confidential", "individual"]):
                    slug_clean = re.sub(r'-\d+$', '', slug).replace("-", " ").title()
                    company = slug_clean
                    is_placeholder = False
        
        # C. Check description start (e.g. "Siemens Mobility (SMO) is...")
        if is_placeholder and description:
            # Look at first two lines
            first_part = description.strip().split('\n')[0][:200]
            # Pattern: "CompanyName (ABBR) is" or "CompanyName is"
            match = re.search(r"^([A-Z][A-Za-z0-9\s&]{2,50})(\s*\([A-Z0-9]+\))?\s+is\s+(the|a|an)\b", first_part)
            if match:
                company = match.group(1).strip()
                is_placeholder = False
        
        # D. Generic Heuristics
        if is_placeholder and description:
            found_name = _extract_company_from_description(description)
            if found_name:
                company = found_name
                is_placeholder = False

    return StandardJob(
        title=raw.get("title") or "Unknown",
        company_name=company or "Unknown",
        job_url=raw.get("url") or raw.get("jobUrl") or "",
        source_platform="bayt",
        actor_id=actor_id,
        job_id=f"bayt_{raw.get('jobId')}" if raw.get("jobId") else None,
        location_raw=raw.get("location"),
        posted_at=_parse_date(raw.get("scrapedAt")),
        domain=domain,
        salary_raw=raw.get("salary"),
        employment_type=raw.get("employmentType") or raw.get("employment_type"),
        description_raw=description,
    )
