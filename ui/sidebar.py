"""Sidebar: API key status (never the key itself), model, session spend, clear cache."""
import streamlit as st

from labeler import config
from labeler.labeling_engine import clear_cache
from ui.ui_models import AppState


def render(state: AppState, api_key_found: bool) -> None:
    """Draw the sidebar."""
    with st.sidebar:
        st.title("LLM CSV Labeler")
        if api_key_found:
            st.success("API key found")
        else:
            st.error(f"API key missing. Add {config.API_KEY_ENV_VAR}=... to the .env file, then restart.")
        st.caption(f"Model: `{config.MODEL}`")
        st.metric("Spend this session", f"${state.session_spend_usd:.4f}")
        if st.button("Clear cache", key="clear_cache",
                     help="Forget saved results. The next run of every query is charged again."):
            clear_cache()
            state.cache_version += 1
            st.toast("Cache cleared.")
