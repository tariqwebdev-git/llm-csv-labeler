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
│  models           → Query, RowLabel, RunStats  │
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
├── .streamlit/config.toml       # less padding above/below the fixed bars
├── ui/
│   ├── ui_models.py              # AppState type only
│   ├── session.py                # get_state() from st.session_state
│   ├── page_style.py + .css      # custom CSS: one-window layout, only the query area scrolls; compact upload (no "<" in the CSS)
│   ├── upload_section.py         # top bar: compact file picker + text column
│   ├── session_info.py           # top right: key status, spend, Settings (model, Clear cache); warnings
│   ├── query_form_section.py     # top bar: single-line Create Query form
│   ├── data_preview_section.py   # empty-row warnings + preview (collapsed by default)
│   ├── query_actions.py          # state rules: add/edit/delete/record results (no drawing)
│   ├── result_tables.py          # preview order, test-run split
│   ├── answer_table.py           # every answers table: wrapped rows, double-click for full text
│   ├── query_list_section.py     # all cards (the main part of the page)
│   ├── query_card.py             # one card: collapsible header, edit, test, run, delete, stats box
│   ├── query_file_section.py     # bottom bar: Save queries, Load queries (popover)
│   ├── download_section.py       # bottom bar: Download CSV (new columns after the text column)
│   └── reading_list_sidebar.py   # sidebar: non-empty answers of the chosen column
├── labeler/
│   ├── config.py                 # settings only: model, prices, batch size, limits
│   ├── models.py                 # types only: dataclasses and enums
│   ├── errors.py                 # exception classes only
│   ├── api_key.py                # load OPENAI_API_KEY from .env
│   ├── environment_check.py      # is the app running from its own .venv? (warning at the top)
│   ├── python_version_check.py   # stops the app with a clear message on Python older than 3.12
│   ├── prompt_builder.py         # system prompt, batch prompt, text sanitising
│   ├── openai_client.py          # the only OpenAI caller
│   ├── response_parser.py        # reply lines + logprobs -> labels, confidence
│   ├── row_preparer.py           # empty/trim checks, de-duplication
│   ├── batch_planner.py          # groups rows into small batches (row count + token budget)
│   ├── token_counter.py          # token counts (tiktoken)
│   ├── batch_runner.py           # concurrent batches, retry/recovery, refusals
│   ├── labeling_engine.py        # public API: estimate_cost(), run_query()
│   ├── cost_estimator.py         # token counting, $ from estimate/usage
│   ├── result_cache.py           # SQLite cache
│   ├── csv_io.py                 # read (encoding/delimiter), write bytes
│   ├── column_utils.py           # column naming, text-column detection
│   ├── output_builder.py         # insert label/conf/note columns after the text column
│   └── query_store.py            # queries <-> JSON
├── scripts/
│   ├── run_labeling_cli.py       # run one query from the terminal (+ accuracy check vs a key)
│   ├── run_eval.py               # accuracy of several queries vs hand-made keys; compare models
│   └── run_stress_test.py        # large-file speed/cost/accuracy test (spend-capped)
├── tests/                        # test_*.py; no API cost (fake_classifier.py stands in for OpenAI)
├── sample_data/                  # sample.csv, sample_key.csv, sample_queries.json, generators
├── docs/
│   └── architecture.md           # this file
├── README.md                     # how to use the app, settings, troubleshooting
├── INSTALL-MAC.md                # step-by-step install guide
├── requirements.txt              # exact package versions (Python 3.12+)
├── .env.example                  # copy to .env and add your OpenAI key
└── .gitignore                    # .env, cache.db, output/, venv, data/
```

## 3. Run flow (one query)

1. **Prepare.** Strip the text. Empty rows get the note `empty` and aren't sent. Text over 2,000 chars is trimmed with the note `trimmed`. Newlines and `|` become spaces.
2. **Deduplicate.** Identical texts are sent once, and the result is copied to every matching row.
3. **Cache lookup.** The key is a hash of model + system prompt + query + text. Hits cost $0.
4. **Batch.** `batch_planner` groups uncached unique texts into batches of at most `BATCH_SIZE` (10) rows and `MAX_BATCH_ITEM_TOKENS` (1,000) text tokens. Each row gets a short local id (1–10), which is mapped back to the CSV rows locally. Bigger batches make answers drift between rows.
5. **Send concurrently.** asyncio with a semaphore, 10 batches at a time, `temperature=0`, `logprobs=True`, `top_logprobs=2`, and `max_tokens` capped per batch.
6. **Parse.** Use the regex `^(\d+)\|([01])$`. Confidence = `p_chosen / (p_0 + p_1)`.
7. **Recover.** If more than half a batch is missing, it's retried at half size. Any other missing rows are retried one by one. After that, rows get the note `refused`, `blocked` or `failed` and stay blank.
8. **Save.** Good results are written to the cache after each batch (SQLite WAL, commit per batch, so closing the tab can't corrupt it). Failures are not cached.
9. **Return.** The run returns a DataFrame with `<name>`, `<name>_conf` and `<name>_note`, plus RunStats (matched, not labelled, note counts, actual cost).

A progress callback (`done_batches, total_batches`) is passed in from the UI, so the engine stays UI-free.

## 4. Efficiency: beating the targets

| Technique | Gain |
|---|---|
| Short local ids (1–10) instead of CSV row numbers | fewer input/output tokens |
| Small batches (≤ 10 rows / 1,000 tokens), sent concurrently | accurate answers without losing speed |
| Deduplicate identical texts | "N/A", "No opinion" etc. are sent once |
| SQLite cache | re-runs and unchanged rows cost $0 |
| Static system prompt + criterion first | OpenAI's automatic prompt caching discounts the repeated prefix |
| Reply capped at rows × 8 tokens (`OUTPUT_TOKENS_PER_ROW_LIMIT`) | stops runaway replies |
| Concurrency 10 (configurable) and the SDK's built-in 429 retry (honours Retry-After) | fast without hitting rate limits |
| `tiktoken` estimate before the run | no surprise costs |

**Targets for 1,000 rows:** under 30 seconds and under 1 cent per query. The plan's targets are 2 minutes and a few cents.

## 5. Model

Current model: `gpt-6-luna`, with `REASONING_EFFORT = "none"`. It's a reasoning model, and it only returns the token probabilities used for the confidence score when reasoning is switched off. The model name, reasoning setting and prices live only in `config.py`.

To change the model: set `MODEL`, `REASONING_EFFORT` (`None` for older chat models, `"none"` for reasoning models) and the 3 `PRICE_*` values in `config.py`. Then check accuracy with `python scripts/run_eval.py --model <name>` before using it on real files.

## 6. Error handling

| Case | Result |
|---|---|
| 401 / missing key | Run stops, clear UI message, Run button disabled |
| 429 / timeout | SDK backoff retry (max 3), then `failed` |
| `message.refusal` / no valid lines | Split, retry single rows, then `refused` |
| `finish_reason == content_filter` | Single-row retry, then `blocked` |

The API key is never logged, printed or shown in the app.
