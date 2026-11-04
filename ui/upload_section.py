"""Step 1: upload a CSV, preview it and choose the text column."""
import pandas as pd
import streamlit as st

from labeler import config
from labeler.column_utils import column_with_fewest_empty, count_empty, guess_text_column
from labeler.csv_io import read_csv
from labeler.errors import CsvReadError
from ui.session import clear_result
from ui.ui_models import AppState

_COLUMN_KEY = "text_column_select"


@st.cache_data(show_spinner="Reading CSV...")
def _parse_csv(data: bytes) -> pd.DataFrame:
    """Parsed once per file, so large files are not re-read on every click."""
    return read_csv(data)


def render(state: AppState) -> None:
    st.header("1. Upload CSV")
    uploaded = st.file_uploader("CSV file", type=["csv"])
    if uploaded is None:
        if state.df is not None:
            state.df, state.file_id = None, ""
            clear_result(state)
        return

    if uploaded.file_id != state.file_id:
        try:
            df = _parse_csv(uploaded.getvalue())
        except CsvReadError as exc:
            st.error(str(exc))
            state.df, state.file_id = None, ""
            clear_result(state)
            return
        state.df, state.file_id, state.file_name = df, uploaded.file_id, uploaded.name
        state.text_column = guess_text_column(df)
        st.session_state[_COLUMN_KEY] = state.text_column
        clear_result(state)

    df = state.df
    st.write(f"**{len(df):,} rows**, {len(df.columns)} columns: {', '.join(df.columns)}")
    if len(df) > config.SOFT_ROW_LIMIT:
        st.warning(f"More than {config.SOFT_ROW_LIMIT:,} rows. Check the estimated cost before running.")
    st.dataframe(df.head(config.PREVIEW_ROWS))

    column = st.selectbox("Text column to label", list(df.columns), key=_COLUMN_KEY)
    if column != state.text_column:
        state.text_column = column
        clear_result(state)
    _warn_empty_rows(df, column)


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
