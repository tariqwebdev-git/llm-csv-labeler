"""Load the page's custom CSS (fixed top and bottom bars, compact upload)."""
from pathlib import Path

import streamlit as st

_CSS_FILE = Path(__file__).with_name("page_style.css")


def apply() -> None:
    """Add page_style.css to the page. Call once, near the top of app.py."""
    st.html(f"<style>{_CSS_FILE.read_text(encoding='utf-8')}</style>")
