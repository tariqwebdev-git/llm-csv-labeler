"""Changes to the app state for queries: add, edit, delete, record results.

No Streamlit drawing here, so these rules are easy to read and test.
"""
from labeler.column_utils import to_column_name
from labeler.models import Note, Query, QueryKind, QueryStatus, RunResult
from labeler.output_builder import result_column_names
from ui.ui_models import AppState, ColumnWorkspace, QueryRun

_ERROR_NOTES = {Note.REFUSED.value, Note.BLOCKED.value, Note.FAILED.value}
_COMPLETED = (QueryStatus.DONE, QueryStatus.DONE_WITH_ERRORS)


def find_query(state: AppState, query_id: str) -> Query | None:
    """The query with this id, or None."""
    return next((q for q in state.queries if q.id == query_id), None)


def free_column_name(state: AppState, wanted: str, exclude_id: str | None = None) -> str:
    """A name whose 3 output columns clash with no CSV column and no other query.

    Queries of every text column count, because all of them end up in one download.
    """
    taken = set(state.df.columns) if state.df is not None else set()
    parked = [q for ws in state.workspaces.values() for q in ws.queries]
    for q in state.queries + parked:
        if q.id != exclude_id:
            taken.update(result_column_names(q.name))
    base = to_column_name(wanted)
    candidate, n = base, 1
    while any(col in taken for col in result_column_names(candidate)):
        n += 1
        candidate = f"{base}_{n}"
    return candidate


def add_query(state: AppState, text: str, name: str, kind: QueryKind = QueryKind.LLM) -> Query:
    """Add a 'Not run' query (LLM or keyword) with a clash-free column name."""
    query = Query(name=free_column_name(state, name or text), text=text.strip(), kind=kind)
    state.queries.append(query)
    return query


def delete_query(state: AppState, query_id: str) -> None:
    """Remove a query and its results."""
    state.queries = [q for q in state.queries if q.id != query_id]
    state.full_runs.pop(query_id, None)
    state.test_runs.pop(query_id, None)


def update_query_text(state: AppState, query_id: str, text: str) -> None:
    """New wording (or new keywords): an old full result becomes Out of date; an old test is dropped."""
    query = find_query(state, query_id)
    text = text.strip()
    if query is None or not text or text == query.text:
        return
    query.text = text
    state.test_runs.pop(query_id, None)
    query.status = QueryStatus.OUT_OF_DATE if query_id in state.full_runs else QueryStatus.NOT_RUN


def record_test(state: AppState, query: Query, run: QueryRun) -> None:
    """Store a 20-row test result; status becomes Tested unless already Done."""
    state.test_runs[query.id] = run
    state.session_spend_usd += run.result.stats.cost_usd
    if query.status not in _COMPLETED:
        query.status = QueryStatus.TESTED


def record_run(state: AppState, query: Query, run: QueryRun) -> None:
    """Store a full-run result and set Done / Done with errors."""
    state.full_runs[query.id] = run
    state.session_spend_usd += run.result.stats.cost_usd
    query.status = status_after_run(run.result)


def status_after_run(result: RunResult) -> QueryStatus:
    """Done, or Done with errors if any row was refused, blocked or failed."""
    has_errors = any(note in _ERROR_NOTES for note in result.stats.note_counts)
    return QueryStatus.DONE_WITH_ERRORS if has_errors else QueryStatus.DONE


def reset_results(state: AppState) -> None:
    """New file or new text column: keep the queries, drop all results."""
    state.full_runs.clear()
    state.test_runs.clear()
    for query in state.queries:
        query.status = QueryStatus.NOT_RUN
        query.name = free_column_name(state, query.name, exclude_id=query.id)


def completed_queries(workspace: AppState | ColumnWorkspace) -> list[Query]:
    """Queries whose columns go into the download (of the active column, or of one workspace)."""
    return [q for q in workspace.queries if q.status in _COMPLETED and q.id in workspace.full_runs]
