"""Helpers for output column names and for picking the text column."""
import re

import pandas as pd

from labeler.prompt_builder import sanitize_text

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


def count_empty(df: pd.DataFrame, column: str) -> int:
    """Rows with no usable text in `column` (same rule as the labeller: these are skipped)."""
    return sum(1 for value in df[column] if not sanitize_text(str(value)))


def non_empty_answers(df: pd.DataFrame, column: str) -> pd.Series:
    """The rows of `column` that have text (same rule as count_empty), with their row numbers."""
    values = df[column]
    return values[[bool(sanitize_text(str(value))) for value in values]]


def column_with_fewest_empty(df: pd.DataFrame) -> str:
    """The column that has text in the most rows; ties go to the longest average text."""
    return min(df.columns, key=lambda col: (count_empty(df, col), -_average_length(df, col)))


def _average_length(df: pd.DataFrame, column: str) -> float:
    return df[column].astype(str).str.len().mean()


def guess_text_column(df: pd.DataFrame) -> str:
    """The column with the longest average text: most likely the free-text answers."""
    return max(df.columns, key=lambda col: _average_length(df, col))
