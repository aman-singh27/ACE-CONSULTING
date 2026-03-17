"""
Interface for Apify API to trigger actor runs.
"""

from apify_client import ApifyClient
from app.core.config import settings
import asyncio

def _get_client():
    return ApifyClient(settings.APIFY_TOKEN)

async def run_actor(actor_id: str, actor_input: dict) -> str:
    """
    Trigger an Apify actor and return the Run ID.
    """
    client = _get_client()
    # Call is synchronous in the basic apify client, so we can wrap it in an executor if needed,
    # or use the AsyncApifyClient. We will use AsyncApifyClient instead.
    from apify_client import ApifyClientAsync
    async_client = ApifyClientAsync(settings.APIFY_TOKEN)
    
    logger = __import__('logging').getLogger(__name__)
    logger.debug(f"Starting actor run for actor_id: {actor_id} with input: {actor_input}")
    
    try:
        # Start the actor run but don't wait for it to finish
        start_kwargs = {"run_input": actor_input}
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
