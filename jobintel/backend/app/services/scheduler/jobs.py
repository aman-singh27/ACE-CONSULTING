"""
Automated periodic jobs for the scheduler.
"""

from datetime import datetime, timezone
from sqlalchemy import select
from app.db.session import async_session_factory
from app.models.actor_config import ActorConfig
from app.models.actor_run import ActorRun
from app.services.actors.actor_service import (
    reconcile_running_actor_runs,
    trigger_actor,
)
from app.services.intelligence.insights_engine import generate_daily_insights
from app.services.intelligence.company_metrics import calculate_company_metrics
from app.core.logging import get_logger

logger = get_logger(__name__)


async def check_due_actors():
    """
    Find active actors where next_run_at <= now() and trigger them if not already running.
    Then bump their next_run_at according to frequency_days.
    """
    logger.info("Scheduler checking actors...")
    now = datetime.now(timezone.utc)
    
    async with async_session_factory() as db:
        # 0. Reconcile stale/running runs first so actors don't get stuck forever.
        try:
            await reconcile_running_actor_runs(db)
        except Exception as e:
            logger.error(f"Failed to reconcile running actor runs: {e}")
            await db.rollback()

        # 1. Find due actors
        # Actors that are active and either have passed their next run time, 
        # or have NEVER run (next_run_at is None)
        stmt = select(ActorConfig).where(
            ActorConfig.is_active == True,
            (ActorConfig.next_run_at <= now) | (ActorConfig.next_run_at.is_(None))
        )
        res = await db.execute(stmt)
        due_actors = res.scalars().all()
        
        for actor in due_actors:
            # 2. Safety check: ensure actor is not already running.
            running_stmt = select(ActorRun).where(
                ActorRun.actor_config_id == actor.id,
                ActorRun.status == "running"
            )
            running_res = await db.execute(running_stmt)
            if running_res.scalars().first() is not None:
                logger.info(f"Actor skipped (already running): {actor.actor_name}")
                continue

            # 3. Trigger Actor
            try:
                logger.info(f"Actor due: {actor.actor_name}")
                logger.info("Triggering actor run...")
                
                # trigger_actor creates the ActorRun record and updates last_run_at
                await trigger_actor(db, actor.id)
                
                # 4. Bump next_run_at
                # Add frequency_days to either now, or ideally from the previous next_run_at if it wasn't wildly behind
                from datetime import timedelta
                actor.next_run_at = now + timedelta(days=actor.frequency_days)
                
                await db.commit()
            except Exception as e:
                logger.error(f"Failed to trigger due actor {actor.actor_name}: {e}")
                await db.rollback()

async def run_daily_insights():
    """
    Run the daily BD insights engine.
    """
    logger.info("Scheduler running daily insights...")
    async with async_session_factory() as db:
        try:
            summary = await generate_daily_insights(db)
            logger.info(f"Daily insights completed. Summary: {summary}")
        except Exception as e:
            logger.error(f"Failed to generate daily insights: {e}")

async def run_company_metrics():
    """
    Run the daily BD company metrics calculator.
    """
    logger.info("Scheduler running company metrics recalculation...")
    async with async_session_factory() as db:
        try:
            summary = await calculate_company_metrics(db)
            logger.info(f"Company metrics completed. Summary: {summary}")
        except Exception as e:
            logger.error(f"Failed to recalculate company metrics: {e}")


async def run_hubspot_sync():
    """
    Nightly HubSpot sync job.
    Syncs all companies updated in last 24 hours.
    """
    logger.info("Scheduler: starting HubSpot sync...")
    async with async_session_factory() as db:
        try:
            from app.services.hubspot.sync_service import (
                sync_companies_to_hubspot
            )
            summary = await sync_companies_to_hubspot(db)
            logger.info(
                "Scheduler: HubSpot sync complete. Summary: %s",
                summary
            )
            # Store result in the status tracker
            from app.api.routes.hubspot import _store_sync_result
            _store_sync_result(summary)
        except Exception as e:
            logger.error(
                "Scheduler: HubSpot sync failed: %s", e
            )
            from app.api.routes.hubspot import _store_sync_result
            _store_sync_result({
                "error": str(e),
                "companies_synced": 0,
                "synced_at": datetime.now(timezone.utc).isoformat()
            })

