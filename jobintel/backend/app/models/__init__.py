"""
Models package – import all models so Alembic can detect them.
"""

from app.models.actor_config import ActorConfig  # noqa: F401
from app.models.actor_run import ActorRun  # noqa: F401
from app.models.company import Company  # noqa: F401
from app.models.company_contact import CompanyContact  # noqa: F401
from app.models.daily_insight import DailyInsight  # noqa: F401
from app.models.enrichment_cache import EnrichmentCache  # noqa: F401
from app.models.job_posting import JobPosting  # noqa: F401
from app.models.system_settings import SystemSettings  # noqa: F401
