"""
One-time utility to create custom HubSpot company properties.
"""

import logging
from typing import Any, Dict

from app.services.hubspot.hubspot_client import hubspot_client

logger = logging.getLogger(__name__)


async def create_custom_properties() -> None:
    """Create custom HubSpot company properties needed by JobIntel."""

    properties = [
        {
            "name": "jobintel_id",
            "label": "JobIntel ID",
            "type": "string",
            "fieldType": "text",
            "groupName": "companyinformation",
        },
        {
            "name": "hiring_velocity_score",
            "label": "Hiring Velocity Score",
            "type": "number",
            "fieldType": "number",
            "groupName": "companyinformation",
        },
        {
            "name": "bd_tags",
            "label": "BD Tags",
            "type": "string",
            "fieldType": "text",
            "groupName": "companyinformation",
        },
        {
            "name": "total_postings_7d",
            "label": "Jobs Last 7 Days",
            "type": "number",
            "fieldType": "number",
            "groupName": "companyinformation",
        },
    ]

    for prop in properties:
        try:
            await hubspot_client._request("POST", "/crm/v3/properties/companies", prop)
            logger.info("Created property: %s", prop["name"])
        except ValueError as e:
            if "409" in str(e):
                logger.info("Property %s already exists, skipping", prop["name"])
            else:
                logger.error("Failed to create property %s: %s", prop["name"], str(e))
                raise
        except Exception as e:
            logger.error("Unexpected error creating property %s: %s", prop["name"], str(e))
            raise