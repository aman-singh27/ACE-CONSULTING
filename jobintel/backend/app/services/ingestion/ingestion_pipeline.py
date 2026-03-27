"""
Ingestion pipeline – orchestrates fetching a dataset and processing its records.
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.actor_config import ActorConfig
from app.models.actor_run import ActorRun
from app.services.ingestion.apify_client import fetch_dataset_items
from app.services.ingestion.record_processor import process_record
from app.services.intelligence.company_metrics import calculate_company_metrics
from app.services.normalizers.registry import get_normalizer

logger = get_logger(__name__)


async def process_dataset(
    db: AsyncSession,
    actor_config: Optional[ActorConfig],
    actor_run: ActorRun,
    dataset_id: str,
) -> None:
    """Fetch an Apify dataset and pass each item through the ingestion pipeline.

    Updates ``actor_run`` stats (total_scraped, total_errors, status,
    completed_at) and commits the transaction.
    """
    total_scraped = 0
    total_errors = 0

    # ── Resolve normalizer ───────────────────────────────────
    normalizer_key = actor_config.normalizer_key if actor_config else None
    normalizer = get_normalizer(normalizer_key)
    actor_id = actor_config.actor_id if actor_config else "unknown"
    domain = actor_config.domain if actor_config else None

    if normalizer:
        logger.info("Using normalizer: %s", normalizer_key)
    else:
        logger.warning("No normalizer resolved – records will be logged raw")

    try:
        # ── Fetch dataset ────────────────────────────────────
        items = await fetch_dataset_items(dataset_id)
        
        if items:
            logger.debug("First item from dataset %s for debugging: %s", dataset_id, items[0])

        # ── Iterate and Write Records ────────────────────────
        # Some callers perform SELECTs on this session before invoking the
        # pipeline, which may leave an open transaction. Reset to a clean state
        # so per-record `db.begin()` blocks work reliably.
        if db.in_transaction():
            await db.commit()

        for idx, item in enumerate(items, start=1):
            try:
                # Process each record in its own transaction block
                async with db.begin():
                    await process_record(
                        db,
                        item,
                        idx,
                        actor_run,
                        normalizer=normalizer,
                        actor_id=actor_id,
                        domain=domain,
                    )
                total_scraped += 1
            except Exception as exc:
                total_errors += 1
                logger.exception("Error processing record %d from dataset %s. Item data: %s", idx, dataset_id, item)

        # ── Mark success ─────────────────────────────────────
        if total_scraped == 0 and total_errors > 0:
            actor_run.status = "failed"
            actor_run.error_log = (
                f"All records failed processing (errors={total_errors}, dataset={dataset_id})"
            )
            logger.warning(
                "Dataset %s produced no successful records (errors=%d)",
                dataset_id,
                total_errors,
            )
        else:
            actor_run.status = "success"
            actor_run.error_log = None

        # Move dynamically added properties into physical columns or generic handling
        # Since DB model currently doesn't have total_new/total_duplicates natively,
        # we log them for now.
        total_new = getattr(actor_run, "total_new", 0)
        logger.info(
            "Dataset %s processed: scraped=%d, errors=%d, new=%d, final_status=%s",
            dataset_id,
            total_scraped,
            total_errors,
            total_new,
            actor_run.status,
        )

    except Exception as exc:
        # ── Dataset fetch or fatal error ─────────────────────
        actor_run.status = "failed"
        actor_run.error_log = str(exc)
        logger.exception("Pipeline failed for dataset %s: %s", dataset_id, exc)

    finally:
        # ── Update run stats ─────────────────────────────────
        actor_run.total_scraped = total_scraped
        actor_run.total_errors = total_errors
        actor_run.completed_at = datetime.now(timezone.utc)

        db.add(actor_run)
        await db.commit()
        logger.info("Actor run %s finalised: status=%s", actor_run.id, actor_run.status)

        # ── Update company metrics ───────────────────────────
        try:
            logger.info("Triggering real-time calculate_company_metrics update...")
            await calculate_company_metrics(db)
        except Exception as e:
            logger.error("Failed to recalculate company metrics after pipeline: %s", e)
