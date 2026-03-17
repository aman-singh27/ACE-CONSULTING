"""
Text normalization for titles and company names to improve match rates.
"""

import re


def normalize_company(name: str | None) -> str:
    """Normalize a company name for fuzzy matching and deduplication."""
    if not name:
        return ""

    # 1. Lowercase and strip
    name = name.lower().strip()

    # 2. Keep only alphanumeric and whitespace
    name = re.sub(r"[^a-z0-9\s]", "", name)

    # 3. Remove common corporate entity suffixes
    # Assumes words as boundaries
    name = re.sub(r"\b(llc|ltd|inc|corp|co|pvt|fze|wll)\b", "", name)

    # 4. Collapse multiple spaces into one
    name = re.sub(r"\s+", " ", name)

    return name.strip()


def normalize_title(title: str | None) -> str:
    """Normalize a job title for deduplication."""
    if not title:
        return ""

    # 1. Lowercase and strip
    title = title.lower().strip()

    # 2. Keep only alphanumeric and whitespace
    title = re.sub(r"[^a-z0-9\s]", "", title)

    # 3. Collapse multiple spaces into one
    title = re.sub(r"\s+", " ", title)

    return title.strip()
