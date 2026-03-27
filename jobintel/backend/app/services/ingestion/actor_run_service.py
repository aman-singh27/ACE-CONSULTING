"""
Actor run service – creates and manages actor_runs records.
"""

from datetime import date, datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.actor_config import ActorConfig
from app.models.actor_run import ActorRun

logger = get_logger(__name__)


async def create_actor_run(
    db: AsyncSession,
    *,
    actor_id: str,
    apify_run_id: str,
    dataset_id: str,
) -> dict:
    """Look up the actor config and create an actor_runs record.

    Returns a dict with run_id, dataset_id, and the ORM objects
    (actor_config may be None, actor_run is always set).
    """

    # Look up an existing actor_runs record created when we triggered the actor
    result = await db.execute(
        select(ActorRun)
        .where(ActorRun.apify_run_id == apify_run_id)
    )
    run = result.scalar_one_or_none()
    
    if not run:
        logger.warning(
            "No existing ActorRun found for apify_run_id=%s. Creating fallback run record.",
            apify_run_id,
        )
        config_res = await db.execute(
            select(ActorConfig).where(ActorConfig.actor_id == actor_id)
        )
        actor_config = config_res.scalar_one_or_none()

        now = datetime.now(timezone.utc)
        run = ActorRun(
            actor_config_id=actor_config.id if actor_config else None,
            apify_run_id=apify_run_id,
            status="running",
            started_at=now,
            run_date=now.date(),
        )
        db.add(run)
        await db.flush()
    else:
        actor_config = None

    # Find linked actor config
    actor_config_id = run.actor_config_id
    if actor_config_id and actor_config is None:
        config_res = await db.execute(
            select(ActorConfig).where(ActorConfig.id == actor_config_id)
        )
        actor_config = config_res.scalar_one_or_none()
        
    if not actor_config:
        logger.warning("No actor_config found linked to run – run will be processed without config link")

    logger.info(
        "Matched existing Actor run: run_id=%s, apify_run_id=%s, dataset_id=%s",
        run.id, apify_run_id, dataset_id,
    )

    return {
        "run_id": str(run.id),
        "actor_config_id": str(actor_config_id) if actor_config_id else None,
        "dataset_id": dataset_id,
        "actor_config": actor_config,
        "actor_run": run,
    }
