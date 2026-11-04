# Milestone 1: Pre-development (Days 1–2)

**Goal:** labelling works end to end and Alex can try a first version.

## Day 1: engine (no UI)
| # | Task | Files |
|---|---|---|
| 1 | Repo, branches, scaffold, `.gitignore`, `.env.example`, requirements | root |
| 2 | Settings, types, errors | `config.py`, `models.py`, `errors.py` |
| 3 | CSV read/write, column helpers | `csv_io.py`, `column_utils.py` |
| 4 | Prompts | `prompt_builder.py` |
| 5 | OpenAI client (async, logprobs, timeout, retries) | `openai_client.py` |
| 6 | Parsing and confidence | `response_parser.py` |
| 7 | Row prep, dedup, batches, recovery, refusals | `row_preparer.py`, `batch_runner.py` |
| 8 | Cache and cost | `result_cache.py`, `cost_estimator.py` |
| 9 | Public API and output columns | `labeling_engine.py`, `output_builder.py` |
| 10 | CLI run and accuracy check vs `sample_key.csv` | `scripts/run_labeling_cli.py` |
| 11 | Unit tests (mocked OpenAI) | `tests/` |
| 12 | Day 1 live checks: model supports logprobs, `0`/`1` comes back as its own token, ids map correctly | (live) |

## Day 2: first UI
- Upload, column picker (handles several text columns) and preview
- One query: create, run, progress bar
- Download CSV with label, confidence and note columns
- Short README (macOS)
- Progress update to Alex

## Test data
`sample_data/sample.csv` has 220 synthetic rows. It covers hits, near misses (expected 1), unrelated rows, abusive rows, empty rows, injection attempts and one long row. The answers are in `sample_key.csv`.

## Done when
- The CLI labels `sample.csv` with no crashes, and every row gets 1, 0, or blank plus a note.
- Accuracy and near-miss confidence are reported.
- `pytest` passes.
- The UI flow works for one query.
