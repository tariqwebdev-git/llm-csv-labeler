"""One query card: name, wording, status, results box, and Edit / Test / Run / Delete."""
import pandas as pd
import streamlit as st

from labeler import config
from labeler.errors import ApiConfigError, ApiKeyError
from labeler.labeling_engine import estimate_cost, pick_test_rows, run_query
from labeler.models import CostEstimate, Query
from ui.query_actions import delete_query, record_run, record_test, update_query_text
from ui.result_tables import full_preview, split_test_rows
from ui.ui_models import AppState, QueryRun


@st.cache_data(show_spinner=False, max_entries=256)
def _estimate(file_id: str, column: str, query_text: str, cache_version: int, _texts: list) -> CostEstimate:
    """Cached per file/column/wording; cache_version changes after every run or cache clear."""
    return estimate_cost(_texts, query_text)


def render(state: AppState, query: Query, api_key: str | None) -> None:
    ready = state.df is not None and state.text_column is not None
    editing = st.session_state.get(_key("editing", query), False)

    with st.container(border=True):
        st.subheader(query.name)
        if editing:
            _editor(state, query)
        else:
            st.write(query.text)
        st.caption(f"Status: **{query.status.value}**")

        full = state.full_runs.get(query.id)
        if full:
            _stats_box(full)
        if ready and not editing:
            column = state.df[state.text_column]
            test_texts = column.iloc[pick_test_rows(len(column))].tolist()
            test_est = _estimate(f"{state.file_id}:test", state.text_column, query.text,
                                 state.cache_version, test_texts)
            full_est = _estimate(state.file_id, state.text_column, query.text,
                                 state.cache_version, column.tolist())
            st.caption(f"Estimate: test ${test_est.cost_usd:.4f} for {test_est.rows_total} rows · "
                       f"full run ${full_est.cost_usd:.4f} for {full_est.rows_total:,} rows "
                       f"({full_est.rows_cached:,} already cached)")

        _buttons(state, query, api_key, can_run=ready and bool(api_key) and not editing)
        _delete_confirmation(state, query)

        test = state.test_runs.get(query.id)
        if test and ready:
            _test_preview(state, query, test)
        if full and ready:
            with st.expander("Results: rows needing attention first, then lowest confidence"):
                st.caption("Confidence close to 0.50 means the model was unsure.")
                st.dataframe(full_preview(state.df, state.text_column, query.name,
                                          full.result.labels, config.RESULT_PREVIEW_ROWS))


def _key(kind: str, query: Query) -> str:
    return f"{kind}_{query.id}"


def _editor(state: AppState, query: Query) -> None:
    new_text = st.text_area("Edit query", value=query.text, key=_key("edit_text", query))
    save, cancel = st.columns(2)
    if save.button("Save", key=_key("save", query), type="primary"):
        update_query_text(state, query.id, new_text)
        st.session_state[_key("editing", query)] = False
        st.rerun()
    if cancel.button("Cancel", key=_key("cancel", query)):
        st.session_state[_key("editing", query)] = False
        st.rerun()


def _stats_box(run: QueryRun) -> None:
    stats = run.result.stats
    notes = ", ".join(f"{count} {note}" for note, count in stats.note_counts.items()) or "none"
    st.info(f"**{stats.matched:,} of {stats.rows_total:,} matched, {stats.not_labelled:,} not labelled**  \n"
            f"Notes: {notes}  \n"
            f"Cost ${stats.cost_usd:.4f} · {stats.seconds}s · {stats.rows_from_cache:,} rows from cache")


def _buttons(state: AppState, query: Query, api_key: str | None, can_run: bool) -> None:
    edit, test, run, delete = st.columns(4)
    if edit.button("Edit", key=_key("edit", query)):
        st.session_state[_key("editing", query)] = True
        st.rerun()
    if test.button("Test (20 rows)", key=_key("test", query), disabled=not can_run):
        _run(state, query, api_key, test_only=True)
    if run.button("Run", key=_key("run", query), disabled=not can_run, type="primary"):
        _run(state, query, api_key, test_only=False)
    if delete.button("Delete", key=_key("delete", query)):
        st.session_state[_key("confirm_delete", query)] = True
        st.rerun()


def _delete_confirmation(state: AppState, query: Query) -> None:
    if not st.session_state.get(_key("confirm_delete", query)):
        return
    st.warning(f"Delete query **{query.name}** and its results?")
    yes, no = st.columns(2)
    if yes.button("Yes, delete", key=_key("confirm_yes", query)):
        delete_query(state, query.id)
        st.session_state.pop(_key("confirm_delete", query), None)
        st.rerun()
    if no.button("Keep", key=_key("confirm_no", query)):
        st.session_state.pop(_key("confirm_delete", query), None)
        st.rerun()


def _run(state: AppState, query: Query, api_key: str, test_only: bool) -> None:
    column = state.df[state.text_column]
    indices = pick_test_rows(len(column)) if test_only else None
    texts = column.iloc[indices].tolist() if test_only else column.tolist()
    bar = st.progress(0.0, text="Starting...")
    try:
        result = run_query(
            texts, query.text, api_key=api_key,
            on_progress=lambda done, total: bar.progress(done / total, text=f"Batches {done}/{total}"),
        )
    except (ApiKeyError, ApiConfigError) as exc:
        bar.empty()
        st.error(str(exc))
        return
    run = QueryRun(result=result, query_text=query.text, row_indices=indices)
    (record_test if test_only else record_run)(state, query, run)
    state.cache_version += 1
    st.rerun()


def _test_preview(state: AppState, query: Query, test: QueryRun) -> None:
    matched, unmatched, not_labelled = split_test_rows(
        state.df, state.text_column, query.name, test.row_indices, test.result.labels)
    with st.expander(f"Test on {len(test.row_indices)} rows: {len(matched)} matched, "
                     f"{len(unmatched)} not matched · cost ${test.result.stats.cost_usd:.4f}", expanded=True):
        st.markdown("**Matched**")
        st.dataframe(_by_confidence(matched, query.name))
        st.markdown("**Not matched**")
        st.dataframe(_by_confidence(unmatched, query.name))
        if not not_labelled.empty:
            st.markdown("**Not labelled**")
            st.dataframe(not_labelled)


def _by_confidence(table: pd.DataFrame, name: str) -> pd.DataFrame:
    return table.sort_values(f"{name}_conf")
