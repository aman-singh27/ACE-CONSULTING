"""
Settings service for managing system configuration in the database.
"""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.system_settings import SystemSettings


async def get_setting(db: AsyncSession, setting_key: str) -> Optional[str]:
    """
    Retrieve a setting value from the database.
    Returns None if not found.
    """
    result = await db.execute(
        select(SystemSettings.setting_value).where(
            SystemSettings.setting_key == setting_key
        )
    )
    value = result.scalar_one_or_none()
    return value


async def set_setting(db: AsyncSession, setting_key: str, setting_value: str) -> None:
    """
    Create or update a setting in the database.
    """
    # Check if setting exists
    existing = await db.execute(
        select(SystemSettings).where(SystemSettings.setting_key == setting_key)
    )
    setting = existing.scalar_one_or_none()
    
    if setting:
        setting.setting_value = setting_value
    else:
        setting = SystemSettings(
            setting_key=setting_key,
            setting_value=setting_value,
        )
        db.add(setting)
    
    await db.commit()


async def delete_setting(db: AsyncSession, setting_key: str) -> bool:
    """
    Delete a setting from the database.
    Returns True if a setting was deleted, False otherwise.
    """
    result = await db.execute(
        select(SystemSettings).where(SystemSettings.setting_key == setting_key)
    )
    setting = result.scalar_one_or_none()
    
    if setting:
        db.delete(setting)
        await db.commit()
        return True

    return False
