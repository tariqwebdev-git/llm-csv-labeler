import pandas as pd

from labeler.models import QueryStatus, RowLabel, RunResult, RunStats, TokenUsage
from ui.download_section import labeled_table
from ui.query_actions import add_query, record_run
from ui.ui_models import AppState, QueryRun
from ui.workspace_actions import all_workspaces, query_counts, reset_all_results, switch_column


def _state() -> AppState:
    df = pd.DataFrame({"id": ["1", "2"], "a": ["x", "y"], "mid": ["m", "n"], "b": ["p", "q"]})
    state = AppState(df=df)
    switch_column(state, "a")
    return state


def _run(n: int = 2) -> QueryRun:
    stats = RunStats(n, n, 0, {}, 0, n, 1, TokenUsage(), 0.0, 0.1)
    return QueryRun(RunResult([RowLabel(1, 0.9)] * n, stats), "text")


def test_each_column_keeps_its_own_queries_and_results():
    state = _state()
    qa = add_query(state, "Query on a", "qa")
    record_run(state, qa, _run())
    switch_column(state, "b")
    assert state.queries == [] and state.full_runs == {}
    qb = add_query(state, "Query on b", "qb")
    switch_column(state, "a")
    assert state.queries == [qa] and qa.id in state.full_runs
    switch_column(state, "b")
    assert state.queries == [qb]


def test_names_unique_across_columns():
    state = _state()
    add_query(state, "First", "kids")
    switch_column(state, "b")
    assert add_query(state, "Second", "kids").name == "kids_2"


def test_download_puts_each_columns_queries_after_that_column():
    state = _state()
    record_run(state, add_query(state, "Query on a", "qa"), _run())
    switch_column(state, "b")
    record_run(state, add_query(state, "Query on b", "qb"), _run())
    assert list(labeled_table(state).columns) == [
        "id", "a", "qa", "qa_conf", "qa_note", "mid", "b", "qb", "qb_conf", "qb_note"]


def test_query_counts_and_new_file_reset():
    state = _state()
    qa = add_query(state, "Query on a", "qa")
    record_run(state, qa, _run())
    switch_column(state, "b")
    add_query(state, "Query on b", "qb")
    assert query_counts(state) == {"a": 1, "b": 1}
    reset_all_results(state)
    workspaces = all_workspaces(state)
    assert all(not ws.full_runs for ws in workspaces.values())
    assert qa.status == QueryStatus.NOT_RUN and len(workspaces["a"].queries) == 1
