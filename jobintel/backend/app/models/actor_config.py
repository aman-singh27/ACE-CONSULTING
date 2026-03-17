"""
ActorConfig model – Apify actor scraper configurations.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Integer,
    Numeric,
    Text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.base import TimestampMixin


class ActorConfig(TimestampMixin, Base):
    __tablename__ = "actor_configs"

    # ── Primary key ──────────────────────────────────────────
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # ── Identity ─────────────────────────────────────────────
    actor_id: Mapped[str] = mapped_column(Text)
    actor_name: Mapped[Optional[str]] = mapped_column(Text)

    # ── Targeting ────────────────────────────────────────────
    platform: Mapped[Optional[str]] = mapped_column(Text)
    domain: Mapped[Optional[str]] = mapped_column(Text)

    keywords = mapped_column(ARRAY(Text), default=list)
    locations = mapped_column(ARRAY(Text), default=list)

    # ── Scheduling ───────────────────────────────────────────
    frequency_days: Mapped[int] = mapped_column(Integer, default=1)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    last_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    next_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # ── Budget ───────────────────────────────────────────────
    monthly_budget_usd: Mapped[Optional[float]] = mapped_column(Numeric)
    spend_mtd_usd: Mapped[float] = mapped_column(Numeric, default=0)

    alert_threshold_pct: Mapped[int] = mapped_column(Integer, default=80)

    # ── Config ───────────────────────────────────────────────
    apify_input_template = mapped_column(JSONB, nullable=True)

    normalizer_key: Mapped[Optional[str]] = mapped_column(Text)
