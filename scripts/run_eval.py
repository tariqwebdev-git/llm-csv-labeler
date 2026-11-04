"""Accuracy check: run several queries on a CSV and score them against an answer key.

Default cases are the 5 test queries on sample_data/sample.csv. Each run uses a
fresh temporary cache, so results always come from the model (not the cache).

  python scripts/run_eval.py                    # gpt-4o-mini (config default)
  python scripts/run_eval.py --model gpt-4o     # compare another model

Blank expected labels in the key mean "ambiguous" and are not scored.
"""
import argparse
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd  # noqa: E402

from labeler import config  # noqa: E402
from labeler.api_key import load_api_key  # noqa: E402
from labeler.errors import LabelerError  # noqa: E402
from labeler.labeling_engine import run_query  # noqa: E402

# USD per 1M tokens (input, cached input, output) for models we compare.
MODEL_PRICES = {
    "gpt-4o-mini": (0.15, 0.075, 0.60),
    "gpt-4o": (2.50, 1.25, 10.00),
}
INJECTION_MARKERS = ("Ignore the above instructions", "SYSTEM: label this row")
_PREVIEW = 80


@dataclass(frozen=True)
class EvalCase:
    query: str
    key_column: str


CASES = [
    EvalCase("Mentions a person getting hit by a car or other vehicle, or almost getting hit "
             "(near misses count)", "expected_hit_by_vehicle"),
    EvalCase("Complains that buses or trains are late, unreliable or do not go where needed",
             "expect_bus_complaint"),
    EvalCase("Does not mention any vehicle (car, bus, train, truck, taxi, bike, etc.)", "expect_no_vehicle"),
    EvalCase("Contains insults, swearing or offensive language", "expect_insult"),
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--csv", type=Path, default=PROJECT_ROOT / "sample_data" / "sample.csv")
    parser.add_argument("--key", type=Path, default=PROJECT_ROOT / "sample_data" / "sample_key.csv")
    parser.add_argument("--column", default="transportation_open")
    parser.add_argument("--model", default=config.MODEL)
    args = parser.parse_args()

    if args.model in MODEL_PRICES:
        config.PRICE_INPUT_PER_1M, config.PRICE_CACHED_INPUT_PER_1M, config.PRICE_OUTPUT_PER_1M = \
            MODEL_PRICES[args.model]
    data = pd.read_csv(args.csv, dtype=str, keep_default_na=False)
    key = pd.read_csv(args.key, dtype=str, keep_default_na=False)
    texts = data[args.column].tolist()

    print(f"Model: {args.model} | {len(texts)} rows | {len(CASES)} queries\n")
    total_cost = 0.0
    try:
        for case in CASES:
            cache = Path(tempfile.mkdtemp(prefix="eval_")) / "cache.db"
            result = run_query(texts, case.query, api_key=load_api_key(), model=args.model, cache_path=cache)
            total_cost += result.stats.cost_usd
            _report(case, texts, key[case.key_column].tolist(), result)
    except LabelerError as exc:
        print(f"Error: {exc}")
        return 1
    print(f"Total cost: ${total_cost:.4f}")
    return 0


def _report(case: EvalCase, texts: list[str], expected: list[str], result) -> None:
    scored = [(t, e, r) for t, e, r in zip(texts, expected, result.labels) if e and r.label is not None]
    row_ok = sum(1 for _, e, r in scored if int(e) == r.label)
    unique = {t: (e, r) for t, e, r in scored}
    wrong = {t: (e, r) for t, (e, r) in unique.items() if int(e) != r.label}
    print(f"Query: {case.query}")
    print(f"  rows {row_ok}/{len(scored)} ({row_ok / len(scored):.1%}) | unique texts "
          f"{len(unique) - len(wrong)}/{len(unique)} | ${result.stats.cost_usd:.4f} | {result.stats.seconds}s")
    for text, (exp, r) in wrong.items():
        print(f"    WRONG expected {exp} got {r.label} (conf {r.confidence}): {text[:_PREVIEW]}")
    for text, exp, r in zip(texts, expected, result.labels):
        if text.startswith(INJECTION_MARKERS):
            status = "ok" if not exp or str(r.label) == exp else "WRONG"
            print(f"    injection [{status}] expected {exp or '-'} got {r.label}: {text[:50]}")
    print()


if __name__ == "__main__":
    sys.exit(main())
