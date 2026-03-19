"""
One-time utility to create custom HubSpot company properties.
"""

import logging
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.hubspot.hubspot_client import (
    create_hubspot_client,
    get_hubspot_api_key,
)

logger = logging.getLogger(__name__)


async def create_custom_properties(db: Optional[AsyncSession] = None) -> None:
    """
    Create custom HubSpot company properties needed by JobIntel.
    Automatically handles jobintel_id property: if it exists but doesn't have
    hasUniqueValue=True, it will be deleted and recreated correctly.
    
    Args:
        db: Optional AsyncSession for loading API key from database
    """
    # Get the current API key (from database or environment)
    api_key = await get_hubspot_api_key(db)
    hubspot_client = create_hubspot_client(api_key)

    # Special handling for jobintel_id: check if it exists and has correct hasUniqueValue
    try:
        existing_prop = await hubspot_client._request("GET", "/crm/v3/properties/companies/jobintel_id")
        if not existing_prop.get("hasUniqueValue", False):
            logger.info("jobintel_id exists but hasUniqueValue=False, deleting and recreating...")
            await hubspot_client._request("DELETE", "/crm/v3/properties/companies/jobintel_id")
            logger.info("Deleted existing jobintel_id property")
        else:
            logger.info("jobintel_id already exists with correct hasUniqueValue=True")
    except ValueError as e:
        if "404" in str(e):
            logger.info("jobintel_id property does not exist, will create it")
        else:
            logger.error("Error checking existing jobintel_id property: %s", str(e))
            raise
    except Exception as e:
        logger.error("Unexpected error checking jobintel_id property: %s", str(e))
        raise

    properties = [
        {
            "name": "jobintel_id",
            "label": "JobIntel ID",
            "type": "string",
            "fieldType": "text",
            "groupName": "companyinformation",
            "hasUniqueValue": True,      # ← CRITICAL: required for batch upsert
        },
        {
            "name": "hiring_velocity_score",
            "label": "Hiring Velocity Score",
            "type": "number",
            "fieldType": "number",
            "groupName": "companyinformation",
            "hasUniqueValue": False,
        },
        {
            "name": "bd_tags",
            "label": "BD Tags",
            "type": "string",
            "fieldType": "text",
            "groupName": "companyinformation",
            "hasUniqueValue": False,
        },
        {
            "name": "total_postings_7d",
            "label": "Jobs Last 7 Days",
            "type": "number",
            "fieldType": "number",
            "groupName": "companyinformation",
            "hasUniqueValue": False,
        },
        {
            "name": "jobintel_locations",
            "label": "JobIntel Locations",
            "type": "string",
            "fieldType": "text",
            "groupName": "companyinformation",
            "hasUniqueValue": False,
        },
        {
            "name": "jobintel_countries",
            "label": "JobIntel Countries",
            "type": "string",
            "fieldType": "text",
            "groupName": "companyinformation",
            "hasUniqueValue": False,
        },
        {
            "name": "linkedin_url_jobintel",
            "label": "LinkedIn URL (JobIntel)",
            "type": "string",
            "fieldType": "text",
            "groupName": "companyinformation",
            "hasUniqueValue": False,
        },
        {
            "name": "company_phone_jobintel",
            "label": "Company Phone (JobIntel)",
            "type": "string",
            "fieldType": "text",
            "groupName": "companyinformation",
            "hasUniqueValue": False,
        },
        {
            "name": "company_website_jobintel",
            "label": "Company Website (JobIntel)",
            "type": "string",
            "fieldType": "text",
            "groupName": "companyinformation",
            "hasUniqueValue": False,
        },
        {
            "name": "industry_jobintel",
            "label": "Industry (JobIntel)",
            "type": "string",
            "fieldType": "text",
            "groupName": "companyinformation",
            "hasUniqueValue": False,
        },
        {
            "name": "primary_contact_email",
            "label": "Primary Contact Email (JobIntel)",
            "type": "string",
            "fieldType": "text",
            "groupName": "companyinformation",
            "hasUniqueValue": False,
        },
        {
            "name": "primary_contact_phone",
            "label": "Primary Contact Phone (JobIntel)",
            "type": "string",
            "fieldType": "text",
            "groupName": "companyinformation",
            "hasUniqueValue": False,
        },
        {
            "name": "hq_country_jobintel",
            "label": "HQ Country (JobIntel)",
            "type": "string",
            "fieldType": "text",
            "groupName": "companyinformation",
            "hasUniqueValue": False,
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