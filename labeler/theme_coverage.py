"""Which answers no query has matched yet (to spot themes that are still missing).

No Streamlit here: the sidebar's "No match yet" view calls this with the full runs
of the active column's queries.
"""
from collections.abc import Sequence

import pandas as pd

from labeler.column_utils import has_text
from labeler.models import RowLabel


def unmatched_answers(df: pd.DataFrame, column: str, label_lists: Sequence[Sequence[RowLabel]]) -> pd.Series:
    """The non-empty answers in `column` that got label 1 from none of the given runs.

    label_lists: one list of RowLabels per query (a full run: one label per row, same
    order as df). With no runs, every answer is returned. A blank label (failed,
    refused) is not a match, so that row stays in the list.
    """
    values = df[column]
    runs = [labels for labels in label_lists if len(labels) == len(values)]
    keep = [has_text(value) and not any(labels[row].label == 1 for labels in runs)
            for row, value in enumerate(values)]
    return values[keep]
