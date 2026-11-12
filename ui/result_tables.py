"""Shape results into tables for the cards (preview order, test split) and the sidebar filter."""
import pandas as pd

from labeler.models import Note, RowLabel
from labeler.output_builder import CONFIDENCE_SUFFIX, NOTE_SUFFIX, add_result_columns

_NEEDS_ATTENTION, _LABELLED, _EMPTY = 0, 1, 2


def full_preview(df: pd.DataFrame, column: str, name: str, labels: list[RowLabel], limit: int) -> pd.DataFrame:
    """Rows needing attention first, then labelled rows by lowest confidence, empty rows last."""
    table = add_result_columns(df[[column]], name, labels)
    group = [_EMPTY if r.note == Note.EMPTY else _LABELLED if r.label is not None else _NEEDS_ATTENTION
             for r in labels]
    order = pd.DataFrame({
        "group": group,
        "conf": pd.to_numeric(table[name + CONFIDENCE_SUFFIX], errors="coerce").to_numpy(),
    }, index=table.index).sort_values(["group", "conf"], na_position="last").index
    return table.loc[order].head(limit)


def split_test_rows(df: pd.DataFrame, column: str, name: str, row_indices: list[int],
                labels: list[RowLabel]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """(matched, unmatched, not labelled) rows of a test run."""
    rows = add_result_columns(df.iloc[row_indices][[column]], name, labels)
    matched = rows[rows[name] == "1"]
    unmatched = rows[rows[name] == "0"]
    not_labelled = rows[rows[name] == ""][[column, name + NOTE_SUFFIX]]
    return matched, unmatched, not_labelled


def query_rows(df: pd.DataFrame, column: str, name: str, labels: list[RowLabel],
               row_indices: list[int] | None = None) -> pd.DataFrame:
    """Text, label and confidence of one query's rows (all rows, or a test run's rows). Empty rows left out."""
    rows = df[[column]] if row_indices is None else df.iloc[row_indices][[column]]
    table = add_result_columns(rows, name, labels)
    table = table[table[name + NOTE_SUFFIX] != Note.EMPTY.value]
    return table[[column, name, name + CONFIDENCE_SUFFIX]]


def filter_rows(table: pd.DataFrame, name: str, show: str) -> pd.DataFrame:
    """show: 'all', 'matched' (1), 'not_matched' (0) or 'not_labelled' (blank)."""
    wanted = {"matched": "1", "not_matched": "0", "not_labelled": ""}.get(show)
    return table if wanted is None else table[table[name] == wanted]
