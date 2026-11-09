"""Row count, empty-row warning and a collapsed preview of the uploaded file."""
import pandas as pd
import streamlit as st

from labeler import config
from labeler.column_utils import column_with_fewest_empty, count_empty
from ui.answer_table import show_table
from ui.ui_models import AppState


def render(state: AppState) -> None:
    """Draw the warnings (always visible) and the preview (collapsed by default)."""
    df = state.df
    if df is None:
        return
    if len(df) > config.SOFT_ROW_LIMIT:
        st.warning(f"More than {config.SOFT_ROW_LIMIT:,} rows. Check the estimated cost before running.")
    _warn_empty_rows(df, state.text_column)
    with st.expander(f"Data preview: {len(df):,} rows, {len(df.columns)} columns", expanded=False):
        st.caption(f"Columns: {', '.join(df.columns)}")
        show_table(df.head(config.PREVIEW_ROWS), state.text_column)


def _warn_empty_rows(df: pd.DataFrame, column: str) -> None:
    """Empty rows are skipped, so say so before anyone pays for a run."""
    empty = count_empty(df, column)
    if not empty:
        return
    message = f"{empty:,} of {len(df):,} rows are empty in `{column}`; they will not be labelled."
    if empty / len(df) > config.EMPTY_WARNING_SHARE:
        best = column_with_fewest_empty(df)
        hint = f" Column `{best}` has text in the most rows." if best != column else ""
        st.error(f"{message} Is this the right column?{hint}")
    else:
        st.warning(message)
