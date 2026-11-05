"""Stress test: large file, matches only at the end, hard queries, long rows, cache.

Proves cost depends on row count and text length only, not on where matches
are or how hard the query is. Each scenario uses a fresh temporary cache.

  python sample_data/make_stress_sample.py         # generate data first
  python scripts/run_stress_test.py                # stops if estimate > --max-spend
"""
import argparse
import sys
import tempfile
from dataclasses import dataclass
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd  # noqa: E402

from labeler import config  # noqa: E402
from labeler.api_key import load_api_key  # noqa: E402
from labeler.errors import LabelerError  # noqa: E402
from labeler.labeling_engine import estimate_cost, run_query  # noqa: E402

DATA_CSV = PROJECT_ROOT / "sample_data" / "stress.csv"
KEY_CSV = PROJECT_ROOT / "sample_data" / "stress_key.csv"
RESULTS_MD = PROJECT_ROOT / "docs" / "milestone-1" / "stress-test-results.md"
TEXT_COLUMN = "transportation_open"


@dataclass(frozen=True)
class Scenario:
    id: str
    title: str
    query: str
    key_column: str
    long_rows_only: bool = False
    reuse_cache_of: str | None = None   # run against another scenario's cache


SCENARIOS = [
    Scenario("A", "5,000 rows, matches only in last 250",
             "Mentions a person getting hit by a car or other vehicle", "expect_hit"),
    Scenario("B", "Negation query",
             "Does NOT mention any vehicle (car, bus, train, truck, taxi, etc.)", "expect_no_vehicle"),
    Scenario("C", "Two-condition query",
             "A child was hurt AND the speaker blames the city", "expect_child_city"),
    Scenario("D", "300 long rows (~1,500 chars)",
             "Mentions a person getting hit by a car or other vehicle", "expect_hit", long_rows_only=True),
    Scenario("E", "Re-run A (cache)",
             "Mentions a person getting hit by a car or other vehicle", "expect_hit", reuse_cache_of="A"),
    Scenario("F", "A with one word changed",
             "Mentions someone getting hit by a car or other vehicle", "expect_hit", reuse_cache_of="A"),
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--max-spend", type=float, default=0.25, help="abort if total estimate is above this (USD)")
    args = parser.parse_args()

    if not DATA_CSV.exists():
        print("Run `python sample_data/make_stress_sample.py` first.")
        return 1
    data = pd.read_csv(DATA_CSV, dtype=str, keep_default_na=False)
    key = pd.read_csv(KEY_CSV)
    temp_dir = Path(tempfile.mkdtemp(prefix="stress_"))
    cache_of = {s.id: temp_dir / f"{s.reuse_cache_of or s.id}.db" for s in SCENARIOS}

    # 1. Estimate everything before spending anything.
    estimates = {}
    for s in SCENARIOS:
        texts, _ = _rows_for(s, data, key)
        repeat = s.reuse_cache_of and s.query == _scenario(s.reuse_cache_of).query
        estimates[s.id] = 0.0 if repeat else estimate_cost(texts, s.query, cache_path=cache_of[s.id]).cost_usd
    total = sum(estimates.values())
    print(f"Total estimated cost: ${total:.4f} (limit ${args.max_spend:.2f})")
    if total > args.max_spend:
        print("Above the limit. Nothing was sent.")
        return 1

    # 2. Run scenarios in order (E and F reuse A's cache).
    api_key = load_api_key()
    results = []
    try:
        for s in SCENARIOS:
            texts, expected = _rows_for(s, data, key)
            print(f"\n[{s.id}] {s.title}: {len(texts)} rows")
            run = run_query(texts, s.query, api_key=api_key, cache_path=cache_of[s.id],
                            on_progress=lambda d, t: print(f"\r  batches {d}/{t}", end="", flush=True))
            print()
            results.append(_summarise(s, run, expected, estimates[s.id], key))
            print("  " + " | ".join(f"{k}: {v}" for k, v in results[-1].items() if k not in ("Scenario", "Query")))
    except LabelerError as exc:
        print(f"\nError: {exc}")
        return 1

    _write_markdown(results)
    print(f"\nResults written to {RESULTS_MD}")
    return 0


def _scenario(scenario_id: str) -> Scenario:
    return next(s for s in SCENARIOS if s.id == scenario_id)


def _rows_for(s: Scenario, data: pd.DataFrame, key: pd.DataFrame) -> tuple[list[str], list[int]]:
    mask = key["is_long"] == 1 if s.long_rows_only else pd.Series(True, index=key.index)
    return data.loc[mask, TEXT_COLUMN].tolist(), key.loc[mask, s.key_column].tolist()


def _summarise(s: Scenario, run, expected: list[int], estimate: float, key: pd.DataFrame) -> dict:
    stats = run.stats
    labelled = [(e, r.label) for e, r in zip(expected, run.labels) if r.label is not None]
    correct = sum(1 for e, got in labelled if e == got)
    batches = -(-stats.texts_sent // config.BATCH_SIZE)
    diff = f"{(stats.cost_usd - estimate) / estimate:+.0%}" if estimate else "n/a"
    row = {
        "Scenario": f"{s.id}. {s.title}",
        "Query": s.query,
        "Rows": stats.rows_total,
        "Est $": f"{estimate:.4f}",
        "Actual $": f"{stats.cost_usd:.4f}",
        "Diff": diff,
        "$ / 1k rows": f"{stats.cost_usd / stats.rows_total * 1000:.4f}",
        "Time s": stats.seconds,
        "Requests (batches)": f"{stats.requests_sent} ({batches})",
        "Notes": ", ".join(f"{v} {k}" for k, v in stats.note_counts.items()) or "none",
        "Accuracy": f"{correct}/{len(labelled)} ({correct / len(labelled):.1%})" if labelled else "n/a",
    }
    if s.id == "A":
        tail = sum(1 for i, r in enumerate(run.labels) if i >= len(run.labels) - 250 and r.label == 1)
        head = sum(1 for i, r in enumerate(run.labels) if i < len(run.labels) - 250 and r.label == 1)
        row["Accuracy"] += f"; found {tail}/250 at end, {head} false positives before"
    return row


def _write_markdown(results: list[dict]) -> None:
    columns = list(results[0].keys())
    lines = [
        "# Stress test results",
        "",
        f"Date: {date.today()} · Model: `{config.MODEL}` · Batch size {config.BATCH_SIZE} · "
        f"Concurrency {config.MAX_CONCURRENT}",
        "",
        "Data: `sample_data/stress.csv` (5,000 unique rows; 250 matches only at the end; 300 long rows). "
        "Each scenario uses a fresh cache except E and F, which reuse A's.",
        "",
        "| " + " | ".join(columns) + " |",
        "|" + "---|" * len(columns),
    ]
    lines += ["| " + " | ".join(str(r[c]) for c in columns) + " |" for r in results]
    RESULTS_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
