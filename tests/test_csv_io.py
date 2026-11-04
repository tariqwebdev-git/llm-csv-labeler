import pandas as pd
import pytest

from labeler.csv_io import labeled_filename, read_csv, to_csv_bytes
from labeler.errors import CsvReadError


def test_excel_export_cp1252_semicolons():
    data = "id;answer\n1;caf\xe9 near the road\n2;N/A\n".encode("cp1252")
    df = read_csv(data)
    assert list(df.columns) == ["id", "answer"]
    assert df["answer"].tolist() == ["caf\xe9 near the road", "N/A"]   # N/A kept as text


def test_quotes_commas_and_line_breaks_round_trip():
    original = pd.DataFrame({"id": ["007", "2"], "text": ['He said "stop", then\nleft', "a, b"]})
    df = read_csv(to_csv_bytes(original))
    assert df.equals(original)                                           # ids not reformatted


def test_output_has_bom_for_excel():
    assert to_csv_bytes(pd.DataFrame({"a": ["x"]})).startswith(b"\xef\xbb\xbf")


@pytest.mark.parametrize("data", [b"", b"   \n", b"a,b\n"])
def test_unusable_files_rejected(data):
    with pytest.raises(CsvReadError):
        read_csv(data)


def test_labeled_filename():
    assert labeled_filename("answers.csv") == "answers_labeled.csv"
