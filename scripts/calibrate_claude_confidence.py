"""Calibrate Claude's confidence score against hand-checked answers.

Runs the test queries of scripts/run_eval.py on sample_data/sample.csv with Claude
(about a few cents), groups the rows by raw confidence, and shows how often each
group is actually right. It then prints a CLAUDE_CONFIDENCE_CALIBRATION table to
paste into labeler/config.py, so that "0.80" means "about 80% of rows like this
are correct".

Needs ANTHROPIC_API_KEY in .env.  Usage:  python scripts/calibrate_claude_confidence.py
Re-run it after changing ANTHROPIC_MODEL or the vote-check settings.
"""
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd  # noqa: E402

from labeler import config  # noqa: E402
from labeler.api_key import load_api_key  # noqa: E402
from labeler.errors import LabelerError  # noqa: E402
from labeler.labeling_engine import run_query  # noqa: E402
from labeler.models import Provider  # noqa: E402
from run_eval import CASES  # noqa: E402

BANDS = [(0.5, 0.6), (0.6, 0.7), (0.7, 0.8), (0.8, 0.9), (0.9, 1.01)]
MIN_ROWS_PER_BAND = 30     # fewer rows than this: too few to trust, band skipped
MIN_TRUSTED_BANDS = 3      # fewer trusted bands than this: no table is suggested


def main() -> int:
    data = pd.read_csv(PROJECT_ROOT / "sample_data" / "sample.csv", dtype=str, keep_default_na=False)
    key = pd.read_csv(PROJECT_ROOT / "sample_data" / "sample_key.csv", dtype=str, keep_default_na=False)
    config.CLAUDE_CONFIDENCE_CALIBRATION = [(0.5, 0.5), (1.0, 1.0)]     # measure raw confidence
    pairs: list[tuple[float, bool]] = []
    total_cost = 0.0
    try:
        for case in CASES:
            texts = data[case.column or "transportation_open"].tolist()
            cache = Path(tempfile.mkdtemp(prefix="calibrate_")) / "cache.db"
            result = run_query(texts, case.query, api_key=load_api_key(Provider.ANTHROPIC),
                               provider=Provider.ANTHROPIC, cache_path=cache)
            total_cost += result.stats.cost_usd
            for expected, label in zip(key[case.key_column], result.labels):
                if expected and label.label is not None and label.confidence is not None:
                    pairs.append((label.confidence, int(expected) == label.label))
            print(f"{case.query[:60]}... done (${result.stats.cost_usd:.4f})")
    except LabelerError as exc:
        print(f"Error: {exc}")
        return 1

    print(f"\n{len(pairs)} scored rows, total cost ${total_cost:.4f}\n")
    print("Raw confidence | rows | actually right")
    table = [(0.5, 0.5)]
    trusted_bands = 0
    for low, high in BANDS:
        band = [ok for conf, ok in pairs if low <= conf < high]
        if not band:
            continue
        accuracy = sum(band) / len(band)
        print(f"  {low:.1f}-{min(high, 1.0):.1f}      | {len(band):4d} | {accuracy:.0%}")
        if len(band) >= MIN_ROWS_PER_BAND:
            trusted_bands += 1
            middle = round((low + min(high, 1.0)) / 2, 2)
            table.append((middle, round(max(accuracy, table[-1][1]), 2)))   # never decreasing
    table.append((1.0, table[-1][1]))
    if trusted_bands < MIN_TRUSTED_BANDS:
        print(f"\nNot enough rows in the lower bands to calibrate (each band needs {MIN_ROWS_PER_BAND}+ rows, "
              f"and {MIN_TRUSTED_BANDS}+ bands are needed). Keep CLAUDE_CONFIDENCE_CALIBRATION as it is: the raw "
              "scores already rank doubtful rows lowest. Re-run on a larger hand-checked file.")
        return 0
    print(f"\nPaste into labeler/config.py:\nCLAUDE_CONFIDENCE_CALIBRATION = {table}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
