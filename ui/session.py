"""Access the single AppState stored in Streamlit's session."""
import streamlit as st

from ui.ui_models import AppState

_STATE_KEY = "app_state"


def get_state() -> AppState:
    if _STATE_KEY not in st.session_state:
        st.session_state[_STATE_KEY] = AppState()
    return st.session_state[_STATE_KEY]
