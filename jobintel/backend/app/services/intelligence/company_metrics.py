"""
Company Metrics Engine – recalculates dynamic company aggregates daily.
"""

from datetime import datetime, timedelta, timezone, date
from typing import Dict, Any

from sqlalchemy import select, update, func, Date, cast, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

from app.models.company import Company
from app.models.job_posting import JobPosting
from app.models.company_contact import CompanyContact
from app.models.daily_insight import DailyInsight
from app.core.logging import get_logger

logger = get_logger(__name__)


async def calculate_company_metrics(db: AsyncSession) -> Dict[str, Any]:
    """
    Recalculate dynamic aggregates and BD prioritization scores for all companies 
    based on job scraping activity and today's insights.
    """
    now_utc = datetime.now(timezone.utc)
    today = now_utc.date()
    thirty_days_ago = today - timedelta(days=30)
    seven_days_ago = today - timedelta(days=7)
    
    # ── 1. Scrape DB context on job_postings ───────────────────────────
    # Determine the count of job postings per company for last 7d, 30d, and max activity.
    # Exclude duplicates and handle missing posted_at by falling back to created_at
    job_stats_query = text("""
        SELECT 
            company_id,
            COUNT(*) as total_alltime,
            COUNT(*) FILTER (WHERE cast(COALESCE(posted_at, created_at) as date) >= :seven_days_ago) as total_7d,
            COUNT(*) FILTER (WHERE cast(COALESCE(posted_at, created_at) as date) >= :thirty_days_ago) as total_30d,
            MAX(COALESCE(posted_at, created_at)) as last_active_at
        FROM job_postings
        WHERE company_id IS NOT NULL 
          AND is_duplicate = false
        GROUP BY company_id
    """)
    job_res = await db.execute(
        job_stats_query, 
        {
            "seven_days_ago": seven_days_ago, 
            "thirty_days_ago": thirty_days_ago
        }
    )
    
    company_stats = {}
    for row in job_res:
        company_stats[str(row.company_id)] = {
            "total_alltime": int(row.total_alltime or 0),
            "total_7d": int(row.total_7d or 0),
            "total_30d": int(row.total_30d or 0),
            "last_active_at": row.last_active_at
        }
        
    # ── 2. Retrieve today's BD intelligence signals ────────────────────
    insight_query = select(DailyInsight).where(DailyInsight.insight_date == today)
    insight_res = await db.execute(insight_query)
    insight = insight_res.scalar_one_or_none()
    
    # Pre-map signaling strings to sets for instant matching
    companies_spiking = set()
    companies_struggling = {} # company_id -> dict with repeat_count
    new_entrants = set()
    ghost_posters = set()
    salary_signals = set()
    
    if insight:
        companies_spiking = {c.get("company_id") for c in (insight.companies_spiking or []) if c.get("company_id")}
        
        for st in (insight.companies_struggling or []):
            if st.get("company_id"):
                companies_struggling[st.get("company_id")] = st.get("repeat_count", 0)
                
        new_entrants = {c.get("company_id") for c in (insight.new_entrants or []) if c.get("company_id")}
        ghost_posters = {c.get("company_id") for c in (insight.ghost_posters or []) if c.get("company_id")}
        salary_signals = {c.get("company_id") for c in (insight.salary_signals or []) if c.get("company_id")}

    # ── 2.5. Retrieve Companies with Contacts ────────────────────────
    # Get IDs of companies that have at least one contact
    contact_query = select(CompanyContact.company_id).distinct()
    contact_res = await db.execute(contact_query)
    companies_with_contacts = {str(r[0]) for r in contact_res.all() if r[0]}

    # ── 3. Combine variables to update Company Models ─────────────────
    # We iterate across the stats and assign BD metrics cleanly against all updated hashes.
    
    bulk_update_mappings = []
    summary = {
        "companies_updated": 0,
        "spiking_companies": 0,
        "struggling_companies": 0
    }
    
    for comp_id, stats in company_stats.items():
        # Averages & Velocity Logic
        total_alltime = stats["total_alltime"]
        total_7d = stats["total_7d"]
        total_30d = stats["total_30d"]
        avg_30d = total_30d / 30.0
        
        if avg_30d > 0:
            velocity_score = int((total_7d / avg_30d) * 100)
        else:
            velocity_score = 0
            
        # Prioritization & Tagging Logic
        tags = []
        bd_priority = 0
        
        if comp_id in companies_spiking:
            tags.append("spiking")
            bd_priority += 40
            summary["spiking_companies"] += 1
            
        if comp_id in new_entrants:
            tags.append("new_entrant")
            bd_priority += 10 # Extra bump for fresh data
            
        if comp_id in ghost_posters:
            tags.append("ghost_poster")
            
        if comp_id in salary_signals:
            tags.append("salary_signal")
            bd_priority += 15
            
        if comp_id in companies_struggling:
            tags.append("struggling")
            repeat_count = companies_struggling[comp_id]
            bd_priority += min(repeat_count * 5, 25)
            summary["struggling_companies"] += 1
            
        if comp_id in companies_with_contacts:
            tags.append("contact_available")
            bd_priority += 20
                
        # Recency bump weighting inside of Prioritization Logic
        last_active = stats["last_active_at"]
        if last_active:
            # Ensure it has timezone for comparison
            if last_active.tzinfo is None:
                last_active = last_active.replace(tzinfo=timezone.utc)
                
            time_diff = now_utc - last_active
            if time_diff.total_seconds() <= 86400: # 24h
                bd_priority += 20
            elif time_diff.total_seconds() <= 259200: # 72h
                bd_priority += 10
                
        # Limit total BD Priority Score to max 100 ceiling bounds.
        bd_priority = min(bd_priority, 100)
        
        bulk_update_mappings.append({
            "id": comp_id, # Target PK for updating
            "total_postings_alltime": total_alltime,
            "total_postings_7d": total_7d,
            "total_postings_30d": total_30d,
            "avg_postings_30d": round(avg_30d, 2),
            "hiring_velocity_score": float(velocity_score),
            "last_active_at": stats["last_active_at"],
            "bd_tags": tags,
            "bd_priority_score": bd_priority
        })
        
        summary["companies_updated"] += 1


    # ── 4. Flush Bulk DB Updates ──────────────────────────────
    if bulk_update_mappings:
        logger.info(f"Bulk updating {len(bulk_update_mappings)} company metrics...")
        
        # Batch updates in sizes of 1000 to prevent parameterized row exhaustion limits
        batch_size = 1000
        for i in range(0, len(bulk_update_mappings), batch_size):
            batch = bulk_update_mappings[i:i + batch_size]
            await db.execute(update(Company), batch)
            
        await db.commit()
    
    logger.info(f"Company metrics recalculated successfully: {summary}")
    return summary
