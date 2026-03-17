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
