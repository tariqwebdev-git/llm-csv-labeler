"""Access the single AppState stored in Streamlit's session."""
import streamlit as st

from labeler.provider_settings import default_provider
from ui.ui_models import AppState

_STATE_KEY = "app_state"


def get_state() -> AppState:
    """The app state for this browser session (created on first use)."""
    if _STATE_KEY not in st.session_state:
        st.session_state[_STATE_KEY] = AppState(provider=default_provider())
    return st.session_state[_STATE_KEY]
