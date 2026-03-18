"""
HubSpot sync API endpoints.
"""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db

# Module-level sync state tracker
_last_sync_result: dict | None = None
_sync_in_progress: bool = False


def _store_sync_result(result: dict) -> None:
    """Store the result of a sync operation."""
    global _last_sync_result
    _last_sync_result = result


# Pydantic schemas
class SyncStatusResponse(BaseModel):
    status: str          # "idle" | "running" | "completed" | "failed"
    last_sync: dict | None = None
    next_scheduled: str  # "03:00 UTC daily"
    message: str


class SyncTriggerResponse(BaseModel):
    status: str
    message: str
    summary: dict | None = None


# Router setup
router = APIRouter(tags=["hubspot"])


@router.get("/sync/status", response_model=SyncStatusResponse)
async def get_sync_status():
    """Return the current HubSpot sync status and last result."""
    global _sync_in_progress, _last_sync_result

    if _sync_in_progress:
        status = "running"
        message = "Sync is currently in progress..."
    elif _last_sync_result is None:
        status = "idle"
        message = "No sync has run yet this session."
    elif "error" in _last_sync_result:
        status = "failed"
        message = f"Last sync failed: {_last_sync_result['error']}"
    else:
        status = "completed"
        companies = _last_sync_result.get('companies_synced', 0)
        synced_at = _last_sync_result.get('synced_at', 'unknown')
        message = (
            f"Last sync: {companies} companies synced "
            f"at {synced_at}"
        )

    return SyncStatusResponse(
        status=status,
        last_sync=_last_sync_result,
        next_scheduled="03:00 UTC daily",
        message=message
    )


@router.post("/sync", response_model=SyncTriggerResponse)
async def trigger_sync(
    hours_back: int = Query(
        default=24,
        ge=1,
        le=168,
        description="How many hours back to sync (1-168)"
    ),
    db: AsyncSession = Depends(get_db)
):
    """
    Manually trigger a HubSpot sync.
    hours_back controls how far back to look for
    updated companies (default 24h, max 7 days / 168h).
    """
    global _sync_in_progress, _last_sync_result

    if _sync_in_progress:
        return SyncTriggerResponse(
            status="already_running",
            message="A sync is already in progress. "
                    "Please wait for it to complete.",
            summary=None
        )

    _sync_in_progress = True
    try:
        from app.services.hubspot.sync_service import (
            sync_companies_to_hubspot
        )
        summary = await sync_companies_to_hubspot(
            db, hours_back=hours_back
        )
        _last_sync_result = summary

        if "error" in summary:
            return SyncTriggerResponse(
                status="failed",
                message=f"Sync failed: {summary['error']}",
                summary=summary
            )

        return SyncTriggerResponse(
            status="completed",
            message=(
                f"Sync complete: "
                f"{summary.get('companies_synced', 0)} companies, "
                f"{summary.get('notes_created', 0)} notes, "
                f"{summary.get('deals_created', 0)} deals, "
                f"{summary.get('contacts_synced', 0)} contacts "
                f"in {summary.get('duration_seconds', 0)}s"
            ),
            summary=summary
        )

    except Exception as e:
        error_result = {
            "error": str(e),
            "companies_synced": 0,
            "synced_at": datetime.now(timezone.utc).isoformat()
        }
        _last_sync_result = error_result
        return SyncTriggerResponse(
            status="failed",
            message=f"Sync failed unexpectedly: {str(e)}",
            summary=error_result
        )
    finally:
        _sync_in_progress = False


@router.post("/sync/company/{company_id}", response_model=SyncTriggerResponse)
async def sync_specific_company(
    company_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Sync a specific company to HubSpot.
    Creates/updates the company, deal, and associated contacts.
    """
    from uuid import UUID
    try:
        company_uuid = UUID(company_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company ID format")

    try:
        from app.services.hubspot.sync_service import (
            sync_single_company_to_hubspot
        )

        summary = await sync_single_company_to_hubspot(db, company_uuid)

        if "error" in summary:
            return SyncTriggerResponse(
                status="failed",
                message=f"Sync failed: {summary['error']}",
                summary=summary
            )

        return SyncTriggerResponse(
            status="completed",
            message=(
                f"Company sync complete: "
                f"{summary.get('company_synced', False) and 'company' or 'no changes'}, "
                f"{summary.get('deal_created', False) and 'deal created' or 'deal exists'}, "
                f"{summary.get('contacts_synced', 0)} contacts"
            ),
            summary=summary
        )

    except Exception as e:
        return SyncTriggerResponse(
            status="failed",
            message=f"Sync failed unexpectedly: {str(e)}",
            summary={"error": str(e)}
        )


@router.post("/setup", status_code=200)
async def setup_hubspot_properties():
    """
    One-time endpoint to create custom HubSpot company
    properties required by JobIntel.
    Safe to call multiple times — skips existing properties.
    """
    try:
        from app.services.hubspot.property_setup import (
            create_custom_properties
        )
        await create_custom_properties()
        return {
            "status": "success",
            "message": "HubSpot custom properties created "
                       "(existing ones skipped)."
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Property setup failed: {str(e)}"
        )