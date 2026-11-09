"""Create Query form for the top bar: one line for the query, its column name and Add."""
import streamlit as st

from labeler import config
from labeler.column_utils import suggest_column_name
from ui.query_actions import add_query
from ui.ui_models import AppState

QUERY_PLACEHOLDER = ("New query: write a full sentence describing what counts, e.g. 'Mentions a person "
                     "getting hit by a car or other vehicle (near misses count)'")
_TEXT_KEY = "new_query_text"
_NAME_KEY = "new_query_name"


def render(state: AppState) -> None:
    """Draw the single-line add-query form."""
    text_col, name_col, add_col = st.columns([6, 2, 1], gap="small", vertical_alignment="bottom")
    text = text_col.text_input("New query", key=_TEXT_KEY, on_change=_suggest_name,
                               placeholder=QUERY_PLACEHOLDER, label_visibility="collapsed").strip()
    name_col.text_input("Column name", key=_NAME_KEY, placeholder="column name",
                        label_visibility="collapsed", help="Name of the new columns in the download.")
    add_col.button("Add", key="add_query", on_click=_add, args=(state,), disabled=not text,
                   type="primary", width="stretch", icon=":material/add:", help="Add the query as a card")
    if text and len(text.split()) < config.QUERY_MIN_WORDS:
        st.warning("Short queries are often misread. Describe what counts in a full sentence, "
                   "and test on 20 rows first.")


def _suggest_name() -> None:
    st.session_state[_NAME_KEY] = suggest_column_name(st.session_state.get(_TEXT_KEY, ""))


def _add(state: AppState) -> None:
    """Button callback: add the card and clear the form."""
    text = st.session_state.get(_TEXT_KEY, "").strip()
    if text:
        add_query(state, text, st.session_state.get(_NAME_KEY, ""))
        st.session_state[_TEXT_KEY] = ""
        st.session_state[_NAME_KEY] = ""
