"""Keyword queries: a row matches if its text contains any of the given words.

Runs locally: no API call, no cost, instant. Matching ignores upper/lower case.
"""
import re
from collections.abc import Sequence

from labeler.models import Note, RowLabel
from labeler.prompt_builder import sanitize_text

_SEPARATORS = re.compile(r"[,;\n]+")
_MATCH_CONFIDENCE = 1.0     # a keyword match is certain, not a guess


def parse_keywords(text: str) -> list[str]:
    """'car, Truck,, hit by' -> ['car', 'Truck', 'hit by']. Duplicates (any case) are dropped."""
    keywords: list[str] = []
    seen: set[str] = set()
    for part in _SEPARATORS.split(text):
        word = " ".join(part.split())
        if word and word.casefold() not in seen:
            seen.add(word.casefold())
            keywords.append(word)
    return keywords


def keyword_pattern(keywords: Sequence[str], whole_words: bool) -> re.Pattern:
    """One case-insensitive pattern for all keywords.

    whole_words=True: 'car' matches "my car" but not "scar". Phrases like 'hit by'
    match with any spacing between the words.
    """
    parts = [r"\s+".join(re.escape(piece) for piece in word.split())
             for word in sorted(keywords, key=len, reverse=True)]
    body = "|".join(parts)
    if whole_words:
        body = rf"(?<!\w)(?:{body})(?!\w)"
    return re.compile(body, re.IGNORECASE)


def match_keywords(texts: Sequence[object], keywords: Sequence[str], whole_words: bool) -> list[RowLabel]:
    """One RowLabel per text: 1 if any keyword is found, else 0. Empty rows get note 'empty'."""
    pattern = keyword_pattern(keywords, whole_words) if keywords else None
    labels: list[RowLabel] = []
    for value in texts:
        text = str(value)
        if not sanitize_text(text):
            labels.append(RowLabel(note=Note.EMPTY))
            continue
        found = bool(pattern and pattern.search(text))
        labels.append(RowLabel(label=int(found), confidence=_MATCH_CONFIDENCE))
    return labels
