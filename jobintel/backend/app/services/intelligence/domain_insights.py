"""
Domain Insights Engine – computes dynamic industry domain hiring trends.
"""

from datetime import datetime, timedelta, timezone, date
from typing import List, Dict, Any

from sqlalchemy import select, func, text, cast, Date
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job_posting import JobPosting
from app.core.logging import get_logger

logger = get_logger(__name__)


async def get_domain_trends(db: AsyncSession, domain: str = None, period: str = "60d") -> List[Dict[str, Any]]:
    """
    Computes domain-level hiring statistics by aggregating job postings dynamically.
    """
    now_utc = datetime.now(timezone.utc)
    today = now_utc.date()
    yesterday = today - timedelta(days=1)
    seven_days_ago = today - timedelta(days=7)
    fourteen_days_ago = today - timedelta(days=14)
    
    # ── 1. Base query for primary counts (today, yesterday, wow)
    # Using a single grouped query over the last 14 days
    select_stmt = [
        JobPosting.domain,
        func.count().filter(cast(JobPosting.posted_at, Date) == today).label("today_count"),
        func.count().filter(cast(JobPosting.posted_at, Date) == yesterday).label("yesterday_count"),
        func.count().filter(cast(JobPosting.posted_at, Date) >= seven_days_ago).label("jobs_last_7_days"),
        func.count().filter(
            cast(JobPosting.posted_at, Date) >= fourteen_days_ago,
            cast(JobPosting.posted_at, Date) < seven_days_ago
        ).label("jobs_previous_7_days"),
        func.count(func.distinct(JobPosting.company_id)).filter(
            cast(JobPosting.posted_at, Date) >= seven_days_ago
        ).label("active_companies")
    ]
    
    query = select(*select_stmt).where(
        cast(JobPosting.posted_at, Date) >= fourteen_days_ago,
        JobPosting.domain.is_not(None)
    )
    
    if domain:
        query = query.where(JobPosting.domain == domain)
        
    query = query.group_by(JobPosting.domain)
    res = await db.execute(query)
    rows = res.all()
    
    domains_data = {}
    for row in rows:
        dom = row.domain
        
        # Calculate WoW Change
        last_7 = float(row.jobs_last_7_days)
        prev_7 = float(row.jobs_previous_7_days)
        
        if prev_7 == 0:
            wow_change = 100.0 if last_7 > 0 else 0.0
        else:
            wow_change = ((last_7 - prev_7) / prev_7) * 100.0
            
        domains_data[dom] = {
            "domain": dom,
            "today_count": int(row.today_count),
            "yesterday_count": int(row.yesterday_count),
            "wow_change": round(wow_change, 2),
            "active_companies": int(row.active_companies),
            "top_company": None
        }
        
    # ── 2. Top Company via CTE Window Function ──────────
    # Compute the top hiring company in the last 7 days per domain
    top_company_sql = text("""
        WITH CompanyCounts AS (
            SELECT 
                domain,
                company_id,
                company_name,
                count(*) as job_count
            FROM job_postings
            WHERE cast(posted_at as date) >= :seven_days_ago
              AND domain IS NOT NULL
              AND company_id IS NOT NULL
              AND company_name NOT ILIKE '%confidential%'
            GROUP BY domain, company_id, company_name
        ),
        RankedCompanies AS (
            SELECT 
                domain,
                company_id,
                company_name,
                job_count,
                ROW_NUMBER() OVER(PARTITION BY domain ORDER BY job_count DESC) as rn
            FROM CompanyCounts
        )
        SELECT domain, company_id, company_name, job_count
        FROM RankedCompanies
        WHERE rn = 1
    """)
    
    res_top = await db.execute(top_company_sql, {"seven_days_ago": seven_days_ago})
    for tr in res_top:
        if tr.domain in domains_data:
            domains_data[tr.domain]["top_company"] = {
                "company_id": str(tr.company_id),
                "company_name": tr.company_name,
                "job_count": tr.job_count
            }

    # If a specific domain was requested but has no data in the last 14 days,
    # return an empty list or a zeroed-out response so it matches schema.
    if domain and domain not in domains_data:
        return []
        
    # ── 3. Sort Results ──────────────────────────
    # Sort primarily by activity
    return sorted(list(domains_data.values()), key=lambda x: x["today_count"] + x["yesterday_count"], reverse=True)
