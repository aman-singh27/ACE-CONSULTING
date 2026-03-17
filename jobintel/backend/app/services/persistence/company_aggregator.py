"""
Company aggregation engine – updates company-level statistics and metadata 
based on incoming job postings.
"""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.company import Company
from app.schemas.standard_job import StandardJob

logger = get_logger(__name__)


async def update_company_aggregates(db: AsyncSession, company_id: UUID, job: StandardJob) -> None:
    """Update dynamically tracked company aggregates."""
    
    result = await db.execute(select(Company).where(Company.id == company_id))
    company = result.scalar_one()

    # ── Update Activity Time ─────────────────────────────────
    company.last_active_at = datetime.now(timezone.utc)
    company.total_postings_alltime += 1

    # ── Append Unique Lists ──────────────────────────────────
    # SQLAlchemy ARRAY requires reassignment or careful mutation tracking
    # Extract to new lists, modify, reassign
    platforms = list(company.platforms_seen_on or [])
    if job.source_platform and job.source_platform not in platforms:
        platforms.append(job.source_platform)
    company.platforms_seen_on = platforms

    domains = list(company.domains_active or [])
    if job.domain and job.domain not in domains:
        domains.append(job.domain)
    company.domains_active = domains

    locations = list(company.locations or [])
    loc_str = job.location_raw or job.location_city
    if loc_str and loc_str not in locations:
        locations.append(loc_str)
    company.locations = locations

    countries = list(company.countries or [])
    if job.location_country and job.location_country not in countries:
        countries.append(job.location_country)
    company.countries = countries

    # Flush changes
    await db.flush()
    logger.info("Company aggregates updated: id=%s", company_id)

