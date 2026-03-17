"""
Insights Engine – computes BD intelligence signals daily.
"""

from datetime import datetime, timedelta, timezone, date
from typing import Dict, Any

from sqlalchemy import select, func, text, cast, Date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

from app.models.company import Company
from app.models.job_posting import JobPosting
from app.models.daily_insight import DailyInsight
from app.core.logging import get_logger

logger = get_logger(__name__)


async def generate_daily_insights(db: AsyncSession) -> Dict[str, int]:
    """
    Computes BD intelligence signals and stores the results in daily_insights table.
    """
    logger.info("Starting daily insights generation...")
    today = datetime.now(timezone.utc).date()
    now_utc = datetime.now(timezone.utc)
    
    # ── 1. Spiking Companies ───────────
    spiking_companies = []
    stmt_spiking = select(
        Company.id, Company.company_name, Company.total_postings_7d, Company.avg_postings_30d
    ).where(
        Company.total_postings_7d > Company.avg_postings_30d * 3,
        Company.avg_postings_30d > 0
    )
    res_spiking = await db.execute(stmt_spiking)
    for row in res_spiking:
        comp_id, comp_name, tot_7d, avg_30d = row
        pct_increase = ((float(tot_7d) - float(avg_30d)) / float(avg_30d)) * 100 if avg_30d else 0
        spiking_companies.append({
            "company_id": str(comp_id),
            "company_name": comp_name,
            "velocity_score": int(tot_7d),
            "pct_increase": round(pct_increase, 2)
        })

    # ── 2. Struggling Companies ────────
    struggling_companies = []
    fourteen_days_ago = now_utc - timedelta(days=14)
    stmt_struggling = select(
        JobPosting.company_id,
        JobPosting.company_name,
        JobPosting.title_normalized,
        func.count(JobPosting.id).label("repeat_count")
    ).where(
        JobPosting.posted_at >= fourteen_days_ago,
        JobPosting.company_id.is_not(None),
        JobPosting.title_normalized.is_not(None)
    ).group_by(
        JobPosting.company_id, JobPosting.company_name, JobPosting.title_normalized
    ).having(
        func.count(JobPosting.id) >= 2
    )
    res_struggling = await db.execute(stmt_struggling)
    
    struggling_dict: Dict[str, Any] = {}
    for row in res_struggling:
        comp_id, comp_name, title_norm, repeat_count = row
        comp_id_str = str(comp_id)
        if comp_id_str not in struggling_dict:
            struggling_dict[comp_id_str] = {
                "company_name": comp_name,
                "repeated_roles": [],
                "repeat_count": 0
            }
        
        struggling_dict[comp_id_str]["repeated_roles"].append(title_norm)
        struggling_dict[comp_id_str]["repeat_count"] += repeat_count
    
    for comp_id, data in struggling_dict.items():
        struggling_companies.append({
            "company_id": comp_id,
            "company_name": data["company_name"],
            "repeated_roles": data["repeated_roles"],
            "repeat_count": data["repeat_count"]
        })

    # ── 3. New Entrants ────────────────
    new_entrants = []
    stmt_new = select(
        Company.id, Company.company_name, Company.domains_active, Company.locations
    ).where(
        cast(Company.first_seen_at, Date) == today
    )
    res_new = await db.execute(stmt_new)
    for row in res_new:
        comp_id, comp_name, domains, locations = row
        first_domain = domains[0] if domains and len(domains) > 0 else None
        location = locations[0] if locations and len(locations) > 0 else None
        new_entrants.append({
            "company_id": str(comp_id),
            "company_name": comp_name,
            "first_domain": first_domain,
            "location": location
        })


    # ── 5. Ghost Posters ───────────────
    ghost_posters = []
    stmt_ghost = select(
        Company.id, Company.company_name, Company.countries, Company.total_postings_7d
    ).where(
        func.array_length(Company.countries, 1) >= 3,
        Company.total_postings_7d >= 5
    )
    res_ghost = await db.execute(stmt_ghost)
    for row in res_ghost:
        comp_id, comp_name, countries, volume = row
        ghost_posters.append({
            "company_id": str(comp_id),
            "company_name": comp_name,
            "countries": countries,
            "posting_volume": volume
        })

    # ── 6. Salary Signals ──────────────
    salary_signals = []
    salary_sql = text("""
        WITH RoleMedians AS (
            SELECT 
                title_normalized, 
                location_city, 
                percentile_cont(0.5) WITHIN GROUP (ORDER BY salary_min) AS median_salary
            FROM job_postings
            WHERE salary_min IS NOT NULL
              AND title_normalized IS NOT NULL
              AND location_city IS NOT NULL
            GROUP BY title_normalized, location_city
        )
        SELECT 
            jp.job_id,
            jp.company_name,
            jp.title_normalized,
            jp.salary_min,
            jp.salary_max,
            jp.salary_currency,
            rm.median_salary
        FROM job_postings jp
        JOIN RoleMedians rm 
          ON jp.title_normalized = rm.title_normalized 
         AND jp.location_city = rm.location_city
        WHERE jp.salary_min > (rm.median_salary * 1.3)
          AND cast(jp.scraped_at as date) = :today
          AND rm.median_salary > 0
    """)
    res_salary_signals = await db.execute(salary_sql, {"today": today})
    for row in res_salary_signals:
        salary_signals.append({
            "job_id": row.job_id,
            "company_name": row.company_name,
            "role": row.title_normalized,
            "salary_min": float(row.salary_min) if row.salary_min is not None else None,
            "salary_max": float(row.salary_max) if row.salary_max is not None else None,
            "currency": row.salary_currency
        })

    # ── Aggregates ─────────────────────
    res_jobs = await db.execute(select(func.count(JobPosting.id)).where(cast(JobPosting.scraped_at, Date) == today))
    total_jobs_today = res_jobs.scalar() or 0
    
    res_comps = await db.execute(
        select(func.count(func.distinct(JobPosting.company_id))).where(cast(JobPosting.scraped_at, Date) == today)
    )
    total_companies_active_today = res_comps.scalar() or 0

    # ── UPSERT into daily_insights ─────
    insight_data = {
        "insight_date": today,
        "companies_spiking": spiking_companies,
        "companies_struggling": struggling_companies,
        "new_entrants": new_entrants,
        "ghost_posters": ghost_posters,
        "salary_signals": salary_signals,
        "total_jobs_today": total_jobs_today,
        "total_companies_active_today": total_companies_active_today,
        "computed_at": now_utc
    }
    
    stmt_insert_insight = insert(DailyInsight).values(**insight_data)
    stmt_upsert_insight = stmt_insert_insight.on_conflict_do_update(
        index_elements=["insight_date"],
        set_={
            "companies_spiking": stmt_insert_insight.excluded.companies_spiking,
            "companies_struggling": stmt_insert_insight.excluded.companies_struggling,
            "new_entrants": stmt_insert_insight.excluded.new_entrants,
            "ghost_posters": stmt_insert_insight.excluded.ghost_posters,
            "salary_signals": stmt_insert_insight.excluded.salary_signals,
            "total_jobs_today": stmt_insert_insight.excluded.total_jobs_today,
            "total_companies_active_today": stmt_insert_insight.excluded.total_companies_active_today,
            "computed_at": stmt_insert_insight.excluded.computed_at
        }
    )
    await db.execute(stmt_upsert_insight)
    await db.commit()

    logger.info("Daily insights generation complete.")
    
    return {
        "spiking_companies_count": len(spiking_companies),
        "struggling_companies_count": len(struggling_companies),
        "new_entrants_count": len(new_entrants),
        "ghost_posters_count": len(ghost_posters),
        "salary_signals_count": len(salary_signals)
    }
