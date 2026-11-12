"""Small session info for the top-right corner: API key status (never the key), spend, settings menu."""
import streamlit as st

from labeler import config
from labeler.environment_check import running_in_project_env
from labeler.labeling_engine import clear_cache
from labeler.models import Provider
from labeler.provider_settings import PROVIDER_LABELS, api_key_env_var, model_for
from ui.ui_models import AppState

_PROVIDER_KEY = "provider_choice"
WRONG_ENV_WARNING = ("The app is not running from its own environment (.venv), so errors may occur. "
                     "Stop it (Ctrl+C) and start it with: `.venv/bin/python -m streamlit run app.py` "
                     "(see INSTALL-MAC.md).")


def render(state: AppState, api_key_found: bool) -> None:
    """Draw key status and spend (two short lines), plus a gear menu with the provider and Clear cache."""
    label = PROVIDER_LABELS[state.provider]
    status = (f":green[:material/check_circle: {label} key]" if api_key_found
              else f":red[:material/error: No {label} key]")
    with st.container(key="session_info", horizontal=True, gap="small", vertical_alignment="center"):
        # "\$" stops Streamlit reading text between two $ signs as a maths formula.
        st.markdown(f":small[{status}]  \n:small[Spent \\${state.session_spend_usd:.4f}]",
                    help="What this browser session has cost so far.", width="content")
        _settings_menu(state)


def _settings_menu(state: AppState) -> None:
    """Small gear menu: who answers LLM queries (OpenAI or Claude), and Clear cache."""
    with st.popover("", icon=":material/settings:", type="tertiary", help="Settings"):
        st.radio("AI for LLM queries", list(Provider), index=list(Provider).index(state.provider),
                 key=_PROVIDER_KEY, on_change=_set_provider, args=(state,),
                 format_func=lambda p: f"{PROVIDER_LABELS[p]} ({model_for(p)})",
                 help="Claude needs its own key in .env and gives labels without a confidence score for now. "
                      "Each AI keeps its own saved results.")
        if st.button("Clear cache", key="clear_cache",
                     help="Forget saved results. The next run of every query is charged again."):
            clear_cache()
            state.cache_version += 1
            st.toast("Cache cleared.")


def _set_provider(state: AppState) -> None:
    """Radio callback: runs before the page is redrawn, so the right key is loaded."""
    state.provider = st.session_state[_PROVIDER_KEY]


def render_warnings(state: AppState, api_key_found: bool) -> None:
    """Full-width warnings that must not be missed (shown under the top bar)."""
    if not api_key_found:
        st.error(f"{PROVIDER_LABELS[state.provider]} API key missing. "
                 f"Add {api_key_env_var(state.provider)}=... to the .env file, then restart.")
    if not running_in_project_env():
        st.warning(WRONG_ENV_WARNING)
