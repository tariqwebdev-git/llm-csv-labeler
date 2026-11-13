"""Keyword queries: a row matches if its text contains any of the given words.

Rules (confirmed by Alex):
- Whole words only, upper/lower case ignored: "car" matches "Car", "car," "car." and
  "car's", but not "scar" or "carpet".
- Several words: a row matches if it contains any of them.
- A * at the end of a word matches every word that starts with it:
  "respect*" matches respect, respects, respected, respecting.
- Other special characters are matched literally, so they can't break the search.

Runs locally: no API call, no cost, instant.
"""
import re
from collections.abc import Sequence

from labeler.models import Note, RowLabel
from labeler.prompt_builder import sanitize_text

_SEPARATORS = re.compile(r"[,;\n]+")
_WILDCARD = "*"
_MATCH_CONFIDENCE = 1.0     # a keyword match is certain, not a guess


def parse_keywords(text: str) -> list[str]:
    """'car, Truck,, respect*' -> ['car', 'Truck', 'respect*']. Duplicates (any case) and a
    lone '*' are dropped."""
    keywords: list[str] = []
    seen: set[str] = set()
    for part in _SEPARATORS.split(text):
        word = " ".join(part.split())
        if word.rstrip(_WILDCARD) and word.casefold() not in seen:
            seen.add(word.casefold())
            keywords.append(word)
    return keywords


def keyword_pattern(keywords: Sequence[str]) -> re.Pattern:
    """One case-insensitive, whole-word pattern for all keywords.

    Each keyword is escaped, so characters like . + ( ) match literally. A trailing *
    becomes "any further letters". Phrases like "hit by" match with any spacing.
    """
    parts = []
    for word in sorted(keywords, key=len, reverse=True):
        starts_with = word.endswith(_WILDCARD)
        stem = word.rstrip(_WILDCARD).strip()
        body = r"\s+".join(re.escape(piece) for piece in stem.split())
        parts.append(body + (r"\w*" if starts_with else ""))
    return re.compile(rf"(?<!\w)(?:{'|'.join(parts)})(?!\w)", re.IGNORECASE)


def match_keywords(texts: Sequence[object], keywords: Sequence[str]) -> list[RowLabel]:
    """One RowLabel per text: 1 if any keyword is found, else 0. Empty rows get note 'empty'."""
    pattern = keyword_pattern(keywords) if keywords else None
    labels: list[RowLabel] = []
    for value in texts:
        text = str(value)
        if not sanitize_text(text):
            labels.append(RowLabel(note=Note.EMPTY))
            continue
        found = bool(pattern and pattern.search(text))
        labels.append(RowLabel(label=int(found), confidence=_MATCH_CONFIDENCE))
    return labels
