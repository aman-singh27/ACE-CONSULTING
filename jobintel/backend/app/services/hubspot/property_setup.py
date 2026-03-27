"""
One-time utility to create custom HubSpot company properties.
"""

import asyncio
import logging
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.hubspot.hubspot_client import (
    create_hubspot_client,
    get_hubspot_api_key,
)

logger = logging.getLogger(__name__)


def _is_transient_hubspot_error(exc: Exception) -> bool:
    """Return True for HubSpot/network failures that are safe to retry."""
    message = str(exc)

    if "HubSpot request error:" in message:
        return True

    if "HubSpot request timeout" in message:
        return True

    if "HubSpot server error" in message:
        # Retry only 5xx responses, not client errors.
        try:
            status_code = int(message.split("HubSpot server error ", 1)[1].split(":", 1)[0])
        except (IndexError, ValueError):
            return True
        return status_code >= 500

    return False


async def _request_with_retry(
    hubspot_client: Any,
    method: str,
    path: str,
    payload: Optional[Dict[str, Any]] = None,
    *,
    property_name: str,
    operation: str,
    max_attempts: int = 3,
    base_delay_seconds: float = 0.5,
) -> Any:
    """
    Call HubSpot with bounded retry/backoff for transient failures.

    Non-retriable HubSpot validation errors are allowed to bubble up as-is.
    """
    last_error: Optional[Exception] = None

    for attempt in range(1, max_attempts + 1):
        try:
            return await hubspot_client._request(method, path, payload)
        except RuntimeError as exc:
            if not _is_transient_hubspot_error(exc):
                raise

            last_error = exc
            if attempt >= max_attempts:
                logger.error(
                    "Giving up %s for property %s after %d attempts: %s",
                    operation,
                    property_name,
                    max_attempts,
                    str(exc),
                )
                return None

            delay = base_delay_seconds * (2 ** (attempt - 1))
            logger.warning(
                "Transient HubSpot error while %s property %s (attempt %d/%d): %s. "
                "Retrying in %.1fs",
                operation,
                property_name,
                attempt,
                max_attempts,
                str(exc),
                delay,
            )
            await asyncio.sleep(delay)

    if last_error is not None:
        logger.error(
            "Exhausted retries while %s property %s: %s",
            operation,
            property_name,
            str(last_error),
        )
    return None


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
        existing_prop = await _request_with_retry(
            hubspot_client,
            "GET",
            "/crm/v3/properties/companies/jobintel_id",
            property_name="jobintel_id",
            operation="checking existing property",
        )
        if existing_prop is None:
            logger.warning(
                "Skipping jobintel_id existence check after transient HubSpot errors; "
                "continuing with property setup"
            )
        elif not existing_prop.get("hasUniqueValue", False):
            logger.info("jobintel_id exists but hasUniqueValue=False, deleting and recreating...")
            try:
                delete_result = await _request_with_retry(
                    hubspot_client,
                    "DELETE",
                    "/crm/v3/properties/companies/jobintel_id",
                    property_name="jobintel_id",
                    operation="deleting stale property",
                )
                if delete_result is None:
                    logger.warning(
                        "Could not delete stale jobintel_id after transient errors; "
                        "continuing with the rest of setup"
                    )
                else:
                    logger.info("Deleted existing jobintel_id property")
            except ValueError as e:
                if "404" in str(e):
                    logger.info("jobintel_id property already missing, continuing")
                else:
                    logger.error("Error deleting existing jobintel_id property: %s", str(e))
                    raise
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
            "name": "bd_tag_count",
            "label": "BD Signal Count (JobIntel)",
            "type": "number",
            "fieldType": "number",
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
            result = await _request_with_retry(
                hubspot_client,
                "POST",
                "/crm/v3/properties/companies",
                prop,
                property_name=prop["name"],
                operation="creating",
            )
            if result is None:
                logger.warning(
                    "Skipping property %s after repeated transient HubSpot errors",
                    prop["name"],
                )
                continue
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
