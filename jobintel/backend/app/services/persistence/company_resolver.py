"""
Company resolution – find existing company by normalized name or create a new one.
"""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.company import Company
from app.services.dedup.company_normalizer import normalize_company

logger = get_logger(__name__)


async def resolve_company(db: AsyncSession, company_name: str) -> UUID:
    """Resolve a company by name, creating it if it doesn't exist."""
    
    # 1. Normalize name for matching
    normalized_name = normalize_company(company_name)
    if not normalized_name:
        # Fallback if normalization strips everything
        normalized_name = company_name.lower().strip()
        
    # 2. Check if company exists
    result = await db.execute(
        select(Company).where(Company.company_name_normalized == normalized_name)
    )
    company = result.scalar_one_or_none()
    
    if company:
        return company.id
        
    # 3. Create new company
    now = datetime.now(timezone.utc)
    new_company = Company(
        company_name=company_name,
        company_name_normalized=normalized_name,
        first_seen_at=now,
        last_active_at=now,
        domains_active=[],
        platforms_seen_on=[],
        locations=[],
        countries=[],
        total_postings_alltime=0,
    )
    db.add(new_company)
    await db.flush()  # Populate new_company.id
    
    logger.info("Company created: %s (id=%s)", company_name, new_company.id)
    return new_company.id
