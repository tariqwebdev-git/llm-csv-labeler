"""Read uploaded CSV bytes into a table and write the labelled table back out."""
import csv
import io
from pathlib import Path

import pandas as pd

from labeler.errors import CsvReadError

# Tried in order. utf-8-sig also reads plain UTF-8; cp1252 covers Excel exports.
_ENCODINGS = ("utf-8-sig", "cp1252")
_DELIMITERS = ",;\t"
_SNIFF_CHARS = 64_000
_RENAMED_HEADERS = "renamed_headers"   # key in DataFrame.attrs


def read_csv(data: bytes) -> pd.DataFrame:
    """Parse CSV bytes. Detects encoding and delimiter; every column is read as text.

    Raises CsvReadError with a plain message if the file is unusable.
    """
    text = _decode(data)
    if not text.strip():
        raise CsvReadError("The file is empty.")
    delimiter = _detect_delimiter(text[:_SNIFF_CHARS])
    try:
        df = pd.read_csv(
            io.StringIO(text),
            sep=delimiter,
            dtype=str,
            keep_default_na=False,   # keep "NA", "N/A" etc. as text, not empty
        )
    except (pd.errors.ParserError, pd.errors.EmptyDataError) as exc:
        raise CsvReadError(f"Could not read the CSV: {exc}") from exc

    if df.empty:
        raise CsvReadError("The file has a header but no data rows.")
    df.attrs[_RENAMED_HEADERS] = _renamed_headers(text, delimiter, list(df.columns))
    return df


def to_csv_bytes(df: pd.DataFrame) -> bytes:
    """UTF-8 with BOM so Excel shows special characters correctly.

    Headers pandas renamed on reading (a blank header becomes 'Unnamed: 0')
    are written back exactly as they were in the original file.
    """
    out = df.rename(columns=df.attrs.get(_RENAMED_HEADERS, {}))
    return out.to_csv(index=False).encode("utf-8-sig")


def labeled_filename(original_name: str) -> str:
    """'answers.csv' -> 'answers_labeled.csv'."""
    return f"{Path(original_name).stem}_labeled.csv"


def _renamed_headers(text: str, delimiter: str, columns: list[str]) -> dict[str, str]:
    """{pandas column name: original header} for headers pandas changed (e.g. blank ones)."""
    raw = next(csv.reader(io.StringIO(text), delimiter=delimiter))
    return {col: orig for col, orig in zip(columns, raw) if col != orig}


def _decode(data: bytes) -> str:
    for encoding in _ENCODINGS:
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise CsvReadError("Unknown text encoding. Save the file as UTF-8 CSV and retry.")


def _detect_delimiter(sample: str) -> str:
    try:
        return csv.Sniffer().sniff(sample, delimiters=_DELIMITERS).delimiter
    except csv.Error:
        return ","
