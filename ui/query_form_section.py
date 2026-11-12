"""Create Query forms for the top bar: an LLM query or a keyword query, each on one line."""
import streamlit as st

from labeler import config
from labeler.column_utils import suggest_column_name
from labeler.models import QueryKind
from ui.query_actions import add_query
from ui.ui_models import AppState

QUERY_PLACEHOLDER = ("New query: write a full sentence describing what counts, e.g. 'Mentions a person "
                     "getting hit by a car or other vehicle (near misses count)'")
KEYWORD_PLACEHOLDER = "Words to look for, separated by commas, e.g. car, truck, bus, hit by"
_TEXT_KEY = "new_query_text"
_NAME_KEY = "new_query_name"
_KW_TEXT_KEY = "new_keyword_text"
_KW_NAME_KEY = "new_keyword_name"
_KW_WHOLE_KEY = "new_keyword_whole_words"


def render(state: AppState) -> None:
    """Draw the two tabs: New LLM Query and New Keyword Query."""
    llm_tab, keyword_tab = st.tabs(["New LLM Query", "New Keyword Query"])
    with llm_tab:
        _llm_form(state)
    with keyword_tab:
        _keyword_form(state)


def _llm_form(state: AppState) -> None:
    text_col, name_col, add_col = st.columns([6, 2, 1], gap="small", vertical_alignment="bottom")
    text = text_col.text_input("New query", key=_TEXT_KEY, on_change=_suggest_name, args=(_TEXT_KEY, _NAME_KEY),
                               placeholder=QUERY_PLACEHOLDER, label_visibility="collapsed").strip()
    name_col.text_input("Column name", key=_NAME_KEY, placeholder="column name",
                        label_visibility="collapsed", help="Name of the new columns in the download.")
    add_col.button("Add", key="add_query", on_click=_add_llm, args=(state,), disabled=not text,
                   type="primary", width="stretch", icon=":material/add:", help="Add the query as a card")
    if text and len(text.split()) < config.QUERY_MIN_WORDS:
        st.warning("Short queries are often misread. Describe what counts in a full sentence, "
                   "and test on 20 rows first.")


def _keyword_form(state: AppState) -> None:
    text_col, name_col, whole_col, add_col = st.columns([5, 2, 2, 1], gap="small", vertical_alignment="center")
    text = text_col.text_input("Keywords", key=_KW_TEXT_KEY, on_change=_suggest_name,
                               args=(_KW_TEXT_KEY, _KW_NAME_KEY), placeholder=KEYWORD_PLACEHOLDER,
                               label_visibility="collapsed").strip()
    name_col.text_input("Keyword column name", key=_KW_NAME_KEY, placeholder="column name",
                        label_visibility="collapsed", help="Name of the new columns in the download.")
    whole_col.checkbox("Whole words only", key=_KW_WHOLE_KEY, value=config.KEYWORD_WHOLE_WORDS_DEFAULT,
                       help="On: 'car' does not match 'scar'. Off: it also matches inside longer words. "
                            "Upper/lower case is always ignored.")
    add_col.button("Add", key="add_keyword_query", on_click=_add_keyword, args=(state,), disabled=not text,
                   type="primary", width="stretch", icon=":material/add:", help="Add the keyword query as a card")


def _suggest_name(text_key: str, name_key: str) -> None:
    st.session_state[name_key] = suggest_column_name(st.session_state.get(text_key, ""))


def _add_llm(state: AppState) -> None:
    """Button callback: add the LLM query card and clear the form."""
    text = st.session_state.get(_TEXT_KEY, "").strip()
    if text:
        add_query(state, text, st.session_state.get(_NAME_KEY, ""))
        st.session_state[_TEXT_KEY] = ""
        st.session_state[_NAME_KEY] = ""


def _add_keyword(state: AppState) -> None:
    """Button callback: add the keyword query card and clear the form."""
    text = st.session_state.get(_KW_TEXT_KEY, "").strip()
    if text:
        add_query(state, text, st.session_state.get(_KW_NAME_KEY, ""), kind=QueryKind.KEYWORD,
                  whole_words=st.session_state.get(_KW_WHOLE_KEY, config.KEYWORD_WHOLE_WORDS_DEFAULT))
        st.session_state[_KW_TEXT_KEY] = ""
        st.session_state[_KW_NAME_KEY] = ""
