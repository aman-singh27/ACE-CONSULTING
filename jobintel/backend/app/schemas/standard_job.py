"""
StandardJob – unified internal schema for all scraped job records.

Every platform normalizer converts raw actor output into this object.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class StandardJob:
    """Platform-agnostic representation of a single job posting."""

    # ── Required ─────────────────────────────────────────────
    title: str
    company_name: str
    job_url: str
    source_platform: str
    actor_id: str

    # ── Identity ─────────────────────────────────────────────
    job_id: Optional[str] = None
    fingerprint_hash: Optional[str] = None
    is_duplicate: bool = False

    # ── Normalized Fields ────────────────────────────────────
    title_normalized: Optional[str] = None
    company_normalized: Optional[str] = None

    # ── Location ─────────────────────────────────────────────
    location_raw: Optional[str] = None
    location_city: Optional[str] = None
    location_country: Optional[str] = None
    location_region: Optional[str] = None

    # ── Dates ────────────────────────────────────────────────
    posted_at: Optional[datetime] = None

    # ── Domain ───────────────────────────────────────────────
    domain: Optional[str] = None

    # ── Salary ───────────────────────────────────────────────
    salary_raw: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: Optional[str] = None

    # ── Employment ───────────────────────────────────────────
    employment_type: Optional[str] = None

    # ── Experience ───────────────────────────────────────────
    experience_years_min: Optional[int] = None
    experience_years_max: Optional[int] = None

    # ── Content ──────────────────────────────────────────────
    description_raw: Optional[str] = None
