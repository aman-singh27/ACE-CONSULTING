"""
Business logic for managing and triggering Apify actors locally.
"""

import asyncio
from datetime import datetime, timezone
from datetime import timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import get_logger
from app.db.session import async_session_factory
from app.models.actor_config import ActorConfig
from app.models.actor_run import ActorRun
from app.services.actors.apify_runner import (
    get_actor_run,
    run_actor,
    wait_for_actor_run_finish,
)
from app.services.ingestion.ingestion_pipeline import process_dataset

logger = get_logger(__name__)
TERMINAL_RUN_STATUSES = {"SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT", "TIMED_OUT"}


def _validate_actor_input(actor_id: str, actor_input: dict) -> None:
    """Basic guardrails for known actor input contracts."""
    actor_id_lc = (actor_id or "").lower()

    # cheap_scraper/linkedin-job-scraper expects search seeds.
    if "linkedin-job-scraper" in actor_id_lc:
        has_keyword = bool(actor_input.get("keyword") or actor_input.get("keywords"))
        has_start_urls = bool(actor_input.get("startUrls") or actor_input.get("start_urls"))
        if not (has_keyword or has_start_urls):
            raise ValueError(
                "LinkedIn actor input must include either `keyword` (or `keywords`) "
                "or `startUrls`."
            )


async def _process_run_without_webhook(
    actor_config_id: UUID,
    apify_run_id: str,
) -> None:
    """
    Fallback path when WEBHOOK_URL is not configured.
    Waits for Apify run completion and then runs ingestion pipeline.
    """
    try:
        run_payload = await wait_for_actor_run_finish(apify_run_id, wait_secs=3600)
        if not run_payload:
            raise RuntimeError(f"Apify run {apify_run_id} did not return completion payload")

        run_status = (run_payload.get("status") or "").upper()
        dataset_id = run_payload.get("defaultDatasetId")

        async with async_session_factory() as bg_db:
            config_res = await bg_db.execute(
                select(ActorConfig).where(ActorConfig.id == actor_config_id)
            )
            actor_config = config_res.scalar_one_or_none()

            run_res = await bg_db.execute(
                select(ActorRun).where(ActorRun.apify_run_id == apify_run_id)
            )
            actor_run = run_res.scalar_one_or_none()

            if not actor_run:
                logger.error(
                    "Fallback ingestion could not find ActorRun for apify_run_id=%s",
                    apify_run_id,
                )
                return

            if run_status != "SUCCEEDED":
                actor_run.status = "failed"
                actor_run.completed_at = datetime.now(timezone.utc)
                actor_run.error_log = (
                    f"Apify run finished with status {run_status or 'UNKNOWN'}"
                )
                bg_db.add(actor_run)
                await bg_db.commit()
                logger.warning(
                    "Apify run %s finished with non-success status %s",
                    apify_run_id,
                    run_status or "UNKNOWN",
                )
                return

            if not dataset_id:
                actor_run.status = "failed"
                actor_run.completed_at = datetime.now(timezone.utc)
                actor_run.error_log = "Apify run completed without defaultDatasetId"
                bg_db.add(actor_run)
                await bg_db.commit()
                logger.error(
                    "Apify run %s completed but had no defaultDatasetId",
                    apify_run_id,
                )
                return

            await process_dataset(
                bg_db,
                actor_config=actor_config,
                actor_run=actor_run,
                dataset_id=dataset_id,
            )
            logger.info(
                "Fallback ingestion completed for run %s (dataset=%s)",
                apify_run_id,
                dataset_id,
            )

    except Exception as exc:
        logger.exception(
            "Fallback ingestion failed for run %s: %s",
            apify_run_id,
            exc,
        )


async def reconcile_running_actor_runs(db: AsyncSession, max_runs: int = 25) -> dict:
    """
    Reconcile locally-running ActorRun rows against Apify state.
    Useful when webhook delivery is unavailable or intermittent.
    """
    result = await db.execute(
        select(ActorRun)
        .where(
            ActorRun.status == "running",
            ActorRun.apify_run_id.is_not(None),
        )
        .order_by(ActorRun.started_at.asc().nulls_last())
        .limit(max_runs)
    )
    running_runs = result.scalars().all()

    summary = {
        "checked": len(running_runs),
        "ingested": 0,
        "failed_marked": 0,
        "still_running": 0,
    }

    for actor_run in running_runs:
        if not actor_run.apify_run_id:
            continue

        run_payload = await get_actor_run(actor_run.apify_run_id)
        if not run_payload:
            summary["still_running"] += 1
            continue

        run_status = (run_payload.get("status") or "").upper()
        if run_status not in TERMINAL_RUN_STATUSES:
            summary["still_running"] += 1
            continue

        config = None
        if actor_run.actor_config_id:
            config_res = await db.execute(
                select(ActorConfig).where(ActorConfig.id == actor_run.actor_config_id)
            )
            config = config_res.scalar_one_or_none()

        if run_status == "SUCCEEDED":
            dataset_id = run_payload.get("defaultDatasetId")
            if dataset_id:
                await process_dataset(
                    db,
                    actor_config=config,
                    actor_run=actor_run,
                    dataset_id=dataset_id,
                )
                summary["ingested"] += 1
                continue

            actor_run.status = "failed"
            actor_run.completed_at = datetime.now(timezone.utc)
            actor_run.error_log = "Apify run succeeded but defaultDatasetId was missing"
            db.add(actor_run)
            await db.commit()
            summary["failed_marked"] += 1
            continue

        actor_run.status = "failed"
        actor_run.completed_at = datetime.now(timezone.utc)
        actor_run.error_log = f"Apify run finished with status {run_status}"
        db.add(actor_run)
        await db.commit()
        summary["failed_marked"] += 1

    if summary["checked"] > 0:
        logger.info("Reconciled running actor runs: %s", summary)
    return summary


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
    _validate_actor_input(config.actor_id, actor_input)
    
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
    config.last_run_at = now
    config.next_run_at = now + timedelta(days=config.frequency_days)
    
    await db.commit()

    # 6. Fallback ingestion when webhook delivery is not configured.
    if not settings.WEBHOOK_URL:
        logger.warning(
            "WEBHOOK_URL is not configured. Using polling fallback for apify_run_id=%s",
            apify_run_id,
        )
        asyncio.create_task(_process_run_without_webhook(config.id, apify_run_id))
    
    return apify_run_id
