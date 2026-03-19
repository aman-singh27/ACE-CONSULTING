"""
Contact Extractor – extracts emails and phone numbers from raw text.
"""

import re
from typing import List, Dict, Set

from app.utils.contact_validation import is_valid_phone_number

# regex for emails
EMAIL_REGEX = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'

# permissive regex for phone numbers
PHONE_REGEX = r'(?:\+?\d{1,4}[-.\s]?)?\(?\d{2,5}\)?(?:[-.\s]?\d{2,5})?[-.\s]?\d{4}'

# blacklist for common template/placeholder emails found in job descriptions
EMAIL_BLACKLIST = {
    "accommodation-request_mb@oracle.com",
    "ta-ops@purestorage.com",
    "careercentersupport@fhi360.org",
    "firstname.lastname@cevalogistics.com",
    "careers@sap.com",
    "recruitment@premiumsolutions.qa"
}


def extract_contacts(text: str) -> Dict[str, List[str]]:
    """
    Extracts unique emails and phone numbers from the provided text.
    Filters out common blacklisted template emails and limits the number of results.
    """
    if not text:
        return {"emails": [], "phones": []}
    
    # 1. Emails
    raw_emails = set(e.lower() for e in re.findall(EMAIL_REGEX, text))
    clean_emails: Set[str] = set()
    
    for e in raw_emails:
        # Remove trailing junk often found in scraped footers
        e = re.sub(r'\.(for|fhi|is|the|about|to|and|if|during|at|your|our|we)$', '', e, flags=re.IGNORECASE)
        if e not in EMAIL_BLACKLIST:
            clean_emails.add(e)
    
    # 2. Phones
    raw_phones: Set[str] = set(re.findall(PHONE_REGEX, text))
    clean_phones: Set[str] = set()
    
    for phone in raw_phones:
        # Validate phone before including it
        if is_valid_phone_number(phone):
            clean_phones.add(phone)
    
    # Limit to top 5 to keep table usable
    return {
        "emails": sorted(list(clean_emails))[:5],
        "phones": sorted(list(clean_phones))[:5]
    }
