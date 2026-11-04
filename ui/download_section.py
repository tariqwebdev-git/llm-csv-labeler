"""Step 4: download the original CSV with every completed query's columns added."""
import pandas as pd
import streamlit as st

from labeler.csv_io import labeled_filename, to_csv_bytes
from labeler.output_builder import add_result_columns
from ui.query_actions import completed_queries
from ui.ui_models import AppState


def labeled_table(state: AppState) -> pd.DataFrame:
    """Original rows and columns, plus 3 columns per Done / Done-with-errors query."""
    output = state.df
    for query in completed_queries(state):
        output = add_result_columns(output, query.name, state.full_runs[query.id].result.labels)
    return output


def render(state: AppState) -> None:
    st.header("4. Download")
    if state.df is None:
        st.caption("Upload a CSV first.")
        return
    included = [q.name for q in completed_queries(state)]
    st.caption(f"Includes: {', '.join(included)}" if included
               else "No query has been run yet. The download is the original file.")
    st.download_button("Download CSV", data=to_csv_bytes(labeled_table(state)),
                       file_name=labeled_filename(state.file_name), mime="text/csv", key="download_csv")
