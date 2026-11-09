"""LLM CSV Labeler: Streamlit entry point. Layout only; logic lives in labeler/ and ui/.

Run:  .venv/bin/python -m streamlit run app.py
"""
import sys

import streamlit as st

from labeler.python_version_check import python_too_old, python_version_message

# Checked first, before anything that needs a newer Python, so an old one gets a clear message.
if python_too_old():
    print(python_version_message(), file=sys.stderr)
    st.error(python_version_message())
    st.stop()

from labeler import config  # noqa: E402  (imported after the version check on purpose)
from labeler.api_key import load_api_key  # noqa: E402
from ui import (  # noqa: E402
    data_preview_section,
    download_section,
    page_style,
    query_file_section,
    query_form_section,
    query_list_section,
    reading_list_sidebar,
    session_info,
    upload_section,
)
from ui.session import get_state  # noqa: E402

st.set_page_config(page_title="LLM CSV Labeler", layout="wide",
                   initial_sidebar_state=config.SIDEBAR_WIDTH_PX)
page_style.apply()

state = get_state()
api_key = load_api_key()

# Top bar (stays in view): upload + text column, session info on the right, then Create Query.
with st.container(key="top_bar"):
    upload_col, info_col = st.columns([4, 1], gap="medium", vertical_alignment="center")
    with upload_col:
        upload_section.render(state)
    with info_col:
        session_info.render(state, api_key_found=api_key is not None)
    query_form_section.render(state)

# Query area: the only part of the page that scrolls (between the two bars).
with st.container(key="query_area"):
    session_info.render_warnings(api_key_found=api_key is not None)
    data_preview_section.render(state)
    query_list_section.render(state, api_key)

# Bottom bar (stays in view): small Save / Load queries and Download buttons.
with st.container(key="bottom_bar", horizontal=True, horizontal_alignment="right"):
    query_file_section.render(state)
    download_section.render(state)

reading_list_sidebar.render(state)
