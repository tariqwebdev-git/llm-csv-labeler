"""Sidebar: API key status (never the key itself), model and session spend."""
import streamlit as st

from labeler import config
from ui.ui_models import AppState


def render(state: AppState, api_key_found: bool) -> None:
    with st.sidebar:
        st.title("LLM CSV Labeler")
        if api_key_found:
            st.success("API key found")
        else:
            st.error(f"API key missing. Add {config.API_KEY_ENV_VAR}=... to the .env file, then restart.")
        st.caption(f"Model: `{config.MODEL}`")
        st.metric("Spend this session", f"${state.session_spend_usd:.4f}")
