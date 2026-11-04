"""Step 3: save the query list as JSON, or load one to reuse on a new CSV."""
import streamlit as st

from labeler.errors import QueryFileError
from labeler.query_store import queries_from_json, queries_to_json
from ui.query_actions import free_column_name
from ui.ui_models import AppState

_LOADED_KEY = "loaded_query_file_id"


def render(state: AppState) -> None:
    st.header("3. Save or load queries")
    if state.queries:
        st.download_button("Download queries (.json)", data=queries_to_json(state.queries),
                           file_name="queries.json", mime="application/json", key="save_queries")

    uploaded = st.file_uploader("Load queries (.json)", type=["json"], key="load_queries")
    if uploaded is None or uploaded.file_id == st.session_state.get(_LOADED_KEY):
        return
    st.session_state[_LOADED_KEY] = uploaded.file_id   # load each file once
    try:
        loaded = queries_from_json(uploaded.getvalue().decode("utf-8-sig"))
    except (QueryFileError, UnicodeDecodeError) as exc:
        st.error(f"Could not load queries: {exc}")
        return
    for query in loaded:
        query.name = free_column_name(state, query.name)
        state.queries.append(query)
    st.success(f"Loaded {len(loaded)} queries as 'Not run'. Nothing runs automatically.")
    st.rerun()
