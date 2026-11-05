"""Acceptance: killing the app mid-run must not corrupt the cache (closing the browser tab)."""
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

_SLOW_RUN = """
import asyncio, sys
sys.path.insert(0, {root!r})
from labeler.labeling_engine import run_query
from tests.fake_classifier import FakeClassifier

class SlowFake(FakeClassifier):
    async def classify(self, *args, **kwargs):
        await asyncio.sleep(0.5)
        return await super().classify(*args, **kwargs)

texts = [f"answer number {{i}} hit" for i in range(400)]
run_query(texts, "hit by a vehicle", classifier=SlowFake(), cache_path={cache!r})
"""


def _saved_rows(cache: Path) -> int:
    try:
        with sqlite3.connect(cache) as conn:
            return conn.execute("SELECT COUNT(*) FROM results").fetchone()[0]
    except sqlite3.Error:
        return 0


def test_hard_kill_mid_run_leaves_cache_usable(tmp_path):
    cache = tmp_path / "cache.db"
    proc = subprocess.Popen([sys.executable, "-c", _SLOW_RUN.format(root=str(ROOT), cache=str(cache))])
    try:
        deadline = time.time() + 30
        while _saved_rows(cache) == 0 and time.time() < deadline:   # wait for the first saved batch
            time.sleep(0.1)
        assert proc.poll() is None, "run finished before it could be interrupted"
    finally:
        proc.kill()                                                  # like closing the app abruptly
        proc.wait()

    with sqlite3.connect(cache) as conn:
        assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        saved = conn.execute("SELECT COUNT(*) FROM results").fetchone()[0]
    assert 0 < saved < 400            # finished batches were kept; the rest will run next time
