"""Helpers for output column names and for picking the text column."""
import re

import pandas as pd

# Words dropped when suggesting a short column name from a query.
_STOP_WORDS = frozenset({
    "a", "an", "the", "of", "about", "that", "which", "who", "all", "any",
    "answers", "answer", "stories", "story", "mentions", "mention", "talk",
    "talks", "is", "are", "to", "or", "and", "in", "on", "by", "with", "other",
})
_MAX_SUGGESTED_WORDS = 3


def to_column_name(text: str) -> str:
    """Lowercase, spaces -> '_', only letters, numbers and '_'."""
    name = re.sub(r"\s+", "_", text.strip().lower())
    name = re.sub(r"[^a-z0-9_]", "", name)
    return re.sub(r"_+", "_", name).strip("_") or "query"


def unique_column_name(name: str, existing: set[str]) -> str:
    """Add _2, _3, ... until the name does not clash with `existing`."""
    if name not in existing:
        return name
    n = 2
    while f"{name}_{n}" in existing:
        n += 1
    return f"{name}_{n}"


def suggest_column_name(query_text: str) -> str:
    """'Mentions a person getting hit by a car' -> 'person_getting_hit'."""
    words = re.findall(r"[a-z0-9]+", query_text.lower())
    keywords = [w for w in words if w not in _STOP_WORDS]
    return to_column_name("_".join(keywords[:_MAX_SUGGESTED_WORDS]))


def guess_text_column(df: pd.DataFrame) -> str:
    """The column with the longest average text: most likely the free-text answers."""
    return max(df.columns, key=lambda col: df[col].astype(str).str.len().mean())
