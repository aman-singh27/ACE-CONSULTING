"""
CompanyContact model – people contacts at companies.
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
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
from app.models.base import TimestampMixin


class CompanyContact(TimestampMixin, Base):
    __tablename__ = "company_contacts"

    # ── Primary key ──────────────────────────────────────────
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # ── Foreign key ──────────────────────────────────────────
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), index=True
    )

    # ── Contact information ──────────────────────────────────
    full_name: Mapped[Optional[str]] = mapped_column(Text)
    title: Mapped[Optional[str]] = mapped_column(Text)
    email: Mapped[Optional[str]] = mapped_column(Text, index=True)
    phone: Mapped[Optional[str]] = mapped_column(Text)
    linkedin_url: Mapped[Optional[str]] = mapped_column(Text)

    # ── Classification ──────────────────────────────────────
    department: Mapped[Optional[str]] = mapped_column(Text)
    seniority: Mapped[Optional[str]] = mapped_column(Text)
    source: Mapped[Optional[str]] = mapped_column(Text)

    # ── HubSpot sync ─────────────────────────────────────────
    hubspot_contact_id: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, index=True
    )

    # ── Indexes (declarative) ────────────────────────────────
    __table_args__ = (
        Index("ix_company_contacts_company_id_seniority", company_id, seniority.desc()),
    )
