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


def test_blank_header_survives_upload_and_download():
    from labeler.models import RowLabel
    from labeler.output_builder import add_result_columns
    df = read_csv(b'"","answer"\n"1","voter id"\n')
    out = add_result_columns(df, "q", [RowLabel(1, 0.9)])
    header = to_csv_bytes(out).decode("utf-8-sig").splitlines()[0]
    assert header == ',answer,q,q_conf,q_note'


def test_duplicate_headers_kept_on_download():
    df = read_csv(b"answer,answer\nfirst,second\n")
    assert len(df.columns) == 2
    header = to_csv_bytes(df).decode("utf-8-sig").splitlines()[0]
    assert header == "answer,answer"


def test_bom_only_file_rejected():
    with pytest.raises(CsvReadError):
        read_csv(b"\xef\xbb\xbf")
