"""One query card: collapsible header (name, status), wording, results, and Edit / Test / Run / Delete."""
import pandas as pd
import streamlit as st

from labeler import config
from labeler.errors import ApiConfigError, ApiKeyError
from labeler.labeling_engine import estimate_cost, pick_test_rows, run_keyword_query, run_query
from labeler.models import CostEstimate, Provider, Query, QueryKind
from labeler.provider_settings import uses_logprobs
from ui.answer_table import READ_HINT, show_table
from ui.query_actions import delete_query, record_run, record_test, update_query_text
from ui.result_tables import full_preview, split_test_rows
from ui.ui_models import AppState, QueryRun


@st.cache_data(show_spinner=False, max_entries=256)
def _estimate(file_id: str, column: str, query_text: str, cache_version: int, provider: Provider,
              _texts: list) -> CostEstimate:
    """Cached per file/column/wording/provider; cache_version changes after every run or cache clear."""
    return estimate_cost(_texts, query_text, provider=provider)


def render(state: AppState, query: Query, api_key: str | None) -> None:
    """Draw one query card. Collapsed, it shows only the name and status."""
    with st.container(border=True, key=_key("card", query)):
        collapsed = _header(state, query)
        if not collapsed:
            _body(state, query, api_key)


def _header(state: AppState, query: Query) -> bool:
    """Arrow + name + status + sidebar button on one line. Returns True if the card is collapsed."""
    collapsed_key = _key("collapsed", query)
    collapsed = st.session_state.get(collapsed_key, False)
    arrow, title, sidebar = st.columns([1, 28, 2], gap="small", vertical_alignment="center")
    if arrow.button("", key=_key("toggle", query), type="tertiary",
                    icon=":material/chevron_right:" if collapsed else ":material/expand_more:",
                    help="Show the card" if collapsed else "Collapse the card"):
        st.session_state[collapsed_key] = not collapsed
        st.rerun()
    tag = " &nbsp; :blue-badge[Keyword]" if _is_keyword(query) else ""
    title.markdown(f"**{query.name}**{_match_count(state, query)} &nbsp; "
                   f":small[:gray[{query.status.value}]]{tag}")
    _sidebar_button(state, query, sidebar)
    return collapsed


def _match_count(state: AppState, query: Query) -> str:
    """': 45 matches' after a full run, ': 4 of 20 test rows matched' after a test, else ''."""
    full = state.full_runs.get(query.id)
    if full:
        matched = full.result.stats.matched
        return f": {matched:,} {'match' if matched == 1 else 'matches'}"
    test = state.test_runs.get(query.id)
    if test:
        return f": {test.result.stats.matched} of {test.result.stats.rows_total} test rows matched"
    return ""


def _sidebar_button(state: AppState, query: Query, place) -> None:
    """Show (or stop showing) this query's rows in the sidebar. Needs a test or full run."""
    showing = state.sidebar_query_id == query.id
    has_results = query.id in state.full_runs or query.id in state.test_runs
    if place.button("", key=_key("sidebar", query), icon=":material/view_sidebar:",
                    type="primary" if showing else "tertiary", disabled=not has_results,
                    help="Stop showing in the sidebar" if showing else
                    "Show this query's rows in the sidebar" if has_results else "Test or run the query first"):
        state.sidebar_query_id = None if showing else query.id
        st.rerun()


def _body(state: AppState, query: Query, api_key: str | None) -> None:
    """Everything under the header: wording, estimate, buttons, test and results."""
    ready = state.df is not None and state.text_column is not None
    editing = st.session_state.get(_key("editing", query), False)

    keyword = _is_keyword(query)
    if editing:
        _editor(state, query)
    elif keyword:
        match = "whole words only" if query.whole_words else "also inside longer words"
        st.write(f"Rows containing any of: **{query.text}** :small[:gray[({match}, upper/lower case ignored)]]")
    else:
        st.write(query.text)

    full = state.full_runs.get(query.id)
    if full:
        _stats_box(full, keyword)
    if ready and not editing and keyword:
        st.caption("Free: keyword match, no API needed. Test and Run finish instantly.")
    elif ready and not editing:
        column = state.df[state.text_column]
        test_texts = column.iloc[pick_test_rows(len(column))].tolist()
        test_est = _estimate(f"{state.file_id}:test", state.text_column, query.text,
                             state.cache_version, state.provider, test_texts)
        full_est = _estimate(state.file_id, state.text_column, query.text,
                             state.cache_version, state.provider, column.tolist())
        no_conf = "" if uses_logprobs(state.provider) else " · Claude: confidence from its own rating plus re-checks of unsure rows"
        # "\$" stops Streamlit reading the text between two $ signs as a maths formula.
        st.caption(f"Estimate: test \\${test_est.cost_usd:.4f} for {test_est.rows_total} rows · "
                   f"full run \\${full_est.cost_usd:.4f} for {full_est.rows_total:,} rows "
                   f"({full_est.rows_cached:,} already cached){no_conf}")

    _buttons(state, query, api_key, can_run=ready and (keyword or bool(api_key)) and not editing)
    _delete_confirmation(state, query)

    test = state.test_runs.get(query.id)
    if test and ready:
        _test_preview(state, query, test)
    if full and ready:
        with st.expander("Results: rows needing attention first, then lowest confidence"):
            st.caption("Keyword matches are exact (confidence 1.00). " + READ_HINT if keyword else
                       f"Confidence close to 0.50 means the model was unsure. {READ_HINT}")
            show_table(full_preview(state.df, state.text_column, query.name,
                                    full.result.labels, config.RESULT_PREVIEW_ROWS), state.text_column)


def _key(kind: str, query: Query) -> str:
    return f"{kind}_{query.id}"


def _is_keyword(query: Query) -> bool:
    return query.kind == QueryKind.KEYWORD


def _editor(state: AppState, query: Query) -> None:
    whole_words = None
    if _is_keyword(query):
        new_text = st.text_input("Edit words (separated by commas)", value=query.text, key=_key("edit_text", query))
        whole_words = st.checkbox("Whole words only", value=query.whole_words, key=_key("edit_whole", query),
                                  help="On: 'car' does not match 'scar'. Off: it also matches inside longer words.")
    else:
        new_text = st.text_area("Edit query", value=query.text, key=_key("edit_text", query))
    save, cancel = st.columns(2)
    if save.button("Save", key=_key("save", query), type="primary"):
        update_query_text(state, query.id, new_text, whole_words)
        st.session_state[_key("editing", query)] = False
        st.rerun()
    if cancel.button("Cancel", key=_key("cancel", query)):
        st.session_state[_key("editing", query)] = False
        st.rerun()


def _stats_box(run: QueryRun, keyword: bool = False) -> None:
    stats = run.result.stats
    notes = ", ".join(f"{count} {note}" for note, count in stats.note_counts.items()) or "none"
    cost = (f"Free keyword match · {stats.seconds}s" if keyword else
            f"Cost \\${stats.cost_usd:.4f} · {stats.seconds}s · {stats.rows_from_cache:,} rows from cache")
    st.info(f"**{stats.matched:,} of {stats.rows_total:,} matched, {stats.not_labelled:,} not labelled**  \n"
            f"Notes: {notes}  \n{cost}")


def _buttons(state: AppState, query: Query, api_key: str | None, can_run: bool) -> None:
    with st.container(horizontal=True, gap="small"):   # buttons side by side, left-aligned
        edit = st.button("Edit", key=_key("edit", query))
        test = st.button("Test (20 rows)", key=_key("test", query), disabled=not can_run)
        run = st.button("Run", key=_key("run", query), disabled=not can_run, type="primary")
        delete = st.button("Delete", key=_key("delete", query))
    if edit:
        st.session_state[_key("editing", query)] = True
        st.rerun()
    if test or run:
        _run(state, query, api_key, test_only=test)
    if delete:
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
    if _is_keyword(query):
        result = run_keyword_query(texts, query.text, query.whole_words)
        run = QueryRun(result=result, query_text=query.text, row_indices=indices)
        (record_test if test_only else record_run)(state, query, run)
        st.rerun()
    bar = st.progress(0.0, text="Starting...")
    try:
        result = run_query(
            texts, query.text, api_key=api_key, provider=state.provider,
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
                     f"{len(unmatched)} not matched · cost \\${test.result.stats.cost_usd:.4f}", expanded=True):
        st.caption(READ_HINT)
        st.markdown("**Matched**")
        show_table(_by_confidence(matched, query.name), state.text_column)
        st.markdown("**Not matched**")
        show_table(_by_confidence(unmatched, query.name), state.text_column)
        if not not_labelled.empty:
            st.markdown("**Not labelled**")
            show_table(not_labelled, state.text_column)


def _by_confidence(table: pd.DataFrame, name: str) -> pd.DataFrame:
    return table.sort_values(f"{name}_conf")
