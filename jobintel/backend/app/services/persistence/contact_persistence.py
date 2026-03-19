"""
Contact Persistence – handles saving extracted contacts to the database.
"""

from uuid import UUID
from typing import List, Dict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company_contact import CompanyContact
from app.core.logging import get_logger
from app.utils.contact_validation import is_valid_phone_number

logger = get_logger(__name__)

async def save_extracted_contacts(
    db: AsyncSession, 
    company_id: UUID, 
    contacts: Dict[str, List[str]],
    source: str = "job_description"
) -> None:
    """
    Saves extracted emails and phones to the company_contacts table.
    Avoids duplicate entries for the same company and email/phone.
    """
    if not company_id:
        return

    emails = contacts.get("emails", [])
    phones = contacts.get("phones", [])

    for email in emails:
        # Check if already exists for this company
        stmt = select(CompanyContact).where(
            CompanyContact.company_id == company_id,
            CompanyContact.email == email
        )
        res = await db.execute(stmt)
        if not res.scalar_one_or_none():
            contact = CompanyContact(
                company_id=company_id,
                email=email,
                source=source
            )
            db.add(contact)
            logger.info("Saved new email contact for company %s: %s", company_id, email)

    for phone in phones:
        # Validate phone number before saving
        if not is_valid_phone_number(phone):
            logger.info("Skipped invalid phone number for company %s: %s", company_id, phone)
            continue
            
        # Check if already exists for this company
        stmt = select(CompanyContact).where(
            CompanyContact.company_id == company_id,
            CompanyContact.phone == phone
        )
        res = await db.execute(stmt)
        if not res.scalar_one_or_none():
            contact = CompanyContact(
                company_id=company_id,
                phone=phone,
                source=source
            )
            db.add(contact)
            logger.info("Saved new phone contact for company %s: %s", company_id, phone)

    await db.flush()
