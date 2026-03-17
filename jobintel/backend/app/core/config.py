"""
Application configuration loaded from environment variables / .env file.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for the JobIntel API."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    # ── General ──────────────────────────────────────────────
    APP_NAME: str = "JobIntel"
    ENV: str = "development"

    # ── Database ─────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://jobintel:jobintel@localhost:5432/jobintel"

    # ── Auth / JWT ───────────────────────────────────────────
    JWT_SECRET: str = "supersecretkey"
    JWT_ALGORITHM: str = "HS256"

    # ── Admin bootstrap ──────────────────────────────────────
    ADMIN_EMAIL: str = "admin@jobintel.local"
    ADMIN_PASSWORD_HASH: str = "$2b$12$placeholder"

    # ── External services ────────────────────────────────────
    APIFY_TOKEN: str = "your_apify_token_here"
    WEBHOOK_SECRET: str = "supersecretwebhook"
    WEBHOOK_URL: str | None = None

    # ── Apollo ───────────────────────────────────────────────
    APOLLO_API_KEY: str = "your_apollo_api_key_here"
    APOLLO_BASE_URL: str = "https://api.apollo.io/v1"

settings = Settings()
