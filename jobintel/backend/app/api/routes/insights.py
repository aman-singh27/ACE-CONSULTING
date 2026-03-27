"""
Insights API endpoints (BD Priority List, etc.)
"""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.company import Company
from app.schemas.api import PriorityListCompany

from app.services.intelligence.priority_engine import get_bd_priority_list

router = APIRouter(tags=["insights"])

@router.get("/priority-list", response_model=list[PriorityListCompany])
async def get_priority_list(limit: int = 50, db: AsyncSession = Depends(get_db)):
    """Fetch the top companies ordered by dynamic Business Development Priority Score."""
    return await get_bd_priority_list(db, limit)
