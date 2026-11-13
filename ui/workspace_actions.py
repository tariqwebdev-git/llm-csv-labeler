"""Each text column has its own queries and results (a workspace).

The active column's workspace lives in state.queries / full_runs / test_runs, so
the rest of the app works on it directly. Switching columns parks it and brings
back the other column's workspace. No Streamlit drawing here.
"""
from labeler.models import QueryStatus
from ui.query_actions import free_column_name, reset_results
from ui.ui_models import AppState, ColumnWorkspace


def switch_column(state: AppState, column: str) -> None:
    """Make `column` the active one: park the current workspace, restore (or start) the new one."""
    if column == state.text_column:
        return
    if state.text_column is not None:
        state.workspaces[state.text_column] = ColumnWorkspace(state.queries, state.full_runs, state.test_runs)
    target = state.workspaces.pop(column, None) or ColumnWorkspace()
    state.queries, state.full_runs, state.test_runs = target.queries, target.full_runs, target.test_runs
    state.text_column = column


def all_workspaces(state: AppState) -> dict[str, ColumnWorkspace]:
    """Every column's workspace (the active one included), keyed by column name."""
    workspaces = dict(state.workspaces)
    if state.text_column is not None:
        workspaces[state.text_column] = ColumnWorkspace(state.queries, state.full_runs, state.test_runs)
    return workspaces


def query_counts(state: AppState) -> dict[str, int]:
    """Number of queries per column, for the column picker."""
    return {column: len(ws.queries) for column, ws in all_workspaces(state).items() if ws.queries}


def reset_all_results(state: AppState) -> None:
    """New file: keep every column's queries, drop all results (they belonged to the old file)."""
    for workspace in state.workspaces.values():
        workspace.full_runs.clear()
        workspace.test_runs.clear()
        for query in workspace.queries:
            query.status = QueryStatus.NOT_RUN
            query.name = free_column_name(state, query.name, exclude_id=query.id)
    reset_results(state)
