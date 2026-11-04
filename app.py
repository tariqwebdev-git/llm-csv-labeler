"""LLM CSV Labeler: Streamlit entry point. Layout only; logic lives in labeler/ and ui/.

Run:  streamlit run app.py
"""
import streamlit as st

from labeler.api_key import load_api_key
from ui import download_section, query_section, sidebar, upload_section
from ui.session import get_state

st.set_page_config(page_title="LLM CSV Labeler", layout="wide")

state = get_state()
api_key = load_api_key()

sidebar.render(state, api_key_found=api_key is not None)
st.title("LLM CSV Labeler")
upload_section.render(state)
query_section.render(state, api_key)
download_section.render(state)
