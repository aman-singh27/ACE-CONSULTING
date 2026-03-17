"""
Business logic for managing and triggering Apify actors locally.
"""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.actor_config import ActorConfig
from app.models.actor_run import ActorRun
from app.services.actors.apify_runner import run_actor


async def trigger_actor(db: AsyncSession, actor_config_id: UUID) -> str:
    """
    Look up an ActorConfig by ID, prepare its input templated data, and call Apify.
    Create a running ActorRun record to track it.
    """
    
    # 1. Fetch Actor Config
    stmt = select(ActorConfig).where(ActorConfig.id == actor_config_id)
    res = await db.execute(stmt)
    config = res.scalar_one_or_none()
    
    if not config:
        raise ValueError(f"ActorConfig {actor_config_id} not found")
        
    if not config.is_active:
        raise ValueError(f"ActorConfig {actor_config_id} is inactive")
        
    # 2. Prepare Apify Input
    actor_input = config.apify_input_template or {}
    
    # 3. Trigger run on Apify
    apify_run_id = await run_actor(config.actor_id, actor_input)
    
    # 4. Create ActorRun tracking record
    now = datetime.now(timezone.utc)
    
    new_run = ActorRun(
        apify_run_id=apify_run_id,
        actor_config_id=config.id,
        status="running",
        started_at=now,
        run_date=now.date(),
    )
    
    db.add(new_run)
    
    # 5. Update config last_run_at and next_run_at
    from datetime import timedelta
    config.last_run_at = now
    config.next_run_at = now + timedelta(days=config.frequency_days)
    
    await db.commit()
    
    return apify_run_id
