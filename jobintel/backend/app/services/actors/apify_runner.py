"""
Interface for Apify API to trigger actor runs.
"""

import logging
from typing import Any

from app.core.config import settings

def _extract_positive_max_items(actor_input: dict) -> int | None:
    """
    Normalize common input keys into Apify's `max_items` kwarg.

    We keep the original actor input untouched for backward compatibility and
    only derive a run-level result cap when a positive value is present.
    """
    for key in ("jobsPerRun", "maxItems", "max_items"):
        raw_value = actor_input.get(key)
        if raw_value is None:
            continue

        try:
            value = int(raw_value)
        except (TypeError, ValueError):
            continue

        if value > 0:
            return value

    return None


async def run_actor(actor_id: str, actor_input: dict) -> str:
    """
    Trigger an Apify actor and return the Run ID.
    """
    from apify_client import ApifyClientAsync
    async_client = ApifyClientAsync(settings.APIFY_TOKEN)
    
    logger = logging.getLogger(__name__)
    logger.debug(f"Starting actor run for actor_id: {actor_id} with input: {actor_input}")
    
    try:
        # Start the actor run but don't wait for it to finish
        start_kwargs = {"run_input": actor_input}
        max_items = _extract_positive_max_items(actor_input)
        if max_items is not None:
            start_kwargs["max_items"] = max_items

        if settings.WEBHOOK_URL:
            # Apify webhook configuration
            start_kwargs["webhooks"] = [{
                "event_types": ["ACTOR.RUN.SUCCEEDED", "ACTOR.RUN.FAILED", "ACTOR.RUN.ABORTED", "ACTOR.RUN.TIMED_OUT"],
                "request_url": settings.WEBHOOK_URL,
                "headers_template": f'{{"X-Webhook-Secret": "{settings.WEBHOOK_SECRET}"}}'
            }]
            
        run = await async_client.actor(actor_id).start(**start_kwargs)
        logger.info(f"Successfully started actor {actor_id}, run_id: {run.get('id')}")
        return str(run["id"])
    except Exception as e:
        logger.exception(f"Failed to start actor {actor_id} with input {actor_input}. Error: {e}")
        raise


async def wait_for_actor_run_finish(
    apify_run_id: str,
    wait_secs: int = 1800,
) -> dict[str, Any] | None:
    """Wait for a run to finish and return the Apify run payload."""
    from apify_client import ApifyClientAsync
    async_client = ApifyClientAsync(settings.APIFY_TOKEN)

    logger = logging.getLogger(__name__)
    logger.info(
        "Waiting for Apify run %s to finish (wait_secs=%s)",
        apify_run_id,
        wait_secs,
    )
    return await async_client.run(apify_run_id).wait_for_finish(wait_secs=wait_secs)


async def get_actor_run(apify_run_id: str) -> dict[str, Any] | None:
    """Fetch current Apify run details without waiting."""
    from apify_client import ApifyClientAsync
    async_client = ApifyClientAsync(settings.APIFY_TOKEN)
    return await async_client.run(apify_run_id).get()
