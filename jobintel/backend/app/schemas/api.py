"""
API response schemas for the frontend dashboard.
"""

from datetime import datetime
from typing import Generic, Optional, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Standard paginated wrapper."""
    items: list[T]
    total: int
    page: int
    limit: int


# ── Job Schemas ──────────────────────────────────────────────

class JobResponse(BaseModel):
    id: UUID
    job_id: str
    fingerprint_hash: Optional[str] = None
    
    title: str
    title_normalized: Optional[str] = None
    
    company_name: str
    company_id: Optional[UUID] = None
    
    domain: str
    source_platform: str
    
    location_raw: Optional[str] = None
    location_city: Optional[str] = None
    location_country: Optional[str] = None
    location_region: Optional[str] = None
    
    salary_raw: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: Optional[str] = None
    
    employment_type: Optional[str] = None
    experience_years_min: Optional[int] = None
    experience_years_max: Optional[int] = None
    
    posted_at: Optional[datetime] = None
    scraped_at: datetime
    job_url: Optional[str] = None
    
    is_duplicate: bool
    
    emails: list[str] = []
    phones: list[str] = []
    
    model_config = ConfigDict(from_attributes=True)


class JobDetailResponse(JobResponse):
    """Includes the full text description."""
    description_raw: Optional[str] = None


# ── Company Schemas ──────────────────────────────────────────

class CompanyResponse(BaseModel):
    id: UUID
    company_name: str
    company_name_normalized: str
    
    domains_active: list[str]
    platforms_seen_on: list[str]
    locations: list[str]
    countries: list[str]
    
    total_postings_alltime: int
    total_postings_7d: int
    total_postings_30d: int
    avg_postings_30d: Optional[float] = None
    
    first_seen_at: Optional[datetime] = None
    last_active_at: Optional[datetime] = None
    
    is_repeat_poster: bool
    repeated_roles: list[str]
    
    hiring_velocity_score: float
    bd_priority_score: float
    bd_tags: list[str]
    
    is_enriched: bool
    employee_count: Optional[str] = None
    industry_apollo: Optional[str] = None
    linkedin_url: Optional[str] = None
    website: Optional[str] = None
    hq_country: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ── Priority List Schemas ────────────────────────────────────

class PriorityListCompany(BaseModel):
    id: UUID
    rank: int
    company_id: str
    company_name: str
    domain: str
    domains_active: list[str]
    jobs_today: int
    total_postings_7d: int
    bd_score: float
    bd_priority_score: float
    tags: list[str]
    bd_tags: list[str]
    
    model_config = ConfigDict(from_attributes=True)


# ── Dashboard Summary ────────────────────────────────────────

class DashboardSummary(BaseModel):
    jobs_scraped_today: int
    new_companies_today: int
    active_actors: int
    total_bd_alerts: int


class DashboardAlert(BaseModel):
    id: UUID
    type: str # 'spiking_company', 'new_entrant', 'struggling_company', 'actor_failure', 'budget_warning'
    title: str
    description: str
    company_id: Optional[str] = None
    severity: str # 'info', 'warning', 'critical'
    
    model_config = ConfigDict(from_attributes=True)


# ── Domain Trends Schemas ────────────────────────────────────────────

class TopCompany(BaseModel):
    company_id: str
    company_name: str
    job_count: int

class DomainTrendsResponse(BaseModel):
    domain: str
    today_count: int
    yesterday_count: int
    wow_change: float
    active_companies: int
    top_company: Optional[TopCompany] = None
    
    model_config = ConfigDict(from_attributes=True)


# ── Geo Intelligence Schemas ─────────────────────────────────────────

class CountryHeatmapResponse(BaseModel):
    country: str
    job_count: int
    top_domain: str
    top_company: Optional[TopCompany] = None

    model_config = ConfigDict(from_attributes=True)


class CityBreakdownResponse(BaseModel):
    city: str
    job_count: int
    top_company: Optional[TopCompany] = None

    model_config = ConfigDict(from_attributes=True)


# ── Run Monitor Schemas ──────────────────────────────────────

class RunResponse(BaseModel):
    id: UUID
    apify_run_id: Optional[str] = None
    status: Optional[str] = None
    
    actor_name: Optional[str] = None
    platform: Optional[str] = None
    domain: Optional[str] = None
    
    total_scraped: int
    total_new: int
    total_duplicates: int
    total_cross_dupes: int
    total_errors: int
    
    cost_usd: Optional[float] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class RunDetailResponse(RunResponse):
    error_log: Optional[str] = None


class RunTodayResponse(BaseModel):
    id: UUID
    status: Optional[str] = None
    total_new: int
    started_at: Optional[datetime] = None
    
    actor_name: Optional[str] = None
    platform: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class HealthResponse(BaseModel):
    actor_name: str
    platform: str
    last_run: Optional[datetime] = None
    last_success: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)
