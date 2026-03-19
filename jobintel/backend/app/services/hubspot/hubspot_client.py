"""
HubSpot API client with rate limiting and error handling.
"""

import asyncio
import logging
import time
from typing import Any, Dict, Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

# Rate limiting: 90 calls per 10 seconds (stay under 100 limit)
MAX_CALLS_PER_10S = 90


# Store loaded API key from database to avoid repeated DB queries
_cached_api_key: Optional[str] = None
_cache_last_checked: float = 0
_cache_ttl: float = 300  # Cache for 5 minutes


async def get_hubspot_api_key(db: Optional[Any] = None) -> str:
    """
    Get the HubSpot API key from database or environment.
    
    Priority:
    1. Database settings (if db is provided)
    2. Environment variable (.env file)
    3. Default placeholder value
    
    Args:
        db: Optional AsyncSession for database queries
        
    Returns:
        The HubSpot API key string
    """
    global _cached_api_key, _cache_last_checked
    import time
    
    current_time = time.time()
    
    # Try to get from database if available and cache is fresh
    if db is not None:
        try:
            from app.services.settings import get_setting
            
            # Use cached value if available and fresh
            if (
                _cached_api_key is not None and
                (current_time - _cache_last_checked) < _cache_ttl
            ):
                return _cached_api_key
            
            db_key = await get_setting(db, "hubspot_api_key")
            if db_key and db_key != "your_hubspot_api_key_here":
                _cached_api_key = db_key
                _cache_last_checked = current_time
                return db_key
        except Exception as e:
            logger.debug(f"Failed to get HubSpot API key from database: {e}")
    
    # Fallback to environment variable
    env_key = settings.HUBSPOT_API_KEY
    if env_key and env_key != "your_hubspot_api_key_here":
        return env_key
    
    # Return default placeholder
    return "your_hubspot_api_key_here"


def create_hubspot_client(api_key: Optional[str] = None) -> "HubSpotClient":
    """Factory function to create a new HubSpot client with a specific API key."""
    return HubSpotClient(api_key=api_key)


class HubSpotClient:
    """Async HubSpot API client with rate limiting."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.base_url = settings.HUBSPOT_BASE_URL
        # Use provided API key, fallback to settings, then to default
        api_key_value = api_key or settings.HUBSPOT_API_KEY
        self.headers = {
            "Authorization": f"Bearer {api_key_value}",
            "Content-Type": "application/json",
        }
        self._semaphore = asyncio.Semaphore(MAX_CALLS_PER_10S)

    async def _request(
        self, method: str, path: str, payload: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make a rate-limited request to HubSpot API."""
        async with self._semaphore:
            # Sleep to spread requests over time (90 calls per 10s = ~0.11s per call)
            await asyncio.sleep(0.12)

            url = f"{self.base_url}{path}"

            logger.debug("HubSpot %s %s", method, path)

            async with httpx.AsyncClient(timeout=60.0) as client:
                try:
                    response = await client.request(
                        method=method,
                        url=url,
                        headers=self.headers,
                        json=payload,
                    )

                    if response.status_code == 429:
                        # Rate limited - wait 11 seconds and retry once
                        logger.warning(
                            "HubSpot rate limit hit, waiting 11 seconds and retrying"
                        )
                        await asyncio.sleep(11)
                        response = await client.request(
                            method=method,
                            url=url,
                            headers=self.headers,
                            json=payload,
                        )

                    if response.status_code >= 400:
                        error_body = response.text
                        logger.error(
                            "HubSpot API error %d: %s", response.status_code, error_body
                        )
                        if response.status_code >= 500:
                            raise RuntimeError(
                                f"HubSpot server error {response.status_code}: {error_body}"
                            )
                        else:
                            raise ValueError(
                                f"HubSpot API error {response.status_code}: {error_body}"
                            )

                    return response.json()

                except (httpx.TimeoutException, httpx.ReadTimeout) as e:
                    # Timeout - wait 5 seconds and retry once
                    logger.warning("HubSpot request timeout, retrying once after 5s: %s", str(e))
                    await asyncio.sleep(5)
                    try:
                        response = await client.request(
                            method=method,
                            url=url,
                            headers=self.headers,
                            json=payload,
                        )
                        if response.status_code >= 400:
                             raise RuntimeError(f"HubSpot retry failed with {response.status_code}")
                        return response.json()
                    except Exception as retry_e:
                        logger.error("HubSpot retry failed: %s", str(retry_e))
                        raise RuntimeError(f"HubSpot request timeout after retry: {str(retry_e)}") from retry_e

                except httpx.RequestError as e:
                    logger.error("HubSpot request error: %s", str(e))
                    raise RuntimeError(f"HubSpot request error: {str(e)}") from e

    # ── Company methods ────────────────────────────────────────

    async def find_company_by_jobintel_id(self, jobintel_id: str) -> Optional[str]:
        """Find HubSpot company by JobIntel ID."""
        payload = {
            "filterGroups": [
                {
                    "filters": [
                        {
                            "propertyName": "jobintel_id",
                            "operator": "EQ",
                            "value": jobintel_id,
                        }
                    ]
                }
            ],
            "properties": ["jobintel_id", "name"],
        }

        response = await self._request("POST", "/crm/v3/objects/companies/search", payload)
        results = response.get("results", [])
        return results[0]["id"] if results else None

    async def create_company(self, properties: Dict[str, Any]) -> str:
        """Create a new HubSpot company."""
        payload = {"properties": properties}
        response = await self._request("POST", "/crm/v3/objects/companies", payload)
        return response["id"]

    async def update_company(self, hubspot_id: str, properties: Dict[str, Any]) -> None:
        """Update an existing HubSpot company."""
        payload = {"properties": properties}
        await self._request("PATCH", f"/crm/v3/objects/companies/{hubspot_id}", payload)

    async def upsert_company(self, jobintel_id: str, properties: Dict[str, Any]) -> str:
        """Upsert a HubSpot company by JobIntel ID."""
        existing_id = await self.find_company_by_jobintel_id(jobintel_id)
        if existing_id:
            await self.update_company(existing_id, properties)
            return existing_id
        else:
            return await self.create_company(properties)

    # ── Note method ────────────────────────────────────────────

    async def create_note_on_company(self, hubspot_company_id: str, note_body: str) -> str:
        """Create a note and associate it with a company."""
        # Step 1: Create the note
        timestamp_ms = str(int(time.time() * 1000))
        note_payload = {
            "properties": {
                "hs_note_body": note_body,
                "hs_timestamp": timestamp_ms,
            }
        }
        note_response = await self._request("POST", "/crm/v3/objects/notes", note_payload)
        note_id = note_response["id"]

        # Step 2: Associate note to company
        # Use per-note default association — no typeId needed, most reliable
        await self._request(
            "PUT",
            f"/crm/v4/objects/note/{note_id}/associations/default/company/{hubspot_company_id}",
            None,
        )

        return note_id

    # ── Contact methods ────────────────────────────────────────

    async def find_contact_by_email(self, email: str) -> Optional[str]:
        """Find HubSpot contact by email."""
        payload = {
            "filterGroups": [
                {
                    "filters": [
                        {
                            "propertyName": "email",
                            "operator": "EQ",
                            "value": email,
                        }
                    ]
                }
            ],
            "properties": ["email", "firstname", "lastname"],
        }

        response = await self._request("POST", "/crm/v3/objects/contacts/search", payload)
        results = response.get("results", [])
        return results[0]["id"] if results else None

    async def create_contact(self, properties: Dict[str, Any]) -> str:
        """Create a new HubSpot contact."""
        payload = {"properties": properties}
        response = await self._request("POST", "/crm/v3/objects/contacts", payload)
        return response["id"]

    async def update_contact(self, hubspot_id: str, properties: Dict[str, Any]) -> None:
        """Update an existing HubSpot contact."""
        payload = {"properties": properties}
        await self._request("PATCH", f"/crm/v3/objects/contacts/{hubspot_id}", payload)

    async def upsert_contact(
        self, email: Optional[str], properties: Dict[str, Any]
    ) -> Optional[str]:
        """Upsert a HubSpot contact by email."""
        if not email:
            return None

        existing_id = await self.find_contact_by_email(email)
        if existing_id:
            await self.update_contact(existing_id, properties)
            return existing_id
        else:
            return await self.create_contact(properties)

    async def associate_contact_to_company(
        self, hubspot_company_id: str, hubspot_contact_id: str
    ) -> None:
        """Associate a contact with a company."""
        payload = {
            "inputs": [
                {
                    "from": {"id": hubspot_company_id},
                    "to": {"id": hubspot_contact_id},
                    "types": [
                        {
                            "associationCategory": "HUBSPOT_DEFINED",
                            "associationTypeId": 280,
                        }
                    ],
                }
            ]
        }
        await self._request(
            "PUT", "/crm/v4/associations/companies/contacts/batch/create", payload
        )

    # ── Deal methods ───────────────────────────────────────────

    async def find_deal_by_name(self, deal_name: str) -> Optional[str]:
        """Find HubSpot deal by name."""
        payload = {
            "filterGroups": [
                {
                    "filters": [
                        {
                            "propertyName": "dealname",
                            "operator": "EQ",
                            "value": deal_name,
                        }
                    ]
                }
            ],
            "properties": ["dealname"],
        }

        response = await self._request("POST", "/crm/v3/objects/deals/search", payload)
        results = response.get("results", [])
        return results[0]["id"] if results else None

    async def create_deal(self, properties: Dict[str, Any]) -> str:
        """Create a new HubSpot deal."""
        payload = {"properties": properties}
        response = await self._request("POST", "/crm/v3/objects/deals", payload)
        return response["id"]

    async def associate_deal_to_company(
        self, hubspot_company_id: str, hubspot_deal_id: str
    ) -> None:
        """Associate a deal with a company."""
        payload = {
            "inputs": [
                {
                    "from": {"id": hubspot_company_id},
                    "to": {"id": hubspot_deal_id},
                    "types": [
                        {
                            "associationCategory": "HUBSPOT_DEFINED",
                            "associationTypeId": 342,
                        }
                    ],
                }
            ]
        }
        await self._request(
            "PUT", "/crm/v4/associations/companies/deals/batch/create", payload
        )

    # ── Batch methods ───────────────────────────────────────────

    async def batch_upsert_companies(
        self, records: list[Dict[str, Any]]
    ) -> list[Dict[str, Any]]:
        """
        Upsert up to 100 companies in a single API call.
        Each record: { "idProperty": "jobintel_id", "id": <jobintel_id>,
                       "properties": { ... } }
        Uses POST /crm/v3/objects/companies/batch/upsert
        Returns list of { "id": hubspot_id, "properties": {...} }
        """
        results = []
        for i in range(0, len(records), 100):
            chunk = records[i:i + 100]
            payload = {"inputs": chunk}
            response = await self._request(
                "POST", "/crm/v3/objects/companies/batch/upsert", payload
            )
            results.extend(response.get("results", []))
            await asyncio.sleep(0.15)
        return results

    async def batch_create_notes(
        self, notes: list[Dict[str, Any]]
    ) -> list[str]:
        """
        Create up to 100 notes in one call.
        Each note: { "properties": { "hs_note_body": "...",
                                      "hs_timestamp": "..." } }
        Uses POST /crm/v3/objects/notes/batch/create
        Returns list of created note ids.
        """
        results = []
        for i in range(0, len(notes), 100):
            chunk = notes[i:i + 100]
            payload = {"inputs": chunk}
            response = await self._request(
                "POST", "/crm/v3/objects/notes/batch/create", payload
            )
            results.extend([r["id"] for r in response.get("results", [])])
            await asyncio.sleep(0.15)
        return results

    async def batch_associate_notes(
        self, pairs: list[tuple[str, str]]
    ) -> None:
        """
        Associate notes to companies using the default association endpoint.
        Uses PUT /crm/v4/objects/note/{note_id}/associations/default/company/{company_id}
        per note — no typeId required, most reliable approach per HubSpot docs.
        pairs: list of (hubspot_company_id, note_id)
        """
        for company_id, note_id in pairs:
            try:
                await self._request(
                    "PUT",
                    f"/crm/v4/objects/note/{note_id}/associations/default/company/{company_id}",
                    None,
                )
            except Exception as e:
                logger.warning(
                    "Failed to associate note %s to company %s: %s",
                    note_id, company_id, str(e)
                )
            await asyncio.sleep(0.12)

    async def batch_create_deals(
        self, deals: list[Dict[str, Any]]
    ) -> list[Dict[str, Any]]:
        """
        Create up to 100 deals in one call.
        Each deal: { "properties": { "dealname": "...",
                                      "dealstage": "appointmentscheduled",
                                      "pipeline": "default" } }
        Uses POST /crm/v3/objects/deals/batch/create
        Returns list of { "id": deal_id, "properties": {...} }
        """
        results = []
        for i in range(0, len(deals), 100):
            chunk = deals[i:i + 100]
            payload = {"inputs": chunk}
            response = await self._request(
                "POST", "/crm/v3/objects/deals/batch/create", payload
            )
            results.extend(response.get("results", []))
            await asyncio.sleep(0.15)
        return results

    async def batch_associate_deals(
        self, pairs: list[tuple[str, str]]
    ) -> None:
        """
        pairs: list of (hubspot_company_id, deal_id)
        Uses POST /crm/v4/associations/companies/deals/batch/create
        associationTypeId: 342
        """
        inputs = [
            {
                "from": {"id": company_id},
                "to": {"id": deal_id},
                "types": [
                    {
                        "associationCategory": "HUBSPOT_DEFINED",
                        "associationTypeId": 342,
                    }
                ],
            }
            for company_id, deal_id in pairs
        ]

        for i in range(0, len(inputs), 100):
            chunk = inputs[i:i + 100]
            payload = {"inputs": chunk}
            await self._request(
                "POST", "/crm/v4/associations/companies/deals/batch/create", payload
            )
            await asyncio.sleep(0.15)

    async def batch_upsert_contacts(
        self, records: list[Dict[str, Any]]
    ) -> list[Dict[str, Any]]:
        """
        Each record: { "idProperty": "email", "id": <email>,
                       "properties": { ... } }
        Uses POST /crm/v3/objects/contacts/batch/upsert
        Returns list of results.
        """
        # Only include records where email is non-empty
        valid_records = [r for r in records if r.get("id")]

        results = []
        for i in range(0, len(valid_records), 100):
            chunk = valid_records[i:i + 100]
            payload = {"inputs": chunk}
            response = await self._request(
                "POST", "/crm/v3/objects/contacts/batch/upsert", payload
            )
            results.extend(response.get("results", []))
            await asyncio.sleep(0.15)
        return results

    async def batch_associate_contacts(
        self, pairs: list[tuple[str, str]]
    ) -> None:
        """
        pairs: list of (hubspot_company_id, contact_id)
        associationTypeId: 280
        POST /crm/v4/associations/companies/contacts/batch/create
        """
        inputs = [
            {
                "from": {"id": company_id},
                "to": {"id": contact_id},
                "types": [
                    {
                        "associationCategory": "HUBSPOT_DEFINED",
                        "associationTypeId": 280,
                    }
                ],
            }
            for company_id, contact_id in pairs
        ]

        for i in range(0, len(inputs), 100):
            chunk = inputs[i:i + 100]
            payload = {"inputs": chunk}
            await self._request(
                "POST", "/crm/v4/associations/companies/contacts/batch/create", payload
            )
            await asyncio.sleep(0.15)


# Module-level singleton
hubspot_client = HubSpotClient()