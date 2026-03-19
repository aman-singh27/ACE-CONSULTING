"""
Contact Validation Utility - validates phone numbers and emails for quality.
"""

import re
from typing import Optional

# Phone number blacklist - invalid/placeholder phone numbers (these should be exact digit matches)
INVALID_PHONE_NUMBERS = {
    "114190",
    "1111111111",
    "0000000000",
    "1234567890",
    "9999999999",
    "5555555555",
    "4444444444",
    "3333333333",
    "2222222222",
}

# Keywords that shouldn't appear in valid phone numbers
INVALID_KEYWORDS = {
    "unknown",
    "contact",
    "placeholder",
    "example",
    "sample",
    "test",
}


def is_valid_phone_number(phone: Optional[str]) -> bool:
    """
    Validates a phone number.
    
    Requirements:
    - Must have at least 8 digits (after removing all non-digits)
    - Must not be a known invalid/placeholder number
    - Must not contain only repeating digits  
    - Must not contain invalid keywords (unknown, test, etc)
    
    Args:
        phone: Raw phone number string
        
    Returns:
        True if phone is valid, False otherwise
    """
    if not phone:
        return False
    
    phone_str = str(phone).strip()
    
    # Check for exact blacklisted strings (case-insensitive)
    phone_lower = phone_str.lower()
    
    # Check if it contains invalid keywords
    for keyword in INVALID_KEYWORDS:
        if keyword in phone_lower:
            return False
    
    # Extract only digits
    digits_only = re.sub(r'\D', '', phone_str)
    
    # Check for exact blacklisted numbers
    if digits_only in INVALID_PHONE_NUMBERS:
        return False
    
    # Must have at least 8 digits
    if len(digits_only) < 8:
        return False
    
    # Check for repeating digits (11111111, 22222222, etc.) - 8+ of same digit
    if re.match(r'^(\d)\1{7,}$', digits_only):
        return False
    
    # Valid phone numbers should have some formatting or reasonable length
    # Minimum 10 digits for most valid phone numbers
    has_formatting = bool(re.search(r'[\s\-()\.+]', phone_str))
    has_10_or_more_digits = len(digits_only) >= 10
    
    # Valid if: has 10+ digits, OR (has 8-9 digits AND proper formatting)
    return has_10_or_more_digits or (8 <= len(digits_only) < 10 and has_formatting)


def get_valid_contacts_for_company(contacts: list) -> dict:
    """
    Filters contacts to only include those with valid phone or email.
    
    Args:
        contacts: List of CompanyContact objects
        
    Returns:
        Dict with 'has_valid_contact', 'valid_phones', 'valid_emails'
    """
    valid_phones = []
    valid_emails = []
    
    for contact in contacts:
        if contact.phone and is_valid_phone_number(contact.phone):
            valid_phones.append(contact.phone)
        if contact.email and "@" in str(contact.email):  # Basic email validation
            valid_emails.append(contact.email)
    
    return {
        "has_valid_contact": bool(valid_phones or valid_emails),
        "valid_phones": valid_phones,
        "valid_emails": valid_emails,
    }
