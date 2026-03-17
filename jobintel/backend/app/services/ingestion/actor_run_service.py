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

    # Look up the existing actor_runs record created when we triggered the actor
    result = await db.execute(
        select(ActorRun)
        .where(ActorRun.apify_run_id == apify_run_id)
    )
    run = result.scalar_one_or_none()
    
    if not run:
        logger.warning(f"No existing ActorRun found for apify_run_id={apify_run_id}")
        # Could create one here as fallback if needed, but since our system is the
        # only trigger, this shouldn't happen unless we lose the db.
        raise ValueError(f"ActorRun not found for Apify run {apify_run_id}")

    # Find linked actor config
    actor_config = None
    actor_config_id = run.actor_config_id
    if actor_config_id:
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
