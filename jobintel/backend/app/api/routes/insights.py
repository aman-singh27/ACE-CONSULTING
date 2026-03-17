"""
Insights API endpoints (BD Priority List, etc.)
"""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.company import Company
from app.schemas.api import PriorityListCompany, DomainTrendsResponse

from app.services.intelligence.priority_engine import get_bd_priority_list
from app.services.intelligence.domain_insights import get_domain_trends
from app.services.intelligence.geo_insights import get_country_heatmap, get_city_breakdown

router = APIRouter(tags=["insights"])

@router.get("/priority-list", response_model=list[PriorityListCompany])
async def get_priority_list(limit: int = 10, db: AsyncSession = Depends(get_db)):
    """Fetch the top companies ordered by dynamic Business Development Priority Score."""
    return await get_bd_priority_list(db, limit)


@router.get("/domain-trends", response_model=list[DomainTrendsResponse])
async def get_domain_trends_api(domain: str = None, period: str = "60d", db: AsyncSession = Depends(get_db)):
    """Fetch aggregated hiring statistics and top companies by domain."""
    return await get_domain_trends(db, domain=domain, period=period)

@router.get("/geo-heatmap")
async def get_geo_heatmap_api(
    group: str = "country",
    country: str = None,
    domain: str = None,
    platform: str = None,
    date_range: str = "30d",
    db: AsyncSession = Depends(get_db)
):
    """Fetch geographical job distribution across countries or cities."""
    if group == "city" and country:
        return await get_city_breakdown(db, country=country, domain=domain, platform=platform, date_range=date_range)
    
    # Default behavior is country heatmap
    return await get_country_heatmap(db, domain=domain, platform=platform, date_range=date_range)
