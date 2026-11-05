import pandas as pd

from labeler.models import Note, QueryStatus, RowLabel, RunResult, RunStats, TokenUsage
from ui.query_actions import (
    add_query,
    completed_queries,
    delete_query,
    record_run,
    record_test,
    reset_results,
    update_query_text,
)
from ui.ui_models import AppState, QueryRun


def _run(notes: dict | None = None, cost: float = 0.01) -> QueryRun:
    stats = RunStats(1, 1, 0, notes or {}, 0, 1, 1, TokenUsage(), cost, 0.1)
    return QueryRun(RunResult([RowLabel(1, 0.9)], stats), "text")


def _state() -> AppState:
    return AppState(df=pd.DataFrame({"answer": ["a"], "kids_conf": ["x"]}), text_column="answer")


def test_add_query_avoids_clashes_with_csv_and_other_queries():
    state = _state()
    first = add_query(state, "Stories about children", "kids")
    second = add_query(state, "Other", "kids")
    assert first.name == "kids_2"                 # kids_conf already in the CSV
    assert second.name == "kids_3"


def test_status_flow_test_run_edit():
    state = _state()
    q = add_query(state, "Stories about children", "kids")
    record_test(state, q, _run())
    assert q.status == QueryStatus.TESTED
    record_run(state, q, _run())
    assert q.status == QueryStatus.DONE
    update_query_text(state, q.id, "Stories about kids")
    assert q.status == QueryStatus.OUT_OF_DATE
    assert q.id not in state.test_runs
    assert completed_queries(state) == []         # out of date: not in download
    assert round(state.session_spend_usd, 2) == 0.02


def test_errors_give_done_with_errors():
    state = _state()
    q = add_query(state, "x y z", "q")
    record_run(state, q, _run({Note.REFUSED.value: 2, Note.EMPTY.value: 1}))
    assert q.status == QueryStatus.DONE_WITH_ERRORS
    assert completed_queries(state) == [q]


def test_delete_and_reset():
    state = _state()
    a, b = add_query(state, "a b c", "a"), add_query(state, "d e f", "b")
    record_run(state, a, _run())
    delete_query(state, b.id)
    assert state.queries == [a]
    reset_results(state)
    assert a.status == QueryStatus.NOT_RUN and not state.full_runs
