"""
Hashing utilities for the deduplication engine.
"""

import hashlib


def sha256_hash(value: str) -> str:
    """Return the SHA-256 hex digest of a UTF-8 string."""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
