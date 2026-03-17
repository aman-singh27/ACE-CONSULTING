"""
Apify client wrapper – fetches dataset items from the Apify platform.
"""

import asyncio
from typing import Any

from apify_client import ApifyClient

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_client = ApifyClient(settings.APIFY_TOKEN)


def _fetch_items_sync(dataset_id: str) -> list[dict[str, Any]]:
    """Synchronous dataset fetch (apify_client is not async-native)."""
    dataset = _client.dataset(dataset_id)
    result = dataset.list_items()
    return result.items


async def fetch_dataset_items(dataset_id: str) -> list[dict[str, Any]]:
    """Fetch all items from an Apify dataset.

    Wraps the synchronous apify_client call in ``asyncio.to_thread``
    so it doesn't block the event loop.
    """
    logger.info("Fetching dataset %s", dataset_id)
    try:
        items = await asyncio.to_thread(_fetch_items_sync, dataset_id)
        logger.info("Records found: %d", len(items))
        return items
    except Exception as e:
        logger.exception("Error fetching items for dataset %s from Apify: %s", dataset_id, e)
        raise
