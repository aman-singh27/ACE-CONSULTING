"""
ActorRun model – individual scraping run records.
"""

import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ActorRun(Base):
    __tablename__ = "actor_runs"

    # ── Primary key ──────────────────────────────────────────
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # ── Relationships ────────────────────────────────────────
    actor_config_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("actor_configs.id"),
        index=True,
    )

    apify_run_id: Mapped[Optional[str]] = mapped_column(Text)

    # ── Run details ──────────────────────────────────────────
    run_date: Mapped[Optional[date]] = mapped_column(Date, index=True)
    status: Mapped[Optional[str]] = mapped_column(Text, index=True)

    # ── Counts ───────────────────────────────────────────────
    total_scraped: Mapped[int] = mapped_column(Integer, default=0)
    total_new: Mapped[int] = mapped_column(Integer, default=0)
    total_duplicates: Mapped[int] = mapped_column(Integer, default=0)
    total_cross_dupes: Mapped[int] = mapped_column(Integer, default=0)
    total_errors: Mapped[int] = mapped_column(Integer, default=0)

    # ── Cost ─────────────────────────────────────────────────
    compute_units_used: Mapped[Optional[float]] = mapped_column(Numeric)
    cost_usd: Mapped[Optional[float]] = mapped_column(Numeric)

    # ── Errors ───────────────────────────────────────────────
    error_log: Mapped[Optional[str]] = mapped_column(Text)

    # ── Timestamps ───────────────────────────────────────────
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
