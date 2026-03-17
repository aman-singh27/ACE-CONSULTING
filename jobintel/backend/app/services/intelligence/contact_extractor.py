"""
Contact Extractor – extracts emails and phone numbers from raw text.
"""

import re
from typing import List, Dict, Set

# regex for emails
EMAIL_REGEX = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'

# permissive regex for phone numbers
PHONE_REGEX = r'(?:\+?\d{1,4}[-.\s]?)?\(?\d{2,5}\)?(?:[-.\s]?\d{2,5})?[-.\s]?\d{4}'

def extract_contacts(text: str) -> Dict[str, List[str]]:
    """
    Extracts unique emails and phone numbers from the provided text.
    """
    if not text:
        return {"emails": [], "phones": []}
    
    emails: Set[str] = set(re.findall(EMAIL_REGEX, text))
    phones: Set[str] = set(re.findall(PHONE_REGEX, text))
    
    # Clean up phone numbers slightly (remove extra spaces or dots if needed, 
    # but keeping raw for now as per simple regex)
    
    return {
        "emails": list(emails),
        "phones": list(phones)
    }
