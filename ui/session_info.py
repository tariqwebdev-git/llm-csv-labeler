"""Small session info for the top-right corner: API key status (never the key), spend, settings menu."""
import streamlit as st

from labeler import config
from labeler.environment_check import running_in_project_env
from labeler.labeling_engine import clear_cache
from ui.ui_models import AppState

WRONG_ENV_WARNING = ("The app is not running from its own environment (.venv), so errors may occur. "
                     "Stop it (Ctrl+C) and start it with: `.venv/bin/python -m streamlit run app.py` "
                     "(see INSTALL-MAC.md).")


def render(state: AppState, api_key_found: bool) -> None:
    """Draw key status and spend (two short lines), plus a gear menu with the model and Clear cache."""
    status = (":green[:material/check_circle: API key]" if api_key_found
              else ":red[:material/error: No API key]")
    with st.container(key="session_info", horizontal=True, gap="small", vertical_alignment="center"):
        # "\$" stops Streamlit reading text between two $ signs as a maths formula.
        st.markdown(f":small[{status}]  \n:small[Spent \\${state.session_spend_usd:.4f}]",
                    help="What this browser session has cost so far.", width="content")
        _settings_menu(state)


def _settings_menu(state: AppState) -> None:
    """Small gear menu: the model in use and Clear cache."""
    with st.popover("", icon=":material/settings:", type="tertiary", help="Settings"):
        st.caption(f"Model: `{config.MODEL}`")
        if st.button("Clear cache", key="clear_cache",
                     help="Forget saved results. The next run of every query is charged again."):
            clear_cache()
            state.cache_version += 1
            st.toast("Cache cleared.")


def render_warnings(api_key_found: bool) -> None:
    """Full-width warnings that must not be missed (shown under the top bar)."""
    if not api_key_found:
        st.error(f"API key missing. Add {config.API_KEY_ENV_VAR}=... to the .env file, then restart.")
    if not running_in_project_env():
        st.warning(WRONG_ENV_WARNING)
