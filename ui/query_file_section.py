"""Save the query list as JSON, or load one to reuse on a new CSV (small, for the bottom bar)."""
import streamlit as st

from labeler.errors import QueryFileError
from labeler.query_store import queries_from_json, queries_to_json
from ui.query_actions import free_column_name
from ui.ui_models import AppState

_LOADED_KEY = "loaded_query_file_id"
_MESSAGE_KEY = "query_file_message"


def render(state: AppState) -> None:
    """Draw the small Save queries button and the Load queries menu."""
    st.download_button("Save queries", data=queries_to_json(state.queries), icon=":material/save:",
                       file_name="queries.json", mime="application/json", key="save_queries",
                       disabled=not state.queries, help="Save the queries as a .json file to reuse later.")
    with st.popover("Load queries", icon=":material/upload_file:"):
        uploaded = st.file_uploader("Load queries (.json)", type=["json"], key="load_queries")
    _show_message()
    if uploaded is None or uploaded.file_id == st.session_state.get(_LOADED_KEY):
        return
    st.session_state[_LOADED_KEY] = uploaded.file_id   # load each file once
    try:
        loaded = queries_from_json(uploaded.getvalue().decode("utf-8-sig"))
    except (QueryFileError, UnicodeDecodeError) as exc:
        st.session_state[_MESSAGE_KEY] = ("error", f"Could not load queries: {exc}")
        st.rerun()
    for query in loaded:
        query.name = free_column_name(state, query.name)
        state.queries.append(query)
    st.session_state[_MESSAGE_KEY] = ("success", f"Loaded {len(loaded)} queries as 'Not run'. "
                                                 "Nothing runs automatically.")
    st.rerun()


def _show_message() -> None:
    """Show the result of the last load once, as a toast (the bar has no room for boxes)."""
    message = st.session_state.pop(_MESSAGE_KEY, None)
    if message:
        kind, text = message
        st.toast(text, icon=":material/error:" if kind == "error" else ":material/check_circle:")
