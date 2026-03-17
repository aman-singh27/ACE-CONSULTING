"""
JobPosting model – individual scraped job listings.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Index,
    Integer,
    Numeric,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class JobPosting(Base):
    __tablename__ = "job_postings"

    # ── Primary key ──────────────────────────────────────────
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # ── Identity ─────────────────────────────────────────────
    job_id: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    fingerprint_hash: Mapped[Optional[str]] = mapped_column(Text, index=True)

    # ── Title ────────────────────────────────────────────────
    title: Mapped[str] = mapped_column(Text, nullable=False)
    title_normalized: Mapped[Optional[str]] = mapped_column(Text)

    # ── Company ──────────────────────────────────────────────
    company_name: Mapped[str] = mapped_column(Text, nullable=False)
    company_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )

    # ── Source ───────────────────────────────────────────────
    domain: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    source_platform: Mapped[str] = mapped_column(Text, nullable=False, index=True)

    actor_id: Mapped[str] = mapped_column(Text, nullable=False)
    run_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )

    # ── Location ─────────────────────────────────────────────
    location_raw: Mapped[Optional[str]] = mapped_column(Text)
    location_city: Mapped[Optional[str]] = mapped_column(Text)
    location_country: Mapped[Optional[str]] = mapped_column(Text, index=True)
    location_region: Mapped[Optional[str]] = mapped_column(Text)

    # ── Salary ───────────────────────────────────────────────
    salary_raw: Mapped[Optional[str]] = mapped_column(Text)
    salary_min: Mapped[Optional[float]] = mapped_column(Numeric)
    salary_max: Mapped[Optional[float]] = mapped_column(Numeric)
    salary_currency: Mapped[Optional[str]] = mapped_column(Text)

    # ── Employment ───────────────────────────────────────────
    employment_type: Mapped[Optional[str]] = mapped_column(Text)

    # ── Experience ───────────────────────────────────────────
    experience_years_min: Mapped[Optional[int]] = mapped_column(Integer)
    experience_years_max: Mapped[Optional[int]] = mapped_column(Integer)

    # ── Dates ────────────────────────────────────────────────
    posted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), index=True
    )
    scraped_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    # ── Content ──────────────────────────────────────────────
    job_url: Mapped[Optional[str]] = mapped_column(Text)
    description_raw: Mapped[Optional[str]] = mapped_column(Text)

    # ── Dedup ────────────────────────────────────────────────
    is_duplicate: Mapped[bool] = mapped_column(Boolean, default=False)

    # ── Timestamps ───────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
