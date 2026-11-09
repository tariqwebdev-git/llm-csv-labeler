import pandas as pd

from labeler.models import Note, RowLabel
from labeler.output_builder import add_result_columns


def test_adds_three_columns_without_changing_original():
    df = pd.DataFrame({"text": ["a", "b", "c"]})
    labels = [RowLabel(1, 0.97), RowLabel(0, 0.5, Note.TRIMMED), RowLabel(note=Note.REFUSED)]
    out = add_result_columns(df, "kids", labels)
    assert list(df.columns) == ["text"]
    assert out["kids"].tolist() == ["1", "0", ""]
    assert out["kids_conf"].tolist() == ["0.97", "0.50", ""]
    assert out["kids_note"].tolist() == ["", "trimmed", "refused"]


def test_columns_inserted_right_after_given_column():
    df = pd.DataFrame({"id": ["1"], "text": ["a"], "other": ["x"]})
    out = add_result_columns(df, "q1", [RowLabel(1, 0.9)], after="text")
    out = add_result_columns(out, "q2", [RowLabel(0, 0.8)], after="q1_note")
    assert list(out.columns) == ["id", "text", "q1", "q1_conf", "q1_note", "q2", "q2_conf", "q2_note", "other"]


def test_without_after_columns_go_at_the_end():
    df = pd.DataFrame({"text": ["a"], "other": ["x"]})
    assert list(add_result_columns(df, "q", [RowLabel(1, 0.9)]).columns)[-3:] == ["q", "q_conf", "q_note"]
