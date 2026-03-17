"""
DailyInsight model – precomputed daily intelligence snapshots.
"""

import uuid
from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy import Date, DateTime, Integer
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DailyInsight(Base):
    __tablename__ = "daily_insights"

    # ── Primary key ──────────────────────────────────────────
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # ── Date ─────────────────────────────────────────────────
    insight_date: Mapped[date] = mapped_column(Date, unique=True)

    # ── JSONB insight blobs ──────────────────────────────────
    companies_spiking = mapped_column(JSONB, nullable=True)
    companies_struggling = mapped_column(JSONB, nullable=True)
    new_entrants = mapped_column(JSONB, nullable=True)
    ghost_posters = mapped_column(JSONB, nullable=True)
    salary_signals = mapped_column(JSONB, nullable=True)

    # ── Aggregates ───────────────────────────────────────────
    total_jobs_today: Mapped[Optional[int]] = mapped_column(Integer)
    total_companies_active_today: Mapped[Optional[int]] = mapped_column(Integer)

    # ── Computed ─────────────────────────────────────────────
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
