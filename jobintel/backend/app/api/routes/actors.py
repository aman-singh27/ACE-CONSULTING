"""
Actor configuration and triggering API endpoints.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, ConfigDict, field_validator
from datetime import datetime

from app.api.deps import get_db
from app.models.actor_config import ActorConfig
from app.services.actors.actor_service import trigger_actor

router = APIRouter(tags=["actors"])


class ActorConfigCreate(BaseModel):
    actor_id: str
    actor_name: str
    platform: str
    domain: str
    frequency_days: int = 1
    apify_input_template: dict = {}
    normalizer_key: str
    keywords: list[str] = []
    locations: list[str] = []
    monthly_budget_usd: Optional[float] = None

    @field_validator('apify_input_template')
    @classmethod
    def check_normalizer_not_in_template(cls, v: dict):
        if 'normalizer_key' in v:
            raise ValueError("normalizer_key must be at the top level of ActorConfigCreate, not inside apify_input_template")
        return v

class ActorConfigUpdate(BaseModel):
    frequency_days: int | None = None
    is_active: bool | None = None
    monthly_budget_usd: float | None = None
    apify_input_template: dict | None = None

class ActorConfigResponse(BaseModel):
    id: UUID
    actor_id: str
    actor_name: str | None = None
    platform: str | None = None
    domain: str | None = None
    frequency_days: int
    is_active: bool
    monthly_budget_usd: float | None = None
    apify_input_template: dict | None = None
    normalizer_key: str | None = None
    keywords: list[str] | None = None
    locations: list[str] | None = None
    last_run_at: datetime | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class TriggerResponse(BaseModel):
    status: str
    run_id: str


@router.get("", response_model=List[ActorConfigResponse])
async def list_actors(db: AsyncSession = Depends(get_db)):
    """List all available actor configurations."""
    stmt = select(ActorConfig).order_by(ActorConfig.created_at.desc())
    res = await db.execute(stmt)
    actors = res.scalars().all()
    return actors


@router.post("", response_model=ActorConfigResponse, status_code=201)
async def create_actor(
    payload: ActorConfigCreate, 
    db: AsyncSession = Depends(get_db)
):
    """Register a new Apify Actor configuration."""
    new_actor = ActorConfig(
        actor_id=payload.actor_id,
        actor_name=payload.actor_name,
        platform=payload.platform,
        domain=payload.domain,
        frequency_days=payload.frequency_days,
        apify_input_template=payload.apify_input_template,
        normalizer_key=payload.normalizer_key,
        keywords=payload.keywords or [],
        locations=payload.locations or [],
        monthly_budget_usd=payload.monthly_budget_usd,
    )
    db.add(new_actor)
    await db.commit()
    await db.refresh(new_actor)
    return new_actor


@router.patch("/{id}", response_model=ActorConfigResponse)
async def update_actor(
    id: UUID, 
    payload: ActorConfigUpdate, 
    db: AsyncSession = Depends(get_db)
):
    """Update settings for an Existing Actor."""
    stmt = select(ActorConfig).where(ActorConfig.id == id)
    res = await db.execute(stmt)
    actor = res.scalar_one_or_none()
    
    if not actor:
        raise HTTPException(status_code=404, detail="Actor not found")

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(actor, key, value)

    await db.commit()
    await db.refresh(actor)
    return actor


@router.delete("/{id}", status_code=204)
async def delete_actor(id: UUID, db: AsyncSession = Depends(get_db)):
    """Soft delete an actor (sets is_active=False)."""
    stmt = select(ActorConfig).where(ActorConfig.id == id)
    res = await db.execute(stmt)
    actor = res.scalar_one_or_none()
    
    if not actor:
        raise HTTPException(status_code=404, detail="Actor not found")
        
    actor.is_active = False
    await db.commit()


@router.post("/{id}/trigger", response_model=TriggerResponse)
async def trigger_actor_manual(id: UUID, db: AsyncSession = Depends(get_db)):
    """Manually trigger an actor run on Apify."""
    try:
        run_id = await trigger_actor(db, id)
        return TriggerResponse(status="triggered", run_id=str(run_id))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
