"""Run one query on a CSV from the terminal, and optionally check accuracy against an answer key.

Example (small, cheap check first):
  python scripts/run_labeling_cli.py --csv sample_data/sample.csv \\
      --column transportation_open \\
      --query "Mentions a person getting hit by a car or other vehicle" \\
      --key sample_data/sample_key.csv --limit 20

The answer key must have the same rows in the same order as the CSV, with an
expected-label column (1/0/blank) and an optional 'category' column.
"""
import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd  # noqa: E402

from labeler import config  # noqa: E402
from labeler.api_key import load_api_key  # noqa: E402
from labeler.column_utils import suggest_column_name  # noqa: E402
from labeler.csv_io import labeled_filename, read_csv, to_csv_bytes  # noqa: E402
from labeler.errors import LabelerError  # noqa: E402
from labeler.labeling_engine import estimate_cost, run_query  # noqa: E402
from labeler.models import Provider, RowLabel  # noqa: E402
from labeler.provider_settings import model_for  # noqa: E402
from labeler.output_builder import add_result_columns  # noqa: E402

_TEXT_PREVIEW_CHARS = 90
_WATCH_CATEGORIES = ("near_miss", "abusive", "injection")


def main() -> int:
    args = _parse_args()
    try:
        df = read_csv(args.csv.read_bytes())
        if args.column not in df.columns:
            print(f"Column '{args.column}' not found. Columns: {', '.join(df.columns)}")
            return 1
        if args.limit:
            df = df.head(args.limit)
        texts = df[args.column].tolist()

        provider = Provider(args.provider)
        print(f"Provider: {provider.value} | model: {model_for(provider)}")
        estimate = estimate_cost(texts, args.query, provider=provider)
        print(f"Rows: {estimate.rows_total} | already cached: {estimate.rows_cached} | "
              f"unique texts to send: {estimate.texts_to_send}")
        print(f"Estimated cost: ${estimate.cost_usd:.4f} "
              f"({estimate.input_tokens} in / {estimate.output_tokens} out tokens)")
        if args.estimate_only:
            return 0

        result = run_query(
            texts, args.query, api_key=load_api_key(provider), provider=provider,
            on_progress=lambda done, total: print(f"\rBatches {done}/{total}", end="", flush=True),
        )
        print()
        _print_stats(result.stats, result.labels)

        name = args.name or suggest_column_name(args.query)
        output = add_result_columns(df, name, result.labels)
        out_path = PROJECT_ROOT / "output" / labeled_filename(args.csv.name)
        out_path.parent.mkdir(exist_ok=True)
        out_path.write_bytes(to_csv_bytes(output))
        print(f"Saved: {out_path}")

        if args.key:
            _check_accuracy(df[args.column], result.labels, args.key, args.key_column, len(df))
    except LabelerError as exc:
        print(f"\nError: {exc}")
        return 1
    return 0


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--csv", type=Path, required=True)
    parser.add_argument("--column", required=True, help="text column to label")
    parser.add_argument("--query", required=True)
    parser.add_argument("--name", help="output column name (default: suggested from query)")
    parser.add_argument("--limit", type=int, help="only the first N rows (keep test runs cheap)")
    parser.add_argument("--key", type=Path, help="answer key CSV for an accuracy check")
    parser.add_argument("--key-column", default="expected_hit_by_vehicle")
    parser.add_argument("--estimate-only", action="store_true", help="show cost, do not call the API")
    parser.add_argument("--provider", choices=[p.value for p in Provider], default=config.PROVIDER,
                        help="openai or anthropic (Claude: labels without a confidence score for now)")
    return parser.parse_args()


def _print_stats(stats, labels: list[RowLabel]) -> None:
    no_conf = sum(1 for r in labels if r.label is not None and r.confidence is None)
    print(f"Matched: {stats.matched} of {stats.rows_total} | not labelled: {stats.not_labelled} | "
          f"notes: {stats.note_counts or 'none'}")
    print(f"From cache: {stats.rows_from_cache} rows | texts sent: {stats.texts_sent} | "
          f"time: {stats.seconds}s | actual cost: ${stats.cost_usd:.5f}")
    print(f"Tokens: {stats.usage.input_tokens} in ({stats.usage.cached_input_tokens} cached) / "
          f"{stats.usage.output_tokens} out | requests: {stats.requests_sent} | labels without confidence: {no_conf}")


def _check_accuracy(texts: pd.Series, labels: list[RowLabel], key_path: Path, key_column: str, n_rows: int) -> None:
    key = pd.read_csv(key_path, dtype=str, keep_default_na=False).head(n_rows)
    expected = key[key_column].tolist()
    categories = key["category"].tolist() if "category" in key.columns else [""] * n_rows

    compared = correct = 0
    mismatches = []
    for i, (exp, got) in enumerate(zip(expected, labels)):
        if exp == "" or got.label is None:
            continue
        compared += 1
        if int(exp) == got.label:
            correct += 1
        else:
            mismatches.append(i)

    print(f"\nAccuracy: {correct}/{compared} labelled rows agree with the key"
          + (f" ({correct / compared:.1%})" if compared else ""))
    for i in mismatches:
        print(f"  MISMATCH row {i} [{categories[i]}] expected {expected[i]}, got {labels[i].label} "
              f"(conf {labels[i].confidence}): {_preview(texts.iloc[i])}")

    for category in _WATCH_CATEGORIES:
        rows = [i for i, c in enumerate(categories) if c == category]
        if not rows:
            continue
        print(f"\n{category} rows:")
        for i in rows:
            r = labels[i]
            print(f"  label={r.label} conf={r.confidence} note={r.note.value if r.note else ''}: "
                  f"{_preview(texts.iloc[i])}")


def _preview(text: str) -> str:
    text = str(text)
    return text if len(text) <= _TEXT_PREVIEW_CHARS else text[:_TEXT_PREVIEW_CHARS] + "..."


if __name__ == "__main__":
    sys.exit(main())
