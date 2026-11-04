"""Types for the interface state. Types only: no logic lives here."""
from dataclasses import dataclass, field

import pandas as pd

from labeler.models import Query, RunResult


@dataclass
class QueryRun:
    """One finished test or full run of a query."""
    result: RunResult
    query_text: str                       # wording used, to detect later edits
    row_indices: list[int] | None = None  # rows used by a test run; None = all rows


@dataclass
class AppState:
    """Everything the app remembers between clicks (lives in st.session_state)."""
    df: pd.DataFrame | None = None
    file_id: str = ""                     # detects a new upload
    file_name: str = ""
    text_column: str | None = None
    queries: list[Query] = field(default_factory=list)
    full_runs: dict[str, QueryRun] = field(default_factory=dict)   # query id -> run
    test_runs: dict[str, QueryRun] = field(default_factory=dict)   # query id -> test
    session_spend_usd: float = 0.0
    cache_version: int = 0                # bumped when cached results change
