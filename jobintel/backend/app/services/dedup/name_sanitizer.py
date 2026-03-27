"""
Name sanitizer – detects and cleans URL-like strings used as company names.
"""

import re
from typing import Optional
from urllib.parse import urlparse


# Patterns that indicate a string is a URL, not a company name
_URL_PREFIXES = ("http://", "https://", "www.")
_URL_PATTERN = re.compile(
    r"^(https?://|www\.)|"         # starts with protocol or www.
    r"://|"                         # contains :// anywhere
    r"\.(com|io|org|net|co|ae|in|sa|qa|bh|kw|om|pk|lk|eg|ng)/",  # domain TLD followed by path
    re.IGNORECASE,
)

# Known job board domains → we can try to extract the company from the URL path
_JOB_BOARD_DOMAINS = {
    "linkedin.com", "in.linkedin.com", "uk.linkedin.com", "ae.linkedin.com",
    "bayt.com", "www.bayt.com",
    "naukrigulf.com", "www.naukrigulf.com",
    "indeed.com", "www.indeed.com",
    "glassdoor.com", "www.glassdoor.com",
}

# Domain → human-readable company name for company career sites
# When the URL is a company's own career page (not a job board)
_KNOWN_COMPANY_DOMAINS = {
    "meesho.io": "Meesho",
    "careers.meesho.io": "Meesho",
    "jobs.lever.co": None,  # Lever is a job platform, company is in path
    "boards.greenhouse.io": None,  # Greenhouse, company is in path
    "apply.workable.com": None,  # Workable, company is in path
}


def is_url_like(name: str) -> bool:
    """Check if a string looks like a URL rather than a company name.
    
    Examples that return True:
      - "https://in.linkedin.com/jobs/view/senior-manager-at-meesho-4363554399"
      - "https://meesho.io/jobs/deputy-manager--logistics"
      - "www.somecompany.com/careers"
    
    Examples that return False:
      - "Meesho"
      - "myGwork - LGBTQ+ Business Community"
      - "Amazon Web Services (AWS)"
    """
    if not name or len(name) < 5:
        return False

    name_stripped = name.strip()

    # Quick prefix check
    for prefix in _URL_PREFIXES:
        if name_stripped.lower().startswith(prefix):
            return True

    # Regex check for URL patterns
    if _URL_PATTERN.search(name_stripped):
        return True

    return False


def _extract_company_from_url(url: str) -> Optional[str]:
    """Try to extract a meaningful company name from a URL.
    
    Strategy:
    1. For known company career sites (meesho.io, etc.) → return the known name
    2. For job boards (linkedin.com, etc.) → try to parse company from path
       e.g. "...at-meesho-4363554399" → "Meesho"
    3. For Lever/Greenhouse/Workable → extract from path segment
    4. For unknown domains → extract from domain name
    """
    try:
        # Ensure the URL has a scheme for urlparse
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        parsed = urlparse(url)
        hostname = (parsed.hostname or "").lower()
        path = parsed.path or ""
    except Exception:
        return None

    # 1. Known company career sites
    if hostname in _KNOWN_COMPANY_DOMAINS:
        known_name = _KNOWN_COMPANY_DOMAINS[hostname]
        if known_name:
            return known_name
        # For platforms like Lever/Greenhouse, company is usually the first path segment
        # e.g. jobs.lever.co/meesho/job-id → "Meesho"
        segments = [s for s in path.split("/") if s]
        if segments:
            return segments[0].replace("-", " ").replace("_", " ").title()

    # 2. LinkedIn job URLs → extract company from title slug
    # Pattern: /jobs/view/{title}-at-{company}-{id}
    if "linkedin.com" in hostname:
        match = re.search(r"-at-([a-z0-9-]+)-\d+$", path, re.IGNORECASE)
        if match:
            company_slug = match.group(1)
            return company_slug.replace("-", " ").title()

    # 3. Job board URLs (bayt, naukrigulf, indeed) → try path extraction
    if hostname.replace("www.", "") in {"bayt.com", "naukrigulf.com", "indeed.com"}:
        # Try to find company in path segments
        if "/company/" in path:
            company_slug = path.split("/company/")[-1].split("/")[0]
            if company_slug:
                return re.sub(r"-\d+$", "", company_slug).replace("-", " ").title()

    # 4. Unknown domain → extract company name from hostname
    # e.g. "meesho.io" → "Meesho", "careers.amazon.com" → "Amazon"
    if hostname not in _JOB_BOARD_DOMAINS:
        # Strip common subdomains
        parts = hostname.split(".")
        # Remove common prefixes like www, careers, jobs, apply
        skip_prefixes = {"www", "careers", "jobs", "apply", "boards", "hire"}
        meaningful_parts = [p for p in parts if p not in skip_prefixes and len(p) > 2]
        
        if meaningful_parts:
            # Use the first meaningful part (usually the brand name)
            # e.g. ["meesho", "io"] → "Meesho"
            company_name = meaningful_parts[0]
            # Skip TLDs
            tlds = {"com", "org", "net", "io", "co", "ae", "in", "sa", "qa", "bh", "kw", "om", "pk"}
            if company_name not in tlds:
                return company_name.title()

    return None


def sanitize_company_name(name: str) -> str:
    """Sanitize a company name: if it's a URL, extract the real name.
    
    Returns the cleaned company name, or 'Unknown' if extraction fails.
    
    Examples:
      - "https://meesho.io/jobs/deputy-manager" → "Meesho"
      - "https://in.linkedin.com/jobs/view/senior-manager-at-meesho-4363554399" → "Meesho"
      - "Normal Company Name" → "Normal Company Name" (unchanged)
    """
    if not name:
        return "Unknown"

    name = name.strip()

    if not is_url_like(name):
        return name

    # Try to extract company name from the URL
    extracted = _extract_company_from_url(name)
    if extracted and len(extracted) >= 2:
        return extracted

    return "Unknown"
