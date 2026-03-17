"""
Apify webhook endpoint.
"""

import asyncio

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.config import settings
from app.core.logging import get_logger
from app.db.session import async_session_factory
from app.schemas.apify_webhook import ApifyWebhookPayload
from app.services.ingestion.actor_run_service import create_actor_run
from app.services.ingestion.ingestion_pipeline import process_dataset

router = APIRouter(tags=["webhook"])
logger = get_logger(__name__)


async def _run_pipeline_in_background(
    actor_config,
    actor_run,
    dataset_id: str,
) -> None:
    """Run the ingestion pipeline in a background task with its own DB session."""
    async with async_session_factory() as db:
        try:
            await process_dataset(
                db,
                actor_config=actor_config,
                actor_run=actor_run,
                dataset_id=dataset_id,
            )
        except Exception as exc:
            logger.error("Background pipeline error: %s", exc)


@router.post("/apify")
async def receive_apify_webhook(
    payload: ApifyWebhookPayload,
    x_webhook_secret: str = Header(..., alias="X-Webhook-Secret"),
    db: AsyncSession = Depends(get_db),
):
    """Receive an Apify actor-run webhook.

    1. Validate webhook secret
    2. Parse payload
    3. Look up actor_config
    4. Create actor_runs record
    5. Kick off ingestion pipeline in background
    6. Return accepted immediately
    """

    # ── Validate secret ──────────────────────────────────────
    if x_webhook_secret != settings.WEBHOOK_SECRET:
        logger.warning("Webhook secret mismatch – rejecting request")
        raise HTTPException(status_code=401, detail="Invalid webhook secret")

    logger.debug("Received full webhook payload: %s", payload.model_dump_json())

    logger.info(
        "Webhook received: event_type=%s, actor_id=%s, apify_run_id=%s, dataset_id=%s",
        payload.eventType,
        payload.eventData.actorId,
        payload.eventData.actorRunId,
        payload.resource.defaultDatasetId,
    )

    # ── Create actor run ─────────────────────────────────────
    run_info = await create_actor_run(
        db,
        actor_id=payload.eventData.actorId,
        apify_run_id=payload.eventData.actorRunId,
        dataset_id=payload.resource.defaultDatasetId,
    )

    # ── Kick off pipeline in background ──────────────────────
    asyncio.create_task(
        _run_pipeline_in_background(
            actor_config=run_info["actor_config"],
            actor_run=run_info["actor_run"],
            dataset_id=payload.resource.defaultDatasetId,
        )
    )
    logger.info("Pipeline task launched in background – returning immediately")

    return {
        "status": "accepted",
        "message": "Webhook received",
        "run_id": run_info["run_id"],
        "dataset_id": run_info["dataset_id"],
    }
