"""One way to show tables of answers: long text wraps, and a click shows all of it.

Used by the sidebar reading list, the data preview, test previews and results,
so every table of answers looks and behaves the same.
"""
import pandas as pd
import streamlit as st
from pandas.io.formats.style import Styler

from labeler import config

READ_HINT = "Long answers wrap. Double-click a cell to read the whole answer."
# Solid colours with dark text, so cells read well on the grey sidebar in light and dark mode.
_WHITE_CELL = "background-color: #ffffff; color: #31333f"
_MATCH_CELL = "background-color: #d9f2e1; color: #31333f"   # light green


def show_table(df: pd.DataFrame | Styler, text_column: str | None, height: int | str = "auto",
               text_width: int = config.TABLE_TEXT_WIDTH_PX) -> None:
    """Draw df (or a styled df, e.g. from white_cells) with wrapped rows. The text
    column starts text_width pixels wide and stretches to fill any free space, so it
    never runs past the table's edge."""
    column_config = {}
    if text_column in df.columns:
        column_config[text_column] = st.column_config.TextColumn(text_column, width=text_width)
    st.dataframe(df, column_config=column_config, row_height=config.TABLE_ROW_HEIGHT_PX, height=height)


def white_cells(df: pd.DataFrame, match_column: str | None = None) -> Styler:
    """White cells with dark text (easier to read on the grey sidebar).

    If match_column is given, rows where it is "1" are light green instead.
    """
    def row_style(row: pd.Series) -> list[str]:
        matched = match_column is not None and row[match_column] == "1"
        return [_MATCH_CELL if matched else _WHITE_CELL] * len(row)
    return df.style.apply(row_style, axis=1)
