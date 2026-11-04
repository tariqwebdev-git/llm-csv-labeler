# CLAUDE.md: LLM CSV Labeler

## What this is
A local Streamlit app for Alex Loewi (Upwork client). He uploads a CSV, picks a text column and writes plain-English yes/no queries. Each query adds `<name>` (1/0/blank), `<name>_conf` (0.50–1.00) and `<name>_note` (empty, trimmed, refused, blocked, failed) columns. Labels come from OpenAI in batches, and confidence comes from token logprobs.

- Developer: Tariq Saleem. Senior: Asad. Plan: `LLM CSV Labeler Development Plan Final.pdf` (Nov 4, 2026).
- Alex is on macOS Tahoe, so the README has macOS steps only.
- Main test case: the query "Mentions a person getting hit by a car or other vehicle" on the `transportation_open` column. **Near misses ("a car almost hit my son") count as 1.**

## Commands
```
python -m venv venv && venv/Scripts/pip install -r requirements.txt   # Windows dev (macOS: venv/bin/pip)
streamlit run app.py
python scripts/run_labeling_cli.py --help                             # headless run + accuracy check
pytest
python sample_data/make_sample.py                                      # regenerate synthetic data
```

## Architecture (full detail: docs/architecture.md)
- `app.py` + `ui/`: Streamlit only. They never call OpenAI, SQLite or the file system directly. They call `labeler.labeling_engine`.
- `labeler/`: core logic, with no Streamlit imports (so it can be reused by a future hosted version).
- `openai_client.py` is the only file that talks to OpenAI.
- Settings (model, prices, batch size, concurrency, limits) live only in `labeler/config.py`. Model: `gpt-4o-mini` (gpt-4.1-nano is deprecated).
- Tests use `tests/fake_classifier.py` (no API cost). Live checks use the CLI with `--limit`.

## Code rules
- One responsibility per file. Types go only in `models.py`, exceptions only in `errors.py`, settings only in `config.py`. Never mix them into logic files.
- File names describe their content.
- Clean, readable Python that Alex can maintain. Add a docstring to every public function, especially ones he may change.
- Prefer efficient approaches: deduplicate texts, cache, run concurrently, use short ids. Never break existing behaviour, and run `pytest` before merging.
- Never guess a label. A failure means a blank label plus a note.

## Security
- The API key lives only in `.env`. Never commit, log, print or show it.
- `.env`, `cache.db` and `output/` are in `.gitignore`.
- Alex's spend limit is low, so test with small files or `--limit`.

## Git workflow
`main` ← `staging` ← `dev` ← `feature/<name>`. Feature branches start from `dev` and merge back into `dev`. `dev` → `staging` is for Alex to test, and `staging` → `main` is for releases.

## Docs
`docs/milestone-N/pre-development.md` (the plan) and `post-development.md` (what was built and what is pending). Update both as milestones progress.

## Targets (beat the plan)
1,000 rows in under 30 s and under $0.01 per query. The plan's targets are under 2 minutes and a few cents.

## Status
See the latest `docs/milestone-*/post-development.md`.
