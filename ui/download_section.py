"""Download the original CSV with every completed query's columns added."""
import pandas as pd
import streamlit as st

from labeler.csv_io import labeled_filename, to_csv_bytes
from labeler.output_builder import NOTE_SUFFIX, add_result_columns
from ui.query_actions import completed_queries
from ui.ui_models import AppState


def labeled_table(state: AppState) -> pd.DataFrame:
    """Original rows and columns, plus 3 columns per Done / Done-with-errors query.

    The new columns go right after the text column they describe, in query order.
    """
    output, after = state.df, state.text_column
    for query in completed_queries(state):
        output = add_result_columns(output, query.name, state.full_runs[query.id].result.labels, after=after)
        after = query.name + NOTE_SUFFIX
    return output


def render(state: AppState) -> None:
    """Draw the small Download CSV button (for the bottom bar)."""
    if state.df is None:
        return
    included = [q.name for q in completed_queries(state)]
    st.download_button(
        "Download CSV", data=to_csv_bytes(labeled_table(state)), icon=":material/download:",
        file_name=labeled_filename(state.file_name), mime="text/csv", key="download_csv",
        type="primary",
        help=f"Original file plus the columns of: {', '.join(included)}" if included
        else "No query has been run yet, so this is the original file.",
    )
