"""
Normalizer registry – maps actor normalizer_key to the correct normalizer function.
"""

from typing import Any, Callable, Optional

from app.core.logging import get_logger
from app.schemas.standard_job import StandardJob
from app.services.normalizers.bayt_normalizer import normalize_bayt_job
from app.services.normalizers.linkedin_normalizer import normalize_linkedin_job
from app.services.normalizers.naukrigulf_normalizer import normalize_naukrigulf_job

logger = get_logger(__name__)

# Type alias for normalizer functions
NormalizerFn = Callable[[dict[str, Any], str, Optional[str]], StandardJob]

NORMALIZER_REGISTRY: dict[str, NormalizerFn] = {
    "linkedin": normalize_linkedin_job,
    "naukrigulf": normalize_naukrigulf_job,
    "bayt": normalize_bayt_job,
}


def get_normalizer(key: Optional[str]) -> Optional[NormalizerFn]:
    """Return the normalizer function for the given key, or None."""
    if not key:
        logger.warning("No normalizer key provided")
        return None

    normalizer = NORMALIZER_REGISTRY.get(key)
    if normalizer is None:
        logger.warning("No normalizer registered for key=%s", key)
    return normalizer
