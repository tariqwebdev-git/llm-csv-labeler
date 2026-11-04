"""Step 2: add queries, then show each one as a card."""
import streamlit as st

from labeler import config
from labeler.column_utils import suggest_column_name
from ui import query_card
from ui.query_actions import add_query
from ui.ui_models import AppState

QUERY_HINT = ("Write a full sentence describing what counts, e.g. 'Describes a person getting "
              "hurt in an accident, such as being hit by a vehicle'.")
_TEXT_KEY = "new_query_text"
_NAME_KEY = "new_query_name"


def render(state: AppState, api_key: str | None) -> None:
    st.header("2. Queries")
    _add_form(state)

    if not state.queries:
        st.caption("No queries yet.")
        return
    if state.df is None:
        st.info("Upload a CSV to test or run queries.")
    elif not api_key:
        st.warning("Test and Run are disabled until the API key is found.")
    for query in list(state.queries):
        query_card.render(state, query, api_key)


def _add_form(state: AppState) -> None:
    text = st.text_area(
        "New query", key=_TEXT_KEY, on_change=_suggest_name,
        placeholder="e.g. Mentions a person getting hit by a car or other vehicle",
    ).strip()
    st.caption(QUERY_HINT)
    if text and len(text.split()) < config.QUERY_MIN_WORDS:
        st.warning("Short queries are often misread. Describe what counts in a full sentence, "
                   "and test on 20 rows first.")
    st.text_input("New column name (for results)", key=_NAME_KEY)
    st.button("Add query", key="add_query", on_click=_add, args=(state,), disabled=not text)


def _suggest_name() -> None:
    st.session_state[_NAME_KEY] = suggest_column_name(st.session_state.get(_TEXT_KEY, ""))


def _add(state: AppState) -> None:
    """Button callback: add the card and clear the form."""
    text = st.session_state.get(_TEXT_KEY, "").strip()
    if text:
        add_query(state, text, st.session_state.get(_NAME_KEY, ""))
        st.session_state[_TEXT_KEY] = ""
        st.session_state[_NAME_KEY] = ""
