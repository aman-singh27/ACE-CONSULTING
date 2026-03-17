import logging
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

from app.models.company import Company
from app.models.enrichment_cache import EnrichmentCache
from app.services.apollo.apollo_client import ApolloClient

logger = logging.getLogger(__name__)
apollo_client = ApolloClient()

async def enrich_company(db: AsyncSession, company_id: UUID) -> dict:
    """
    Enriches a company using Apollo.
    Checks cache first, if not found, calls Apollo and stores the result.
    Updates the Company record with enriched data.
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

    logger.info(f"Enriching company {company_name if (company_name:=company.company_name) else domain} ({domain})")

    # 2. Check enrichment_cache
    result = await db.execute(
        select(EnrichmentCache).where(EnrichmentCache.company_id == company.id)
    )
    cached = result.scalar_one_or_none()

    if cached and cached.raw_response:
        logger.info(f"Cache hit: true for company {company_id}")
        return cached.raw_response

    logger.info(f"Cache hit: false for company {company_id}")
    logger.info("Calling Apollo enrichment")

    # 4. Call Apollo
    try:
        data = await apollo_client.enrich_company(domain)
    except Exception as e:
        logger.error(f"Apollo call failed: {e}")
        raise HTTPException(status_code=502, detail=f"Apollo enrichment failed: {str(e)}")

    org = data.get("organization", {})
    if not org:
        logger.warning(f"Apollo returned no organization data for {domain}")
        return data

    # 5. Store enrichment_cache
    cache = EnrichmentCache(
        company_id=company.id,
        apollo_org_id=org.get("id"),
        raw_response=data,
        employee_count=str(org.get("estimated_num_employees")) if org.get("estimated_num_employees") else None,
        founded_year=org.get("founded_year"),
        revenue_range=None,
        technologies=[],
        enriched_by="system",
        enriched_at=datetime.now(timezone.utc)
    )
    db.add(cache)

    # 6. Update company table
    company.employee_count = str(org.get("estimated_num_employees")) if org.get("estimated_num_employees") else company.employee_count
    company.industry_apollo = org.get("industry") or company.industry_apollo
    company.website = org.get("website_url") or company.website
    company.linkedin_url = org.get("linkedin_url") or company.linkedin_url
    company.is_enriched = True
    company.enriched_at = datetime.now(timezone.utc)
    company.apollo_data = data

    await db.commit()

    return data
