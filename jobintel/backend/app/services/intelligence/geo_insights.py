"""
Geo Insights Engine – computes geographical job distributions at country and city levels.
"""

from datetime import datetime, timedelta, timezone, date
from typing import List, Dict, Any

from sqlalchemy import select, func, text, cast, Date
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job_posting import JobPosting
from app.core.logging import get_logger

logger = get_logger(__name__)


def apply_filters(query, domain: str = None, platform: str = None, date_range: str = "30d"):
    """Apply optional filters to the base query."""
    if domain:
        query = query.where(JobPosting.domain == domain)
    if platform:
        query = query.where(JobPosting.source_platform == platform)
    if date_range:
        try:
            days = int(date_range.replace("d", ""))
            cutoff = datetime.now(timezone.utc).date() - timedelta(days=days)
            query = query.where(cast(JobPosting.posted_at, Date) >= cutoff)
        except ValueError:
            pass
    return query


async def get_country_heatmap(
    db: AsyncSession, 
    domain: str = None, 
    platform: str = None, 
    date_range: str = "30d"
) -> List[Dict[str, Any]]:
    """Aggregate job volume and top signals per country."""
    
    # ── 1. Base Aggregation per Country
    base_query = select(
        JobPosting.location_country.label("country"),
        func.count().label("job_count")
    )
    
    base_query = apply_filters(base_query, domain, platform, date_range)
    base_query = base_query.group_by(JobPosting.location_country)
    
    res = await db.execute(base_query)
    countries_data = {row.country: {"country": row.country, "job_count": int(row.job_count), "top_domain": "Unknown", "top_company": None} for row in res}
    
    if not countries_data:
        return []
        
    date_filter = ""
    params = {}
    if date_range:
        try:
            days = int(date_range.replace("d", ""))
            cutoff = datetime.now(timezone.utc).date() - timedelta(days=days)
            date_filter = "AND cast(posted_at as date) >= :cutoff"
            params["cutoff"] = cutoff
        except ValueError:
            pass

    # ── 2. Top Domain CTE window function
    top_domain_sql = text(f"""
        WITH DomainCounts AS (
            SELECT COALESCE(location_country, 'Unknown') as country, domain, count(*) as cnt
            FROM job_postings
            WHERE domain IS NOT NULL {date_filter}
            GROUP BY COALESCE(location_country, 'Unknown'), domain
        ),
        RankedDomains AS (
            SELECT country, domain, cnt,
                   ROW_NUMBER() OVER(PARTITION BY country ORDER BY cnt DESC) as rn
            FROM DomainCounts
        )
        SELECT country, domain
        FROM RankedDomains
        WHERE rn = 1
    """)
    res_dom = await db.execute(top_domain_sql, params)
    for row in res_dom:
        if row.country in countries_data:
            countries_data[row.country]["top_domain"] = row.domain
            
    # ── 3. Top Company CTE window function
    top_company_sql = text(f"""
        WITH CompanyCounts AS (
            SELECT COALESCE(location_country, 'Unknown') as country, company_id, company_name, count(*) as cnt
            FROM job_postings
            WHERE company_id IS NOT NULL 
              AND company_name NOT ILIKE '%confidential%' {date_filter}
            GROUP BY COALESCE(location_country, 'Unknown'), company_id, company_name
        ),
        RankedCompanies AS (
            SELECT country, company_id, company_name, cnt,
                   ROW_NUMBER() OVER(PARTITION BY country ORDER BY cnt DESC) as rn
            FROM CompanyCounts
        )
        SELECT country, company_id, company_name, cnt
        FROM RankedCompanies
        WHERE rn = 1
    """)
    res_comp = await db.execute(top_company_sql, params)
    for row in res_comp:
        if row.country in countries_data:
            countries_data[row.country]["top_company"] = {
                "company_id": str(row.company_id),
                "company_name": row.company_name,
                "job_count": int(row.cnt)
            }
            
    return sorted(list(countries_data.values()), key=lambda x: x["job_count"], reverse=True)


async def get_city_breakdown(
    db: AsyncSession, 
    country: str,
    domain: str = None, 
    platform: str = None, 
    date_range: str = "30d"
) -> List[Dict[str, Any]]:
    """Aggregate job volume per city inside a specific country."""
    
    # ── 1. Base Aggregation per City
    base_query = select(
        JobPosting.location_city.label("city"),
        func.count().label("job_count")
    ).where(
        JobPosting.location_country == country,
        JobPosting.location_city.is_not(None)
    )
    
    base_query = apply_filters(base_query, domain, platform, date_range)
    base_query = base_query.group_by(JobPosting.location_city)
    
    res = await db.execute(base_query)
    cities_data = {row.city: {"city": row.city, "job_count": int(row.job_count), "top_company": None} for row in res}
    
    if not cities_data:
        return []
        
    date_filter = ""
    params = {"country": country}
    if date_range:
        try:
            days = int(date_range.replace("d", ""))
            cutoff = datetime.now(timezone.utc).date() - timedelta(days=days)
            date_filter = "AND cast(posted_at as date) >= :cutoff"
            params["cutoff"] = cutoff
        except ValueError:
            pass
            
    # ── 2. Top Company CTE window function per city
    top_company_sql = text(f"""
        WITH CompanyCounts AS (
            SELECT location_city as city, company_id, company_name, count(*) as cnt
            FROM job_postings
            WHERE location_country = :country AND location_city IS NOT NULL 
              AND company_id IS NOT NULL AND company_name NOT ILIKE '%confidential%' {date_filter}
            GROUP BY location_city, company_id, company_name
        ),
        RankedCompanies AS (
            SELECT city, company_id, company_name, cnt,
                   ROW_NUMBER() OVER(PARTITION BY city ORDER BY cnt DESC) as rn
            FROM CompanyCounts
        )
        SELECT city, company_id, company_name, cnt
        FROM RankedCompanies
        WHERE rn = 1
    """)
    res_comp = await db.execute(top_company_sql, params)
    for row in res_comp:
        if row.city in cities_data:
            cities_data[row.city]["top_company"] = {
                "company_id": str(row.company_id),
                "company_name": row.company_name,
                "job_count": int(row.cnt)
            }
            
    return sorted(list(cities_data.values()), key=lambda x: x["job_count"], reverse=True)
