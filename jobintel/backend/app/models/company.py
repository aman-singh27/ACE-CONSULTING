"""
Company model – aggregated company profiles.
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
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.base import TimestampMixin


class Company(TimestampMixin, Base):
    __tablename__ = "companies"

    # ── Primary key ──────────────────────────────────────────
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # ── Identity ─────────────────────────────────────────────
    company_name: Mapped[Optional[str]] = mapped_column(Text)
    company_name_normalized: Mapped[Optional[str]] = mapped_column(
        Text, unique=True
    )

    # ── Presence ─────────────────────────────────────────────
    domains_active = mapped_column(ARRAY(Text), default=list)
    platforms_seen_on = mapped_column(ARRAY(Text), default=list)

    locations = mapped_column(ARRAY(Text), default=list)
    countries = mapped_column(ARRAY(Text), default=list)

    # ── Posting stats ────────────────────────────────────────
    total_postings_alltime: Mapped[int] = mapped_column(Integer, default=0)
    total_postings_7d: Mapped[int] = mapped_column(Integer, default=0)
    total_postings_30d: Mapped[int] = mapped_column(Integer, default=0)

    avg_postings_30d: Mapped[Optional[float]] = mapped_column(Numeric)

    # ── Activity ─────────────────────────────────────────────
    first_seen_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_active_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), index=True
    )

    is_repeat_poster: Mapped[bool] = mapped_column(Boolean, default=False)
    repeated_roles = mapped_column(ARRAY(Text), default=list)

    # ── Scoring ──────────────────────────────────────────────
    hiring_velocity_score: Mapped[float] = mapped_column(Numeric, default=0)
    bd_priority_score: Mapped[float] = mapped_column(Numeric, default=0)
    lead_score: Mapped[float] = mapped_column(Numeric, default=0)

    bd_tags = mapped_column(ARRAY(Text), default=list)

    # ── Enrichment ───────────────────────────────────────────
    is_enriched: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    enriched_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    apollo_data = mapped_column(JSONB, nullable=True)

    employee_count: Mapped[Optional[str]] = mapped_column(Text)
    industry_apollo: Mapped[Optional[str]] = mapped_column(Text)

    linkedin_url: Mapped[Optional[str]] = mapped_column(Text)
    website: Mapped[Optional[str]] = mapped_column(Text)

    hq_country: Mapped[Optional[str]] = mapped_column(Text)

    # ── Indexes (declarative) ────────────────────────────────
    __table_args__ = (
        Index("ix_companies_bd_priority_score", bd_priority_score.desc()),
    )
