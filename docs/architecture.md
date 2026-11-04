# Architecture: LLM CSV Labeler (v1)

Local Streamlit app. Upload a CSV, label one text column with plain-English yes/no queries using OpenAI, and download the CSV with new columns.

## 1. Layers

```
┌────────────────────────────────────────────────┐
│ UI (Streamlit)   app.py + ui/*                 │  screens, buttons, session state
└───────────────┬────────────────────────────────┘
                │ calls only labeling_engine.run_query(...)
┌───────────────▼────────────────────────────────┐
│ Core (labeler/)                                │  pure Python, no Streamlit
│  labeling_engine  → orchestrates a run         │
│  prompt_builder   → system + batch prompts     │
│  response_parser  → lines + logprobs → labels  │
│  cost_estimator   → tokens → $                 │
│  models           → Query, RowResult, RunStats │
└───────┬───────────────┬───────────────┬────────┘
        │               │               │
┌───────▼──────┐ ┌──────▼──────┐ ┌──────▼───────┐
│ openai_client│ │ result_cache│ │ csv_io       │  infrastructure
│ (only file   │ │ (SQLite)    │ │ query_store  │
│  that calls  │ │             │ │ (JSON)       │
│  OpenAI)     │ │             │ │              │
└──────────────┘ └─────────────┘ └──────────────┘
```

Rules:
- The UI never calls OpenAI, SQLite or the file system directly.
- Core has no Streamlit imports, so a hosted version later reuses it unchanged.
- Changing the LLM provider only changes `openai_client.py`.

## 2. Folder structure

```
llm-csv-labeler/
├── app.py                        # Streamlit entry point (thin: layout only)
├── ui/
│   ├── ui_models.py              # AppState type only
│   ├── session.py                # get_state() from st.session_state
│   ├── sidebar.py                # key status, model, session spend, clear cache
│   ├── upload_section.py         # upload, column picker, preview
│   ├── query_card.py             # one card: edit, test, run, delete, stats box
│   ├── query_file_section.py     # save/load queries JSON
│   └── download_section.py       # labelled CSV download
├── labeler/
│   ├── config.py                 # settings only: model, prices, batch size, limits
│   ├── models.py                 # types only: dataclasses and enums
│   ├── errors.py                 # exception classes only
│   ├── api_key.py                # load OPENAI_API_KEY from .env
│   ├── prompt_builder.py         # system prompt, batch prompt, text sanitising
│   ├── openai_client.py          # the only OpenAI caller
│   ├── response_parser.py        # reply lines + logprobs -> labels, confidence
│   ├── row_preparer.py           # empty/trim checks, de-duplication
│   ├── batch_runner.py           # concurrent batches, retry/recovery, refusals
│   ├── labeling_engine.py        # public API: estimate_cost(), run_query()
│   ├── cost_estimator.py         # token counting, $ from estimate/usage
│   ├── result_cache.py           # SQLite cache
│   ├── csv_io.py                 # read (encoding/delimiter), write bytes
│   ├── column_utils.py           # column naming, text-column detection
│   ├── output_builder.py         # attach label/conf/note columns to the table
│   └── query_store.py            # queries <-> JSON
├── scripts/
│   └── run_labeling_cli.py       # headless run + accuracy check vs sample_key.csv
├── tests/
│   ├── test_response_parser.py
│   ├── test_labeling_engine.py   # mocked OpenAI
│   ├── test_csv_io.py
│   └── test_query_store.py
├── sample_data/                  # sample.csv, sample_key.csv, sample_queries.json, make_sample.py
├── docs/
│   ├── architecture.md
│   ├── milestone-1/{pre-development.md, post-development.md}
│   └── milestone-2/{pre-development.md, post-development.md}
├── CLAUDE.md
├── README.md                     # macOS setup guide
├── requirements.txt
├── .env.example
└── .gitignore                    # .env, cache.db, venv, __pycache__
```

Changes from the plan:
- Files are renamed to say what they hold (`cost.py` → `cost_estimator.py`, `cache.py` → `result_cache.py`, `io_utils.py` → `csv_io.py`, `queries.py` → `query_store.py`).
- `engine.py` is split by job into `row_preparer`, `batch_runner`, `response_parser` and `labeling_engine`.
- Types and exceptions have their own files.
- The UI is split into `ui/`, and there is a CLI script for Day 1 testing.

## 3. Run flow (one query)

1. **Prepare.** Strip the text. Empty rows get the note `empty` and aren't sent. Text over 2,000 chars is trimmed with the note `trimmed`. Newlines and `|` become spaces.
2. **Deduplicate.** Identical texts are sent once, and the result is copied to every matching row.
3. **Cache lookup.** The key is a hash of model + prompt version + query + text. Hits cost $0.
4. **Batch.** Uncached unique texts are split into batches of 50 and given short local ids 1–50, which are mapped back to the CSV rows locally.
5. **Send concurrently.** asyncio with a semaphore, 10 batches at a time, `temperature=0`, `logprobs=True`, `top_logprobs=2`, and `max_tokens` capped per batch.
6. **Parse.** Use the regex `^(\d+)\|([01])$`. Confidence = `p_chosen / (p_0 + p_1)`.
7. **Recover.** If more than half a batch is missing, it's retried at half size. Any other missing rows are retried one by one. After that, rows get the note `refused`, `blocked` or `failed` and stay blank.
8. **Save.** Good results are written to the cache after each batch (SQLite WAL, commit per batch, so closing the tab can't corrupt it). Failures are not cached.
9. **Return.** The run returns a DataFrame with `<name>`, `<name>_conf` and `<name>_note`, plus RunStats (matched, not labelled, note counts, actual cost).

A progress callback (`done_batches, total_batches`) is passed in from the UI, so the engine stays UI-free.

## 4. Efficiency: beating the targets

| Technique | Gain |
|---|---|
| Short local ids (1–50) instead of CSV row numbers | fewer input/output tokens |
| Deduplicate identical texts | "N/A", "No opinion" etc. are sent once |
| SQLite cache | re-runs and unchanged rows cost $0 |
| Static system prompt + criterion first | OpenAI's automatic prompt caching discounts the repeated prefix |
| `max_tokens` = rows × 6 | stops runaway replies |
| Concurrency 10 (configurable) and the SDK's built-in 429 retry (honours Retry-After) | fast without hitting rate limits |
| `tiktoken` estimate before the run | no surprise costs |

**Targets for 1,000 rows:** under 30 seconds and under 1 cent per query. The plan's targets are 2 minutes and a few cents.

## 5. Model

A standard (non-reasoning) chat model that supports logprobs. The candidate is the cheapest current "nano/mini" chat model, to be verified on build day by a live check on whether the `0`/`1` comes back as its own token. The model name and prices live only in `config.py`.

## 6. Error handling

| Case | Result |
|---|---|
| 401 / missing key | Run stops, clear UI message, Run button disabled |
| 429 / timeout | SDK backoff retry (max 3), then `failed` |
| `message.refusal` / no valid lines | Split, retry single rows, then `refused` |
| `finish_reason == content_filter` | Single-row retry, then `blocked` |

## 7. Git

`main` (releases to Alex) ← `staging` (Alex tests here) ← `dev` ← `feature/<name>`. Every feature goes through a PR into `dev`. The key is never committed or logged.
