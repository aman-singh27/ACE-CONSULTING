"""
Jobs API endpoints.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.job_posting import JobPosting
from app.models.company_contact import CompanyContact
from app.schemas.api import JobDetailResponse, JobResponse, PaginatedResponse

router = APIRouter(tags=["jobs"])


@router.get("", response_model=PaginatedResponse[JobResponse])
async def list_jobs(
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    domain: Optional[str] = None,
    platform: Optional[str] = None,
    country: Optional[str] = None,
    company_id: Optional[UUID] = None,
    is_duplicate: Optional[bool] = None,
    employment_type: Optional[str] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """List jobs with pagination and filtering."""
    
    offset = (page - 1) * limit
    
    # Base query
    stmt = select(JobPosting)
    count_stmt = select(func.count(JobPosting.id))
    
    # Filters
    filters = []
    if domain:
        filters.append(JobPosting.domain == domain)
    if platform:
        filters.append(JobPosting.source_platform == platform)
    if country:
        filters.append(JobPosting.location_country == country)
    if company_id:
        filters.append(JobPosting.company_id == company_id)
    if is_duplicate is not None:
        filters.append(JobPosting.is_duplicate == is_duplicate)
    if employment_type:
        filters.append(JobPosting.employment_type == employment_type)
    if search:
        filters.append(
            or_(
                JobPosting.title.ilike(f"%{search}%"),
                JobPosting.company_name.ilike(f"%{search}%")
            )
        )
        
    if filters:
        stmt = stmt.where(*filters)
        count_stmt = count_stmt.where(*filters)
        
    # Order & Pagination
    stmt = stmt.order_by(JobPosting.posted_at.desc().nulls_last()).offset(offset).limit(limit)
    
    # Execute
    total_res = await db.execute(count_stmt)
    total = total_res.scalar_one()
    
    result = await db.execute(stmt)
    items = result.scalars().all()
    
    # NEW: Fetch contacts for these jobs
    company_ids = {item.company_id for item in items if item.company_id}
    contact_map_emails = {}
    contact_map_phones = {}
    
    if company_ids:
        contact_stmt = select(CompanyContact).where(CompanyContact.company_id.in_(company_ids))
        contact_res = await db.execute(contact_stmt)
        contacts = contact_res.scalars().all()
        
        for c in contacts:
            cid = c.company_id
            if cid not in contact_map_emails:
                contact_map_emails[cid] = []
            if cid not in contact_map_phones:
                contact_map_phones[cid] = []
                
            if c.email and c.email not in contact_map_emails[cid]:
                contact_map_emails[cid].append(c.email)
            if c.phone and c.phone not in contact_map_phones[cid]:
                contact_map_phones[cid].append(c.phone)

    # Convert to JobResponse and attach contacts
    job_responses = []
    for item in items:
        jr = JobResponse.model_validate(item)
        jr.emails = contact_map_emails.get(item.company_id, [])
        jr.phones = contact_map_phones.get(item.company_id, [])
        job_responses.append(jr)
    
    return PaginatedResponse(
        items=job_responses,
        total=total,
        page=page,
        limit=limit
    )


@router.get("/{job_id}", response_model=JobDetailResponse)
async def get_job(job_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get full details of a specific job by ID."""
    
    result = await db.execute(select(JobPosting).where(JobPosting.id == job_id))
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    responses = JobDetailResponse.model_validate(job)
    
    # Fetch contacts
    if job.company_id:
        contact_stmt = select(CompanyContact).where(CompanyContact.company_id == job.company_id)
        contact_res = await db.execute(contact_stmt)
        contacts = contact_res.scalars().all()
        responses.emails = list(set(c.email for c in contacts if c.email))
        responses.phones = list(set(c.phone for c in contacts if c.phone))
        
    return responses
