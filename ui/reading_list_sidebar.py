"""Sidebar reading list: the answers in the chosen text column, to keep reading.

Click the sidebar icon on a query card to see that query's rows here, matched
rows highlighted green (plus filter buttons if config.SIDEBAR_FILTER_BUTTONS).
The × goes back to all answers. Cells are white with dark text, for reading.
"""
import streamlit as st

from labeler import config
from labeler.column_utils import non_empty_answers
from labeler.models import Query
from ui.answer_table import READ_HINT, show_table, white_cells
from ui.query_actions import find_query
from ui.result_tables import filter_rows, query_rows
from ui.ui_models import AppState, QueryRun

FILTERS = {"All": "all", "Matched": "matched", "Not matched": "not_matched", "Not labelled": "not_labelled"}
_FILTER_KEY = "sidebar_filter"


def render(state: AppState) -> None:
    """Draw all answers of state.text_column, or the rows of the query picked on a card."""
    with st.sidebar:
        if state.df is None or state.text_column is None:
            st.caption("Upload a CSV. Its answers will be listed here for reading.")
            return
        query = find_query(state, state.sidebar_query_id) if state.sidebar_query_id else None
        run = _query_run(state, query)
        if query is not None and run is not None:
            _query_view(state, query, run)
        else:
            _all_answers(state)


def _query_run(state: AppState, query: Query | None) -> QueryRun | None:
    """The query's full run, else its test run (20 rows), else None."""
    if query is None:
        return None
    return state.full_runs.get(query.id) or state.test_runs.get(query.id)


def _all_answers(state: AppState) -> None:
    answers = non_empty_answers(state.df, state.text_column)
    shown = answers.head(config.READING_LIST_MAX_ROWS)
    more = f" (first {len(shown):,} shown)" if len(shown) < len(answers) else ""
    st.markdown(f"**{state.text_column}** · {len(answers):,} answers{more}")
    st.caption(f"{READ_HINT} Click the sidebar icon on a query card to see only its rows.")
    show_table(white_cells(shown.to_frame()), state.text_column, height=config.READING_LIST_HEIGHT_PX,
               text_width=config.READING_LIST_TEXT_WIDTH_PX)


def _query_view(state: AppState, query: Query, run: QueryRun) -> None:
    title, close = st.columns([8, 1], vertical_alignment="center")
    title.markdown(f"**{state.text_column}** · rows of **{query.name}**")
    if close.button("", icon=":material/close:", key="sidebar_clear", type="tertiary", help="Show all answers"):
        state.sidebar_query_id = None
        st.rerun()
    table = query_rows(state.df, state.text_column, query.name, run.result.labels, run.row_indices)
    choice = "All"
    if config.SIDEBAR_FILTER_BUTTONS:
        choice = st.segmented_control("Show", list(FILTERS), default="All", key=_FILTER_KEY,
                                      label_visibility="collapsed") or "All"
    shown = filter_rows(table, query.name, FILTERS[choice]).head(config.READING_LIST_MAX_ROWS)
    source = "test rows" if run.row_indices is not None else "rows"
    matched = int((table[query.name] == "1").sum())
    st.caption(f"{len(shown):,} shown · {matched:,} of {len(table):,} {source} matched. "
               f"Matched rows are green. {READ_HINT}")
    show_table(white_cells(shown, match_column=query.name), state.text_column,
               height=config.READING_LIST_HEIGHT_PX, text_width=config.READING_LIST_TEXT_WIDTH_PX)
