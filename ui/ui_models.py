"""Types for the interface state. Types only: no logic lives here."""
from dataclasses import dataclass

import pandas as pd

from labeler.models import RunResult


@dataclass
class AppState:
    """Everything the app remembers between clicks (lives in st.session_state)."""
    df: pd.DataFrame | None = None
    file_id: str = ""                    # detects a new upload
    file_name: str = ""
    text_column: str | None = None
    result: RunResult | None = None      # last completed run
    result_name: str = ""                # output column name used for that run
    result_query: str = ""               # query text used for that run
    session_spend_usd: float = 0.0
