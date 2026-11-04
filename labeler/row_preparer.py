"""Clean rows before sending: skip empty, trim long, and send duplicate texts only once."""
from collections.abc import Sequence

from labeler.models import PreparedRows
from labeler.prompt_builder import sanitize_text


def prepare_rows(texts: Sequence[object], max_chars: int) -> PreparedRows:
    """Sanitise, trim and de-duplicate row texts.

    Identical texts (e.g. many "N/A" answers) map to one entry in unique_texts,
    so each is paid for once.
    """
    unique_texts: list[str] = []
    position_of: dict[str, int] = {}
    row_to_unique: list[int | None] = []
    trimmed: set[int] = set()

    for row, raw in enumerate(texts):
        text = sanitize_text("" if raw is None else str(raw))
        if not text:
            row_to_unique.append(None)
            continue
        if len(text) > max_chars:
            text = text[:max_chars]
            trimmed.add(row)
        if text not in position_of:
            position_of[text] = len(unique_texts)
            unique_texts.append(text)
        row_to_unique.append(position_of[text])

    return PreparedRows(unique_texts, row_to_unique, frozenset(trimmed))
