"""
SQLAlchemy declarative base – all ORM models inherit from this.

Importing models here ensures Base.metadata knows about every table
when Alembic runs autogenerate.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


# ── Import all models so their tables are registered on Base.metadata ──
import app.models  # noqa: F401, E402
