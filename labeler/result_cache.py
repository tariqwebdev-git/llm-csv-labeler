"""SQLite cache so an unchanged (model, prompt, query, text) is never paid for twice.

Only labelled rows are stored; refused/blocked/failed rows are retried next run.
Each write commits immediately (WAL mode), so closing the app mid-run cannot
corrupt the cache.
"""
import hashlib
import sqlite3
from collections.abc import Iterable
from pathlib import Path

from labeler import config
from labeler.models import RowLabel

_SQLITE_MAX_PARAMS = 900   # stay under SQLite's per-query variable limit
_SEPARATOR = "\x1f"


class ResultCache:
    def __init__(self, path: Path | None = None):
        """Open the cache file (config.CACHE_PATH unless another path is given)."""
        self._conn = sqlite3.connect(path or config.CACHE_PATH)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS results ("
            " key TEXT PRIMARY KEY, label INTEGER NOT NULL, confidence REAL)"
        )
        self._conn.commit()

    @staticmethod
    def make_key(model: str, system_prompt: str, criterion: str, text: str) -> str:
        """Hash of everything that can change the answer."""
        raw = _SEPARATOR.join((model, system_prompt, criterion.strip(), text))
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def get_many(self, keys: Iterable[str]) -> dict[str, RowLabel]:
        keys = list(keys)
        found: dict[str, RowLabel] = {}
        for start in range(0, len(keys), _SQLITE_MAX_PARAMS):
            chunk = keys[start:start + _SQLITE_MAX_PARAMS]
            placeholders = ",".join("?" * len(chunk))
            rows = self._conn.execute(
                f"SELECT key, label, confidence FROM results WHERE key IN ({placeholders})", chunk
            )
            for key, label, confidence in rows:
                found[key] = RowLabel(label=label, confidence=confidence)
        return found

    def put_many(self, items: dict[str, RowLabel]) -> None:
        """Store labelled rows; rows without a label are skipped."""
        rows = [(k, r.label, r.confidence) for k, r in items.items() if r.label is not None]
        if not rows:
            return
        self._conn.executemany(
            "INSERT OR REPLACE INTO results (key, label, confidence) VALUES (?, ?, ?)", rows
        )
        self._conn.commit()

    def clear(self) -> None:
        self._conn.execute("DELETE FROM results")
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "ResultCache":
        return self

    def __exit__(self, *exc_info) -> None:
        self.close()
