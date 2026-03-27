"""
Run Monitor API endpoints.
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased
from pydantic import BaseModel, ConfigDict

from app.api.deps import get_db
from app.models.actor_config import ActorConfig
from app.models.actor_run import ActorRun
from app.schemas.api import (
    HealthResponse,
    PaginatedResponse,
    RunDetailResponse,
    RunResponse,
    RunTodayResponse,
)

router = APIRouter(tags=["runs"])


class ActorCreditSummaryResponse(BaseModel):
    actor_config_id: UUID
    actor_name: Optional[str] = None
    platform: Optional[str] = None
    actual_spend_usd: float
    run_count_mtd: int


class CreditSummaryResponse(BaseModel):
    total_actual_spend_usd: float
    total_estimated_usd: float
    run_count_mtd: int
    period_start: datetime
    period_end: datetime
    per_actor: list[ActorCreditSummaryResponse]

    model_config = ConfigDict(from_attributes=True)


@router.get("", response_model=PaginatedResponse[RunResponse])
async def list_runs(
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    status: Optional[str] = None,
    platform: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """List runs joined with actor configs."""
    
    offset = (page - 1) * limit
    
    # Base query joining runs and configs
    stmt = (
        select(
            ActorRun.id,
            ActorRun.apify_run_id,
            ActorRun.status,
            ActorRun.total_scraped,
            ActorRun.total_new,
            ActorRun.total_duplicates,
            ActorRun.total_cross_dupes,
            ActorRun.total_errors,
            ActorRun.cost_usd,
            ActorRun.started_at,
            ActorRun.completed_at,
            ActorConfig.actor_name,
            ActorConfig.platform,
            ActorConfig.domain,
        )
        .outerjoin(ActorConfig, ActorRun.actor_config_id == ActorConfig.id)
    )
    
    count_stmt = select(func.count(ActorRun.id)).outerjoin(ActorConfig, ActorRun.actor_config_id == ActorConfig.id)
    
    # Filters
    filters = []
    if status:
        filters.append(ActorRun.status == status)
    if platform:
        filters.append(ActorConfig.platform == platform)
        
    if filters:
        stmt = stmt.where(*filters)
        count_stmt = count_stmt.where(*filters)
        
    stmt = stmt.order_by(ActorRun.started_at.desc().nulls_last()).offset(offset).limit(limit)
    
    total_res = await db.execute(count_stmt)
    total = total_res.scalar_one()
    
    res = await db.execute(stmt)
    rows = res.all()
    
    items = []
    for row in rows:
        items.append(
            RunResponse(
                id=row.id,
                apify_run_id=row.apify_run_id,
                status=row.status,
                total_scraped=row.total_scraped,
                total_new=row.total_new,
                total_duplicates=row.total_duplicates,
                total_cross_dupes=row.total_cross_dupes,
                total_errors=row.total_errors,
                cost_usd=row.cost_usd,
                started_at=row.started_at,
                completed_at=row.completed_at,
                actor_name=row.actor_name,
                platform=row.platform,
                domain=row.domain,
            )
        )
        
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        limit=limit
    )


@router.get("/today", response_model=list[RunTodayResponse])
async def list_runs_today(db: AsyncSession = Depends(get_db)):
    """List only today's runs for the top status strip."""
    
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    
    stmt = (
        select(
            ActorRun.id,
            ActorRun.status,
            ActorRun.total_new,
            ActorRun.started_at,
            ActorConfig.actor_name,
            ActorConfig.platform,
        )
        .outerjoin(ActorConfig, ActorRun.actor_config_id == ActorConfig.id)
        .where(ActorRun.started_at >= today)
        .order_by(ActorRun.started_at.desc().nulls_last())
    )
    
    res = await db.execute(stmt)
    rows = res.all()
    
    items = []
    for row in rows:
        items.append(
            RunTodayResponse(
                id=row.id,
                status=row.status,
                total_new=row.total_new,
                started_at=row.started_at,
                actor_name=row.actor_name,
                platform=row.platform,
            )
        )
        
    return items


@router.get("/health", response_model=list[HealthResponse])
async def get_system_health(db: AsyncSession = Depends(get_db)):
    """Show last run and last success time for all configured actors."""
    
    stmt = (
        select(
            ActorConfig.actor_name,
            ActorConfig.platform,
            func.max(ActorRun.started_at).label("last_run"),
            func.max(
                case(
                    (ActorRun.status == "success", ActorRun.started_at),
                    else_=None
                )
            ).label("last_success")
        )
        .outerjoin(ActorRun, ActorConfig.id == ActorRun.actor_config_id)
        .group_by(ActorConfig.actor_name, ActorConfig.platform)
    )
    
    res = await db.execute(stmt)
    rows = res.all()
    
    items = []
    for row in rows:
        items.append(
            HealthResponse(
                actor_name=row.actor_name,
                platform=row.platform,
                last_run=row.last_run,
                last_success=row.last_success,
            )
        )
        
    return items


@router.get("/credit-summary", response_model=CreditSummaryResponse)
async def get_credit_summary(db: AsyncSession = Depends(get_db)):
    """Return month-to-date spend totals and per-actor breakdown in UTC."""

    now_utc = datetime.now(timezone.utc)
    period_start = now_utc.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    period_end = now_utc

    per_actor_stmt = (
        select(
            ActorRun.actor_config_id.label("actor_config_id"),
            ActorConfig.actor_name,
            ActorConfig.platform,
            func.coalesce(func.sum(func.coalesce(ActorRun.cost_usd, 0)), 0).label("actual_spend_usd"),
            func.count(ActorRun.id).label("run_count_mtd"),
        )
        .join(ActorConfig, ActorRun.actor_config_id == ActorConfig.id)
        .where(
            ActorRun.started_at >= period_start,
            ActorRun.started_at <= period_end,
        )
        .group_by(
            ActorRun.actor_config_id,
            ActorConfig.actor_name,
            ActorConfig.platform,
        )
        .order_by(ActorConfig.actor_name.asc().nulls_last(), ActorConfig.platform.asc().nulls_last())
    )

    totals_stmt = select(
        func.coalesce(func.sum(func.coalesce(ActorRun.cost_usd, 0)), 0).label("total_actual_spend_usd"),
        func.count(ActorRun.id).label("run_count_mtd"),
    ).join(ActorConfig, ActorRun.actor_config_id == ActorConfig.id).where(
        ActorRun.started_at >= period_start,
        ActorRun.started_at <= period_end,
    )

    estimated_stmt = select(
        func.coalesce(func.sum(func.coalesce(ActorConfig.spend_mtd_usd, 0)), 0).label("total_estimated_usd")
    )

    per_actor_res = await db.execute(per_actor_stmt)
    per_actor_rows = per_actor_res.all()

    totals_res = await db.execute(totals_stmt)
    totals_row = totals_res.one()

    estimated_res = await db.execute(estimated_stmt)
    estimated_row = estimated_res.one()

    per_actor = [
        ActorCreditSummaryResponse(
            actor_config_id=row.actor_config_id,
            actor_name=row.actor_name,
            platform=row.platform,
            actual_spend_usd=float(row.actual_spend_usd or 0),
            run_count_mtd=int(row.run_count_mtd or 0),
        )
        for row in per_actor_rows
    ]

    return CreditSummaryResponse(
        total_actual_spend_usd=float(totals_row.total_actual_spend_usd or 0),
        total_estimated_usd=float(estimated_row.total_estimated_usd or 0),
        run_count_mtd=int(totals_row.run_count_mtd or 0),
        period_start=period_start,
        period_end=period_end,
        per_actor=per_actor,
    )


@router.get("/{run_id}", response_model=RunDetailResponse)
async def get_run_detail(run_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get full details of a specific run."""
    
    stmt = (
        select(
            ActorRun.id,
            ActorRun.apify_run_id,
            ActorRun.status,
            ActorRun.total_scraped,
            ActorRun.total_new,
            ActorRun.total_duplicates,
            ActorRun.total_cross_dupes,
            ActorRun.total_errors,
            ActorRun.cost_usd,
            ActorRun.started_at,
            ActorRun.completed_at,
            ActorRun.error_log,
            ActorConfig.actor_name,
            ActorConfig.platform,
            ActorConfig.domain,
        )
        .outerjoin(ActorConfig, ActorRun.actor_config_id == ActorConfig.id)
        .where(ActorRun.id == run_id)
    )
    
    res = await db.execute(stmt)
    row = res.first()
    
    if not row:
        raise HTTPException(status_code=404, detail="Run not found")
        
    return RunDetailResponse(
        id=row.id,
        apify_run_id=row.apify_run_id,
        status=row.status,
        total_scraped=row.total_scraped,
        total_new=row.total_new,
        total_duplicates=row.total_duplicates,
        total_cross_dupes=row.total_cross_dupes,
        total_errors=row.total_errors,
        cost_usd=row.cost_usd,
        started_at=row.started_at,
        completed_at=row.completed_at,
        error_log=row.error_log,
        actor_name=row.actor_name,
        platform=row.platform,
        domain=row.domain,
    )
