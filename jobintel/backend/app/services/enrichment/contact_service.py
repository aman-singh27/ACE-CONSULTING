import logging
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Company
from app.models.company_contact import CompanyContact
from app.services.apollo.apollo_client import ApolloClient

logger = logging.getLogger(__name__)
apollo_client = ApolloClient()

async def fetch_company_contacts(db: AsyncSession, company_id: UUID) -> list[CompanyContact]:
    """
    Fetches contacts for a company from the cache by company_id. 
    If none exist, calls Apollo people search, caches the results, and returns them.
    """
    # 1. Fetch company from DB
    company = await db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Extract domain
    domain = None
    if company.domains_active and len(company.domains_active) > 0:
        domain = company.domains_active[0]
    elif company.website:
        domain = company.website.replace("https://", "").replace("http://", "").replace("www.", "").split("/")[0]

    if not domain:
        raise HTTPException(status_code=400, detail="Company has no domain or website to enrich")

    logger.info(f"Searching contacts for domain: {domain}")

    # 2. Check company_contacts table
    result = await db.execute(
        select(CompanyContact).where(CompanyContact.company_id == company.id)
    )
    existing = result.scalars().all()

    # 3. If contacts exist -> return cached
    if existing:
        logger.info(f"Returning cached contacts for {domain}")
        return list(existing)

    # 4. Call Apollo people search
    logger.info("Calling Apollo people search")
    try:
        data = await apollo_client.search_people(domain)
    except Exception as e:
        logger.error(f"Apollo people search failed: {e}")
        raise HTTPException(status_code=502, detail=f"Apollo search failed: {str(e)}")

    people = data.get("people", [])
    logger.info(f"Contacts found: {len(people)}")

    contacts = []
    # 5. Store contacts
    for p in people:
        contact = CompanyContact(
            company_id=company.id,
            full_name=p.get("name"),
            title=p.get("title"),
            email=p.get("email"),
            linkedin_url=p.get("linkedin_url"),
            department=p.get("department"),
            seniority=p.get("seniority"),
            source="apollo"
        )
        db.add(contact)
        contacts.append(contact)

    await db.commit()
    logger.info("Stored contacts in DB")

    return contacts
