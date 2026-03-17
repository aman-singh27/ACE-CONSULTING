"""
Alerts Engine – compiles dynamic system-wide alerts for the dashboard.
"""

import uuid
from datetime import datetime, timedelta, timezone, date
from typing import List, Dict, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.daily_insight import DailyInsight
from app.models.actor_run import ActorRun
from app.models.actor_config import ActorConfig
from app.core.logging import get_logger

logger = get_logger(__name__)


async def get_dashboard_alerts(db: AsyncSession) -> List[Dict[str, Any]]:
    """
    Compiles alerts from daily BD insights and scraping infrastructure.
    """
    alerts = []
    now_utc = datetime.now(timezone.utc)
    today = now_utc.date()
    
    # ── 1. BD Insights Alerts ─────────────────
    stmt_insight = select(DailyInsight).where(DailyInsight.insight_date == today)
    res_insight = await db.execute(stmt_insight)
    insight = res_insight.scalar_one_or_none()
    
    if insight:
        # Spiking Companies
        for comp in (insight.companies_spiking or []):
            alerts.append({
                "id": uuid.uuid4(),
                "type": "spiking_company",
                "title": "Hiring Velocity Spike",
                "description": f"{comp.get('company_name')} reversed course and spiked by {comp.get('pct_increase')}%",
                "company_id": comp.get("company_id"),
                "severity": "info"
            })
            
        # Struggling Companies
        for comp in (insight.companies_struggling or []):
            roles = ", ".join(comp.get('repeated_roles', [])[:3])
            more = "..." if len(comp.get('repeated_roles', [])) > 3 else ""
            alerts.append({
                "id": uuid.uuid4(),
                "type": "struggling_company",
                "title": "Struggling to Fill",
                "description": f"{comp.get('company_name')} posted the same roles repeatedly ({roles}{more}).",
                "company_id": comp.get("company_id"),
                "severity": "warning"
            })
            
        # New Entrants
        for comp in (insight.new_entrants or []):
            alerts.append({
                "id": uuid.uuid4(),
                "type": "new_entrant",
                "title": "New Entrant Detected",
                "description": f"{comp.get('company_name')} appeared for the first time on our active sources.",
                "company_id": comp.get("company_id"),
                "severity": "info"
            })

    # ── 2. Infra Alerts - Failed Runs ─────────
    forty_eight_hours_ago = now_utc - timedelta(hours=48)
    stmt_failures = select(ActorRun, ActorConfig.actor_name).outerjoin(
        ActorConfig, ActorRun.actor_config_id == ActorConfig.id
    ).where(
        ActorRun.status == "failed",
        ActorRun.started_at >= forty_eight_hours_ago
    )
    res_failures = await db.execute(stmt_failures)
    
    for run, actor_name in res_failures:
        alerts.append({
            "id": uuid.uuid4(),
            "type": "actor_failure",
            "title": "Actor Run Failed",
            "description": f"Actor '{actor_name or 'Unknown'}' run failed during execution.",
            "company_id": None,
            "severity": "critical"
        })

    # ── 3. Infra Alerts - Budget Limits ───────
    stmt_budget = select(ActorConfig).where(
        ActorConfig.is_active == True,
        ActorConfig.monthly_budget_usd > 0,
        ActorConfig.spend_mtd_usd > 0
    )
    res_budget = await db.execute(stmt_budget)
    
    for config in res_budget.scalars().all():
        budget_pct = (config.spend_mtd_usd / config.monthly_budget_usd) * 100
        if budget_pct >= config.alert_threshold_pct:
            level = "critical" if budget_pct >= 100 else "warning"
            title = "Budget Exceeded!" if level == "critical" else "Approaching Budget"
            alerts.append({
                "id": uuid.uuid4(),
                "type": "budget_warning",
                "title": title,
                "description": f"{config.actor_name} is at {budget_pct:.1f}% of its ${int(config.monthly_budget_usd)} monthly limit.",
                "company_id": None,
                "severity": level
            })

    # Sort alerts by severity (critical first) then chronological (best effort via type grouping here)
    severity_rank = {"critical": 0, "warning": 1, "info": 2}
    alerts.sort(key=lambda x: severity_rank.get(x["severity"], 3))
    
    return alerts
