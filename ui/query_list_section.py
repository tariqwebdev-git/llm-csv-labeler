"""The query cards: the main part of the page."""
import streamlit as st

from ui import query_card
from ui.ui_models import AppState


def render(state: AppState, api_key: str | None) -> None:
    """Draw a short hint when needed, then one card per query."""
    if not state.queries:
        st.caption("No queries yet. Write one in the box at the top and click Add.")
        return
    if state.df is None:
        st.info("Upload a CSV to test or run queries.")
    elif not api_key:
        st.warning("LLM queries can't be tested or run until the API key is found. Keyword queries work without it.")
    for query in list(state.queries):
        query_card.render(state, query, api_key)
