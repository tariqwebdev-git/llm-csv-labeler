# CLAUDE.md: LLM CSV Labeler

## What this is
A local Streamlit app for Alex Loewi (Upwork client). He uploads a CSV, picks a text column and writes plain-English yes/no queries. Each query adds `<name>` (1/0/blank), `<name>_conf` (0.50–1.00) and `<name>_note` (empty, trimmed, refused, blocked, failed) columns. Labels come from OpenAI in batches, and confidence comes from token logprobs.

- Developer: Tariq Saleem. Senior: Asad until Nov 2026; he left, and the new senior is new to the project and forwards client messages, so Tariq writes the client replies. Plan: `LLM CSV Labeler Development Plan Final.pdf` (Nov 4, 2026).
- Alex is on macOS Tahoe with conda always active; his install guide is `INSTALL-MAC.md` (macOS steps only).
- Main test case: the query "Mentions a person getting hit by a car or other vehicle" on the `transportation_open` column. **Near misses ("a car almost hit my son") count as 1.**

## Commands
```
python -m venv venv && venv/Scripts/pip install -r requirements.txt   # Windows dev (macOS: venv/bin/pip)
streamlit run app.py                                                  # Windows dev; Alex (macOS): .venv/bin/python -m streamlit run app.py
python scripts/run_labeling_cli.py --help                             # headless run + accuracy check
pytest
python sample_data/make_sample.py                                      # regenerate synthetic data
python sample_data/make_stress_sample.py && python scripts/run_stress_test.py   # 5k-row stress test (~$0.19, capped by --max-spend)
python scripts/run_eval.py [--model gpt-4o-mini]                             # accuracy of 4 queries vs hand keys (~$0.005)
```
Browser checks (Playwright + Edge, separate venv, layout/scroll/end-to-end): see `tools/browser_checks/README.md`.

## Architecture (full detail: docs/architecture.md)
- `app.py` + `ui/`: Streamlit only. They never call OpenAI, SQLite or the file system directly. They call `labeler.labeling_engine`.
- `labeler/`: core logic, with no Streamlit imports (so it can be reused by a future hosted version).
- `openai_client.py` is the only file that talks to OpenAI; `anthropic_client.py` the only one that talks to Anthropic (Claude, `claude-haiku-5-5`, no temperature, thinking disabled). Claude has no logprobs, so its confidence = its own 50-100 rating per row (scored prompt `prompt_builder.SCORED_SYSTEM_PROMPT`; OpenAI's prompt is byte-identical to before) + a vote check on rows under `VOTE_CHECK_BELOW` (`labeling_engine._vote_check`, `confidence_check.py`) + `CLAUDE_CONFIDENCE_CALIBRATION` from `scripts/calibrate_claude_confidence.py`. Provider choice: `classifier_factory.make_classifier`, `provider_settings` (model/prices/key per provider), gear menu in the UI.
- Keyword queries (`keyword_matcher.py`, `labeling_engine.run_keyword_query`): local, free, confidence 1.00, per-query whole-words checkbox. Each text column has its own workspace (`ui/workspace_actions.py`).
- `environment_check.py`: the sidebar warns when the app is not started from the project's own env (conda base broke Alex's first run: old `brotli` there crashes the OpenAI SDK's reply decoding). Setup commands use `uv pip install --python .venv` and `.venv/bin/python -m streamlit` so conda can't interfere.
- Settings (model, prices, batch size, concurrency, limits) live only in `labeler/config.py`. Model: **`gpt-6-luna` with `REASONING_EFFORT="none"`** (needed for logprobs). gpt-4o-mini/gpt-4o shut down 2027-01-14; gpt-4.1-nano already retired. Python **3.12+** (numpy pin); `requirements.txt` is pinned exactly.
- **Batches stay small (10 rows / 1,000 tokens)**: bigger batches make answers drift between items (see docs/milestone-2/post-development.md). Batching is planned in `batch_planner.py`.
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
`INSTALL-MAC.md` is Alex's step-by-step install guide (uv, no Python knowledge needed). Keep it in step with the README's Setup section and with any change to the start command.

## Targets (beat the plan)
1,000 rows in under 30 s and under $0.01 per query. The plan's targets are under 2 minutes and a few cents.

## UI
Query cards are the main focus; top and bottom bars stay fixed: the page is one window high and only the `query_area` container scrolls (flex layout in `ui/page_style.css`, selectors only `.st-key-*` / `data-testid`; sticky positioning was tried and was unreliable; **never put a "<" in that CSS**, Streamlit then drops the whole style block). `app.py` (layout only) + `ui/`: `ui_models.py` (AppState, QueryRun types), `session.py` (get_state), `page_style.py` (+ `.css`), `upload_section.py` (top bar: file + text column), `session_info.py` (top right: key status, spend, Settings with Clear cache; warnings), `query_form_section.py` (top bar: one-line add form), `data_preview_section.py` (collapsed preview + empty-row warnings), `query_actions.py` (state rules: add/edit/delete/record, no drawing), `result_tables.py` (preview order, test split), `answer_table.py` (all answer tables: wrapped rows, double-click for full text), `query_list_section.py` (cards), `query_card.py` (one collapsible card: Edit/Test/Run/Delete), `query_file_section.py` (bottom bar: save/load JSON), `download_section.py` (bottom bar; new columns go right after the text column), `reading_list_sidebar.py` (sidebar: non-empty answers of the chosen column). UI tests: `tests/test_app_ui.py` (AppTest + fake model). Browser checks: Playwright with Edge (`channel="msedge"`) in a scratch venv, not in requirements.

## Part 2 (add-ons) branch
Approved and paid by Alex on 2026-11-12 (Milestone 2, "Four additional features", $400). **Merged into `dev`** together with his 2 small requests (white sidebar cells, match count on cards) and the Claude confidence method (`docs/claude-confidence-method.md`). Sidebar is highlight-only (`SIDEBAR_FILTER_BUTTONS = False`). Build notes: `docs/milestone-3/`. **v1.1.0 waits for Alex's Claude key** (calibration + live check) before release.

## Status
**Read `docs/project-status.md` at the start of every session** (handover log, what Alex has, what we are waiting on, how to release a zip). Update it when anything is sent to Alex or decided. Build history: `docs/milestone-*/post-development.md`; acceptance: `docs/acceptance-checklist.md` (✅ done, ⏳ needs Alex).
