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
from app.schemas.api import CompanyResponse, JobResponse, CompanyContactResponse, PaginatedResponse
from app.services.intelligence.priority_engine import update_all_company_scores
from app.utils.contact_validation import is_valid_phone_number

router = APIRouter(tags=["companies"])

SortOptions = Literal["bd_priority_score", "last_active_at", "total_postings_30d"]


@router.get("", response_model=PaginatedResponse[CompanyResponse])
async def list_companies(
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=1000),
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


@router.get("/{company_id}/contacts", response_model=PaginatedResponse[CompanyContactResponse])
async def get_company_contacts(
    company_id: UUID,
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Get paginated contacts for a specific company."""
    
    offset = (page - 1) * limit
    
    # Verify company exists
    comp_res = await db.execute(select(Company.id).where(Company.id == company_id))
    if not comp_res.first():
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Fetch all contacts for this company
    stmt = (
        select(CompanyContact)
        .where(CompanyContact.company_id == company_id)
        .order_by(CompanyContact.seniority.desc().nulls_last())
        .offset(offset)
        .limit(limit)
    )
    count_stmt = (
        select(func.count(CompanyContact.id)).where(
            CompanyContact.company_id == company_id
        )
    )
    
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


@router.post("/admin/recalculate-all-scores")
async def recalculate_all_scores(db: AsyncSession = Depends(get_db)):
    """
    Recalculates BD priority scores and tags for ALL companies.
    Use this after major logic changes to update existing data.
    """
    result = await update_all_company_scores(db)
    return result


@router.post("/admin/fix-contact-available-tags")
async def fix_contact_available_tags(db: AsyncSession = Depends(get_db)):
    """
    Fixes the 'contact_available' BD tag for all companies.
    Removes the tag from companies that don't have valid contacts.
    Adds the tag to companies that have valid contacts but are missing the tag.
    """
    from app.core.logging import get_logger
    logger = get_logger(__name__)
    
    # Get all companies with contact_available tag
    stmt = select(Company).where(Company.bd_tags.any("contact_available"))
    result = await db.execute(stmt)
    companies_with_tag = result.scalars().all()
    
    # Get all contacts
    contacts_stmt = select(CompanyContact)
    contacts_result = await db.execute(contacts_stmt)
    all_contacts = contacts_result.scalars().all()
    
    # Build map of companies with valid contacts
    companies_with_valid_contacts = {}
    for contact in all_contacts:
        company_id = str(contact.company_id)
        has_valid_phone = contact.phone and is_valid_phone_number(contact.phone)
        has_valid_email = contact.email and "@" in contact.email
        
        if has_valid_phone or has_valid_email:
            if company_id not in companies_with_valid_contacts:
                companies_with_valid_contacts[company_id] = True
    
    # Clean up existing companies
    removed_count = 0
    for company in companies_with_tag:
        company_id = str(company.id)
        # If company doesn't have valid contacts, remove the tag
        if company_id not in companies_with_valid_contacts:
            if "contact_available" in company.bd_tags:
                company.bd_tags = [tag for tag in company.bd_tags if tag != "contact_available"]
                removed_count += 1
                logger.info(f"Removed 'contact_available' tag from {company.company_name}")
    
    # Get all companies
    all_companies_stmt = select(Company)
    all_companies_result = await db.execute(all_companies_stmt)
    all_companies = all_companies_result.scalars().all()
    
    # Add tag to companies with valid contacts but missing tag
    added_count = 0
    for company in all_companies:
        company_id = str(company.id)
        if company_id in companies_with_valid_contacts:
            if "contact_available" not in company.bd_tags:
                company.bd_tags = company.bd_tags + ["contact_available"]
                added_count += 1
                logger.info(f"Added 'contact_available' tag to {company.company_name}")
    
    await db.commit()
    
    logger.info(f"Contact tag cleanup complete: removed {removed_count}, added {added_count}")
    
    return {
        "status": "success",
        "message": f"Fixed contact_available tags",
        "tags_removed": removed_count,
        "tags_added": added_count,
        "total_processed": removed_count + added_count
    }
