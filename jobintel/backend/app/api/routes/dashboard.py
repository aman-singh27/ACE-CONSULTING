"""
Dashboard Summary API endpoints.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.actor_config import ActorConfig
from app.models.company import Company
from app.models.job_posting import JobPosting
from app.models.daily_insight import DailyInsight
from app.schemas.api import DashboardSummary, DashboardAlert
from app.services.intelligence.alerts_engine import get_dashboard_alerts

router = APIRouter(tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
async def get_dashboard_summary(db: AsyncSession = Depends(get_db)):
    """Compute aggregate statistics for the main dashboard view."""
    
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    
    # ── 1. Jobs Scraped Today ────────────────────────────────
    jobs_stmt = select(func.count(JobPosting.id)).where(JobPosting.scraped_at >= today)
    jobs_res = await db.execute(jobs_stmt)
    jobs_scraped_today = jobs_res.scalar() or 0
    
    # ── 2. New Companies Today ───────────────────────────────
    comp_stmt = select(func.count(Company.id)).where(Company.first_seen_at >= today)
    comp_res = await db.execute(comp_stmt)
    new_companies_today = comp_res.scalar() or 0
    
    # ── 3. Active Actors ─────────────────────────────────────
    actor_stmt = select(func.count(ActorConfig.id)).where(ActorConfig.is_active == True)
    actor_res = await db.execute(actor_stmt)
    active_actors = actor_res.scalar() or 0
    
    # ── 4. Total BD Alerts ───────────────────────────────────
    insight_stmt = select(DailyInsight).where(DailyInsight.insight_date == today.date())
    insight_res = await db.execute(insight_stmt)
    insight = insight_res.scalar_one_or_none()
    
    total_bd_alerts = 0
    if insight:
        total_bd_alerts += len(insight.companies_spiking or [])
        total_bd_alerts += len(insight.companies_struggling or [])
        total_bd_alerts += len(insight.new_entrants or [])
        total_bd_alerts += len(insight.domain_surges or [])
        total_bd_alerts += len(insight.ghost_posters or [])
        total_bd_alerts += len(insight.salary_signals or [])
    
    return DashboardSummary(
        jobs_scraped_today=jobs_scraped_today,
        new_companies_today=new_companies_today,
        active_actors=active_actors,
        total_bd_alerts=total_bd_alerts
    )


@router.get("/alerts", response_model=list[DashboardAlert])
async def get_alerts_list(db: AsyncSession = Depends(get_db)):
    """Fetch aggregated system alerts across insights, actor health, and budgets."""
    
    alerts = await get_dashboard_alerts(db)
    return alerts
