"""
System settings model for storing application configuration like API keys.
"""

from sqlalchemy import String, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.base import TimestampMixin


class SystemSettings(TimestampMixin, Base):
    """
    Key-value store for system configuration.
    
    Allows storing and retrieving application settings like API keys,
    without requiring environment file restarts.
    """

    __tablename__ = "system_settings"

    setting_key: Mapped[str] = mapped_column(
        String(255),
        primary_key=True,
        nullable=False,
        doc="Unique setting key (e.g., 'hubspot_api_key')",
    )
    setting_value: Mapped[str] = mapped_column(
        String(2048),
        nullable=False,
        doc="Setting value (encrypted sensitive values recommended)",
    )

    __table_args__ = (Index("idx_setting_key", "setting_key"),)

    def __repr__(self) -> str:
        return f"<SystemSettings key='{self.setting_key}'>"
