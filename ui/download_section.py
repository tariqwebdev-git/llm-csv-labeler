"""Step 3: download the original CSV with the result columns added."""
import streamlit as st

from labeler.csv_io import labeled_filename, to_csv_bytes
from labeler.output_builder import add_result_columns
from ui.ui_models import AppState


def render(state: AppState) -> None:
    st.header("3. Download")
    if state.df is None:
        st.caption("Upload a CSV first.")
        return

    output = state.df
    if state.result is not None:
        output = add_result_columns(state.df, state.result_name, state.result.labels)
    else:
        st.caption("No query has been run yet. The download is the original file.")

    st.download_button(
        "Download CSV",
        data=to_csv_bytes(output),
        file_name=labeled_filename(state.file_name),
        mime="text/csv",
    )
