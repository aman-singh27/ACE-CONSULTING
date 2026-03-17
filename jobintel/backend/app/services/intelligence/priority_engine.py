"""
Priority Engine – computes dynamic BD Priority Scores and rankings.
"""

from datetime import datetime, timedelta, timezone, date
from typing import List, Dict, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Company
from app.models.company_contact import CompanyContact
from app.models.daily_insight import DailyInsight
from app.core.logging import get_logger

logger = get_logger(__name__)


async def get_bd_priority_list(db: AsyncSession, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Computes and returns the top dynamic BD Priority Score rankings.
    """
    now_utc = datetime.now(timezone.utc)
    today = now_utc.date()
    
    # ── 1. Fetch Today's Insights ───────────
    stmt_insight = select(DailyInsight).where(DailyInsight.insight_date == today)
    res_insight = await db.execute(stmt_insight)
    insight = res_insight.scalar_one_or_none()
    
    spiking_ids = set()
    struggling_map = {}
    new_entrant_ids = set()
    salary_signal_ids = set()
    
    if insight:
        if insight.companies_spiking:
            spiking_ids = {c["company_id"] for c in insight.companies_spiking}
        if insight.companies_struggling:
            struggling_map = {c["company_id"]: c["repeat_count"] for c in insight.companies_struggling}
        if insight.new_entrants:
            new_entrant_ids = {c["company_id"] for c in insight.new_entrants}
        if insight.salary_signals:
            # Join with companies on company_name to find ID if needed, 
            # Or if company_id is present in salary_signals
            pass # We'll check company name for salary signals next
            
    # ── 2. Fetch Active Companies ───────────
    # For performance, only look at companies active within last 7 days 
    # OR those present in our insight lists
    seven_days_ago = now_utc - timedelta(days=7)
    
    stmt_comps = select(Company).where(
        (Company.last_active_at >= seven_days_ago) |
        (Company.id.in_([uuid for uuid in list(spiking_ids) + list(struggling_map.keys()) + list(new_entrant_ids)]))
    ).where(
        ~Company.company_name.ilike("%confidential%"),
        ~Company.company_name.ilike("%hidden%")
    )
    
    res_comps = await db.execute(stmt_comps)
    companies = res_comps.scalars().all()
    
    # Pre-process salary signals by name
    salary_signal_names = set()
    if insight and insight.salary_signals:
        salary_signal_names = {s["company_name"] for s in insight.salary_signals}
    
    # ── 2.5. Fetch Companies with Contacts ──────────
    contact_query = select(CompanyContact.company_id).distinct()
    contact_res = await db.execute(contact_query)
    companies_with_contacts = {str(r[0]) for r in contact_res.all() if r[0]}
    
    results = []
    
    # ── 3. Score Companies ──────────────────
    for comp in companies:
        score = 0
        tags = []
        comp_id_str = str(comp.id)
        
        # Hiring Spike (40%)
        if comp_id_str in spiking_ids:
            score += 40
            tags.append("spiking")
            
        # Repeat Roles (25%)
        if comp_id_str in struggling_map:
            rep_count = struggling_map[comp_id_str]
            score += min(rep_count * 5, 25)
            tags.append("struggling")
            
        # Recency (20%)
        if comp.last_active_at:
            hours_since = (now_utc - comp.last_active_at.replace(tzinfo=timezone.utc)).total_seconds() / 3600
            if hours_since <= 24:
                score += 20
            elif hours_since <= 72:
                score += 10
                
        # Salary Signals (15%)
        if comp.company_name in salary_signal_names:
            score += 15
            tags.append("salary_signal")
            
        # New Entrant 
        if comp_id_str in new_entrant_ids:
            tags.append("new_entrant")
            
        # Contact Available (20%)
        if comp_id_str in companies_with_contacts:
            score += 20
            tags.append("contact_available")
            
        if score > 0:
            domain = comp.domains_active[0] if comp.domains_active and len(comp.domains_active) > 0 else "unknown"
            
            # Map values exactly to required schemas
            results.append({
                "id": comp.id,                   # For frontend React keys / schemas
                "company_id": comp_id_str,       # For prompt
                "company_name": comp.company_name,
                "domain": domain,                # For prompt
                "domains_active": comp.domains_active, # For PriorityListCompany
                "jobs_today": comp.total_postings_7d, # For prompt (approx jobs recently)
                "total_postings_7d": comp.total_postings_7d, # For PriorityListCompany
                "bd_score": score,               # For prompt
                "bd_priority_score": score,      # For PriorityListCompany
                "tags": tags,                    # For prompt
                "bd_tags": tags                  # For PriorityListCompany
            })
            
    # ── 4. Sort and Limit ───────────────────
    results.sort(key=lambda x: x["bd_score"], reverse=True)
    top_results = results[:limit]
    
    # Apply rank
    for i, res in enumerate(top_results):
        res["rank"] = i + 1
        
    return top_results
