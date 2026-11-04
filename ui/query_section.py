"""Step 2: write one query, see the estimated cost, run it, review the result."""
import pandas as pd
import streamlit as st

from labeler import config
from labeler.column_utils import suggest_column_name, to_column_name, unique_column_name
from labeler.errors import ApiConfigError, ApiKeyError
from labeler.labeling_engine import estimate_cost, run_query
from labeler.output_builder import CONFIDENCE_SUFFIX, add_result_columns
from ui.ui_models import AppState

QUERY_HINT = ("Write a full sentence describing what counts, e.g. 'Describes a person getting "
              "hurt in an accident, such as being hit by a vehicle'.")
_QUERY_KEY = "query_text"
_NAME_KEY = "query_name"


def _suggest_name() -> None:
    """When the query text changes, suggest a short column name."""
    st.session_state[_NAME_KEY] = suggest_column_name(st.session_state.get(_QUERY_KEY, ""))


def render(state: AppState, api_key: str | None) -> None:
    st.header("2. Query")
    query = st.text_area(
        "Query", key=_QUERY_KEY, on_change=_suggest_name,
        placeholder="e.g. Mentions a person getting hit by a car or other vehicle",
    ).strip()
    st.caption(QUERY_HINT)
    if query and len(query.split()) < config.QUERY_MIN_WORDS:
        st.warning("Short queries are often misread. Describe what counts in a full sentence, "
                   "and test on 20 rows first.")
    name = st.text_input("New column name (for results)", key=_NAME_KEY)

    if state.df is None or not state.text_column:
        st.info("Upload a CSV and choose a text column first.")
        return
    if not api_key:
        st.warning("Run is disabled until the API key is found.")

    texts = state.df[state.text_column].tolist()
    if query:
        estimate = estimate_cost(texts, query)
        st.caption(f"Estimated cost: ${estimate.cost_usd:.4f} for {estimate.rows_total:,} rows "
                   f"({estimate.rows_cached:,} already cached)")

    if st.button("Run", type="primary", disabled=not (api_key and query and name.strip())):
        _run(state, texts, query, name, api_key)

    if state.result is not None:
        _show_result(state, query)


def _run(state: AppState, texts: list, query: str, name: str, api_key: str) -> None:
    column_name = unique_column_name(to_column_name(name), set(state.df.columns))
    bar = st.progress(0.0, text="Starting...")
    try:
        result = run_query(
            texts, query, api_key=api_key,
            on_progress=lambda done, total: bar.progress(done / total, text=f"Batches {done}/{total}"),
        )
    except (ApiKeyError, ApiConfigError) as exc:
        bar.empty()
        st.error(str(exc))
        return
    state.result, state.result_name, state.result_query = result, column_name, query
    state.session_spend_usd += result.stats.cost_usd
    st.rerun()   # refresh sidebar spend and download with the new result


def _show_result(state: AppState, current_query: str) -> None:
    stats = state.result.stats
    if current_query != state.result_query:
        st.warning("The query has changed since the last run. Run again to update the results.")

    notes = ", ".join(f"{count} {note}" for note, count in stats.note_counts.items()) or "none"
    st.info(
        f"**{state.result_name}**: {stats.matched:,} of {stats.rows_total:,} matched, "
        f"{stats.not_labelled:,} not labelled  \n"
        f"Notes: {notes}  \n"
        f"Cost ${stats.cost_usd:.4f} · {stats.seconds}s · {stats.rows_from_cache:,} rows from cache"
    )
    st.caption("Lowest confidence first. Confidence close to 0.50 means the model was unsure.")
    st.dataframe(_preview(state))


def _preview(state: AppState) -> pd.DataFrame:
    table = add_result_columns(state.df[[state.text_column]], state.result_name, state.result.labels)
    confidence = pd.to_numeric(table[state.result_name + CONFIDENCE_SUFFIX], errors="coerce")
    order = confidence.sort_values(na_position="first").index
    return table.loc[order].head(config.RESULT_PREVIEW_ROWS)
