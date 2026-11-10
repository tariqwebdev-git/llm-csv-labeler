"""One way to show tables of answers: long text wraps, and a click shows all of it.

Used by the sidebar reading list, the data preview, test previews and results,
so every table of answers looks and behaves the same.
"""
import pandas as pd
import streamlit as st
from pandas.io.formats.style import Styler

from labeler import config

READ_HINT = "Long answers wrap. Double-click a cell to read the whole answer."


def show_table(df: pd.DataFrame | Styler, text_column: str | None, height: int | str = "auto",
               text_width: int = config.TABLE_TEXT_WIDTH_PX) -> None:
    """Draw df (or a styled df, e.g. with highlighted rows) with wrapped rows. The text
    column starts text_width pixels wide and stretches to fill any free space, so it
    never runs past the table's edge."""
    column_config = {}
    if text_column in df.columns:
        column_config[text_column] = st.column_config.TextColumn(text_column, width=text_width)
    st.dataframe(df, column_config=column_config, row_height=config.TABLE_ROW_HEIGHT_PX, height=height)
