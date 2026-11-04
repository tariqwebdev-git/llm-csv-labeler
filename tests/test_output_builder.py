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
