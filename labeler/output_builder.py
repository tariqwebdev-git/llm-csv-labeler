"""Attach a query's results to the table as <name>, <name>_conf and <name>_note columns."""
import pandas as pd

from labeler.models import RowLabel

CONFIDENCE_SUFFIX = "_conf"
NOTE_SUFFIX = "_note"


def result_column_names(name: str) -> tuple[str, str, str]:
    return name, f"{name}{CONFIDENCE_SUFFIX}", f"{name}{NOTE_SUFFIX}"


def add_result_columns(df: pd.DataFrame, name: str, labels: list[RowLabel]) -> pd.DataFrame:
    """Return a copy of df with the 3 result columns appended. Blank = not labelled."""
    if len(labels) != len(df):
        raise ValueError(f"Got {len(labels)} labels for {len(df)} rows.")
    label_col, conf_col, note_col = result_column_names(name)
    out = df.copy()
    out[label_col] = ["" if r.label is None else str(r.label) for r in labels]
    out[conf_col] = ["" if r.confidence is None else f"{r.confidence:.2f}" for r in labels]
    out[note_col] = [r.note.value if r.note else "" for r in labels]
    return out
