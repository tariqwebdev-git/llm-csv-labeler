"""Compact upload for the top bar: CSV file and text column on one line."""
import pandas as pd
import streamlit as st

from labeler.column_utils import guess_text_column
from labeler.csv_io import read_csv
from labeler.errors import CsvReadError
from ui.query_actions import reset_results
from ui.ui_models import AppState

_COLUMN_KEY = "text_column_select"


@st.cache_data(show_spinner="Reading CSV...")
def _parse_csv(data: bytes) -> pd.DataFrame:
    """Parsed once per file, so large files are not re-read on every click."""
    return read_csv(data)


def render(state: AppState) -> None:
    """Draw the file picker and the text column choice side by side."""
    file_col, column_col = st.columns([3, 2], gap="small", vertical_alignment="center")
    with file_col:
        uploaded = st.file_uploader("CSV file", type=["csv"], label_visibility="collapsed")
    if uploaded is None:
        if state.df is not None:
            state.df, state.file_id = None, ""
            reset_results(state)
        return

    if uploaded.file_id != state.file_id:
        try:
            df = _parse_csv(uploaded.getvalue())
        except CsvReadError as exc:
            st.error(str(exc))
            state.df, state.file_id = None, ""
            reset_results(state)
            return
        state.df, state.file_id, state.file_name = df, uploaded.file_id, uploaded.name
        state.text_column = guess_text_column(df)
        st.session_state[_COLUMN_KEY] = state.text_column
        reset_results(state)

    with column_col:
        column = st.selectbox("Text column", list(state.df.columns), key=_COLUMN_KEY,
                              help="The column with the answers to label.")
    if column != state.text_column:
        state.text_column = column
        reset_results(state)
