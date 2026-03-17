"""
EnrichmentCache model – cached Apollo / enrichment data per company.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class EnrichmentCache(Base):
    __tablename__ = "enrichment_cache"

    # ── Primary key ──────────────────────────────────────────
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # ── Company FK ───────────────────────────────────────────
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id"),
        unique=True,
    )

    # ── Apollo data ──────────────────────────────────────────
    apollo_org_id: Mapped[Optional[str]] = mapped_column(Text)
    raw_response = mapped_column(JSONB, nullable=True)
    contacts = mapped_column(JSONB, nullable=True)

    # ── Company info ─────────────────────────────────────────
    employee_count: Mapped[Optional[str]] = mapped_column(Text)
    founded_year: Mapped[Optional[int]] = mapped_column(Integer)
    revenue_range: Mapped[Optional[str]] = mapped_column(Text)
    technologies = mapped_column(ARRAY(Text), default=list)

    # ── Meta ─────────────────────────────────────────────────
    enriched_by: Mapped[Optional[str]] = mapped_column(Text)
    enriched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
