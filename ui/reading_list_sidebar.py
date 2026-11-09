"""Sidebar reading list: the non-empty answers in the chosen text column, to keep reading."""
import streamlit as st

from labeler import config
from labeler.column_utils import non_empty_answers
from ui.answer_table import READ_HINT, show_table
from ui.ui_models import AppState


def render(state: AppState) -> None:
    """Draw the answers of state.text_column. They follow the column picked at the top."""
    with st.sidebar:
        if state.df is None or state.text_column is None:
            st.caption("Upload a CSV. Its answers will be listed here for reading.")
            return
        answers = non_empty_answers(state.df, state.text_column)
        shown = answers.head(config.READING_LIST_MAX_ROWS)
        more = f" (first {len(shown):,} shown)" if len(shown) < len(answers) else ""
        st.markdown(f"**{state.text_column}** · {len(answers):,} answers{more}")
        st.caption(READ_HINT)
        show_table(shown.to_frame(), state.text_column, height=config.READING_LIST_HEIGHT_PX,
                   text_width=config.READING_LIST_TEXT_WIDTH_PX)
