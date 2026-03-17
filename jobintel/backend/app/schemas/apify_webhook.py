"""
Pydantic schemas for Apify webhook payloads.
"""

from pydantic import BaseModel


class ApifyEventData(BaseModel):
    actorId: str
    actorRunId: str

class ApifyResource(BaseModel):
    defaultDatasetId: str

class ApifyWebhookPayload(BaseModel):
    eventType: str
    eventData: ApifyEventData
    resource: ApifyResource
