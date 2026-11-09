"""Attach a query's results to the table as <name>, <name>_conf and <name>_note columns."""
import pandas as pd

from labeler.models import RowLabel

CONFIDENCE_SUFFIX = "_conf"
NOTE_SUFFIX = "_note"


def result_column_names(name: str) -> tuple[str, str, str]:
    """The 3 output column names for a query: name, name_conf, name_note."""
    return name, f"{name}{CONFIDENCE_SUFFIX}", f"{name}{NOTE_SUFFIX}"


def add_result_columns(df: pd.DataFrame, name: str, labels: list[RowLabel],
                       after: str | None = None) -> pd.DataFrame:
    """Return a copy of df with the 3 result columns added. Blank = not labelled.

    The columns go right after the column `after` (e.g. the text column, or the
    previous query's note column). Without `after` they go at the end.
    """
    if len(labels) != len(df):
        raise ValueError(f"Got {len(labels)} labels for {len(df)} rows.")
    label_col, conf_col, note_col = result_column_names(name)
    out = df.drop(columns=[label_col, conf_col, note_col], errors="ignore")   # re-run replaces
    position = out.columns.get_loc(after) + 1 if after is not None else len(out.columns)
    out.insert(position, label_col, ["" if r.label is None else str(r.label) for r in labels])
    out.insert(position + 1, conf_col, ["" if r.confidence is None else f"{r.confidence:.2f}" for r in labels])
    out.insert(position + 2, note_col, [r.note.value if r.note else "" for r in labels])
    return out
