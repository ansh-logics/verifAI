"""
Utility functions for text processing and fuzzy matching.
"""

from __future__ import annotations

import re
from typing import Iterable


def tokenize(text: str) -> list[str]:
    """
    Tokenize text into lowercase words.

    Args:
        text: Input text to tokenize

    Returns:
        List of normalized tokens
    """
    if not text:
        return []

    # Lowercase and remove non-alphanumeric except + # . @ _ -
    text = text.lower()
    text = re.sub(r"[^a-z0-9+#.@_\-\s]", " ", text)

    # Split and filter empty
    tokens = [t.strip() for t in text.split() if t.strip()]

    return tokens


def normalize_token(token: str) -> str:
    """Normalize a single token."""
    return token.lower().strip()


def levenshtein_distance(s1: str, s2: str) -> int:
    """
    Calculate Levenshtein distance between two strings.

    Args:
        s1: First string
        s2: Second string

    Returns:
        Edit distance (number of single-character edits)
    """
    if len(s1) < len(s2):
        s1, s2 = s2, s1

    if len(s2) == 0:
        return len(s1)

    # Use only two rows
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            # j+1 instead of j since previous_row and current_row are one character longer
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


def find_fuzzy_matches(query_token: str, candidates: Iterable[str], max_distance: int = 2) -> list[str]:
    """
    Find fuzzy matches for a query token.

    Args:
        query_token: Token to find matches for
        candidates: Pool of candidate tokens
        max_distance: Maximum edit distance to consider

    Returns:
        List of fuzzy matching tokens
    """
    matches = []
    for candidate in candidates:
        distance = levenshtein_distance(query_token, candidate)
        if distance <= max_distance:
            matches.append(candidate)

    return matches


def extract_text_fields(*data_dicts) -> str:
    """
    Extract and concatenate text from multiple data dictionaries.

    Recursively traverses dicts/lists to find all string values.
    """
    texts = []

    for data in data_dicts:
        if data is None:
            continue
        if isinstance(data, str):
            texts.append(data)
        elif isinstance(data, dict):
            texts.extend(extract_text_fields(*data.values()))
        elif isinstance(data, (list, tuple)):
            texts.extend(extract_text_fields(*data))

    return " ".join(texts)


def normalize_name(name: str) -> str:
    """Normalize name for searching."""
    if not name:
        return ""
    return name.strip().lower()


def safe_get(data: dict, key: str, default=None):
    """Safely get value from dict with type checking."""
    if not isinstance(data, dict):
        return default
    return data.get(key, default)
