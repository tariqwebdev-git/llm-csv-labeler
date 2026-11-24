"""The "No match yet" list: answers no query has matched (no API cost)."""
import pandas as pd

from labeler.models import Note, RowLabel
from labeler.theme_coverage import unmatched_answers

DF = pd.DataFrame({"answer": ["a car hit me", "", "late bus", "noisy street", "  "]})   # as read_csv gives them


def _labels(*values):
    return [RowLabel(note=Note.FAILED) if v is None else RowLabel(v, 1.0) for v in values]


def test_no_runs_lists_every_non_empty_answer():
    assert unmatched_answers(DF, "answer", []).tolist() == ["a car hit me", "late bus", "noisy street"]


def test_rows_matched_by_any_query_drop_out():
    hit = _labels(1, 0, 0, 0, 0)
    bus = _labels(0, 0, 1, 0, 0)
    assert unmatched_answers(DF, "answer", [hit]).tolist() == ["late bus", "noisy street"]
    assert unmatched_answers(DF, "answer", [hit, bus]).tolist() == ["noisy street"]


def test_blank_labels_are_not_matches():
    failed = _labels(None, 0, None, 0, 0)
    assert unmatched_answers(DF, "answer", [failed]).tolist() == ["a car hit me", "late bus", "noisy street"]


def test_keeps_row_numbers_for_the_table():
    assert unmatched_answers(DF, "answer", [_labels(1, 0, 0, 0, 0)]).index.tolist() == [2, 3]


def test_runs_of_another_length_are_ignored():
    assert len(unmatched_answers(DF, "answer", [_labels(1, 1)])) == 3
