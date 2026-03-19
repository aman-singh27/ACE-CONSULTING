"""
EnrichmentCache model – cached enrichment data from Apollo and other sources.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import (
    ForeignKey,
    Text,
    DateTime,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
from app.models.base import TimestampMixin


class EnrichmentCache(TimestampMixin, Base):
    __tablename__ = "enrichment_cache"

    # ── Primary key ──────────────────────────────────────────
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # ── Foreign key ──────────────────────────────────────────
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), index=True
    )

    # ── Enrichment source ────────────────────────────────────
    apollo_org_id: Mapped[Optional[str]] = mapped_column(Text, index=True)
    
    # ── Company data ─────────────────────────────────────────
    employee_count: Mapped[Optional[str]] = mapped_column(Text)
    founded_year: Mapped[Optional[int]] = mapped_column()
    revenue_range: Mapped[Optional[str]] = mapped_column(Text)
    technologies: Mapped[list] = mapped_column(ARRAY(Text), default=list)

    # ── Raw response ─────────────────────────────────────────
    raw_response: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # ── Metadata ─────────────────────────────────────────────
    enriched_by: Mapped[Optional[str]] = mapped_column(Text)
    enriched_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # ── Indexes (declarative) ────────────────────────────────
    __table_args__ = (
        Index("ix_enrichment_cache_company_id", company_id),
    )
