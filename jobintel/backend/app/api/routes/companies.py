"""
Companies API endpoints.
"""

from typing import Literal, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.company import Company
from app.models.company import Company
from app.models.company_contact import CompanyContact
from app.models.job_posting import JobPosting
from app.schemas.api import CompanyResponse, JobResponse, PaginatedResponse
from app.services.enrichment.company_enrichment_service import enrich_company
from app.services.enrichment.contact_service import fetch_company_contacts

router = APIRouter(tags=["companies"])

SortOptions = Literal["bd_priority_score", "last_active_at", "total_postings_30d"]


@router.get("", response_model=PaginatedResponse[CompanyResponse])
async def list_companies(
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    domain: Optional[str] = None,
    country: Optional[str] = None,
    bd_tag: Optional[str] = None,
    is_enriched: Optional[bool] = None,
    search: Optional[str] = None,
    sort: SortOptions = "bd_priority_score",
    db: AsyncSession = Depends(get_db),
):
    """List companies with pagination and filtering."""
    
    offset = (page - 1) * limit
    
    stmt = select(Company)
    count_stmt = select(func.count(Company.id))
    
    # Filters
    filters = []
    if domain:
        filters.append(Company.domains_active.any(domain))
    if country:
        filters.append(Company.countries.any(country))
    if bd_tag:
        filters.append(Company.bd_tags.any(bd_tag))
    if is_enriched is not None:
        filters.append(Company.is_enriched == is_enriched)
    if search:
        filters.append(Company.company_name.ilike(f"%{search}%"))
        
    if filters:
        stmt = stmt.where(*filters)
        count_stmt = count_stmt.where(*filters)
        
    # Sorting
    if sort == "bd_priority_score":
        stmt = stmt.order_by(Company.bd_priority_score.desc())
    elif sort == "last_active_at":
        stmt = stmt.order_by(Company.last_active_at.desc().nulls_last())
    elif sort == "total_postings_30d":
        stmt = stmt.order_by(Company.total_postings_30d.desc())
        
    stmt = stmt.offset(offset).limit(limit)
    
    # Execute
    total_res = await db.execute(count_stmt)
    total = total_res.scalar_one()
    
    result = await db.execute(stmt)
    items = result.scalars().all()
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        limit=limit
    )


@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(company_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get full details of a specific company by ID."""
    
    result = await db.execute(select(Company).where(Company.id == company_id))
    company = result.scalar_one_or_none()
    
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
        
    return company


@router.get("/{company_id}/jobs", response_model=PaginatedResponse[JobResponse])
async def get_company_jobs(
    company_id: UUID,
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Get paginated jobs for a specific company."""
    
    offset = (page - 1) * limit
    
    # Verify company exists
    comp_res = await db.execute(select(Company.id).where(Company.id == company_id))
    if not comp_res.first():
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Fetch jobs
    stmt = (
        select(JobPosting)
        .where(JobPosting.company_id == company_id)
        .order_by(JobPosting.posted_at.desc().nulls_last())
        .offset(offset)
        .limit(limit)
    )
    count_stmt = select(func.count(JobPosting.id)).where(JobPosting.company_id == company_id)
    
    total_res = await db.execute(count_stmt)
    total = total_res.scalar_one()
    
    result = await db.execute(stmt)
    items = result.scalars().all()
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        limit=limit
    )

@router.post("/{company_id}/enrich")
async def enrich_company_endpoint(
    company_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Enrich a company profile using Apollo data."""
    data = await enrich_company(db, company_id)
    
    return {
        "status": "enriched",
        "data": data
    }

@router.post("/{company_id}/contacts")
async def find_contacts(
    company_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Find contacts for a company profile using Apollo people search."""
    company = await db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    contacts = await fetch_company_contacts(db, company_id)
    
    return {
        "status": "success",
        "contacts": contacts
    }
