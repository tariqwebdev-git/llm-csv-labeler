# Milestone 3: Pre-development (Part 2 add-ons, in house)

## Context
Alex asked for add-ons. Alex said not to start yet, but Asad said we can build them in house. So they go on a separate branch and are merged into `dev` only when Alex agrees. The one thing left out is the **Claude confidence method**: Claude has no logprobs, and the method (stated score + vote check, explained to Tariq) will be agreed with the client later. Everything else is built now:
1. A separate workspace and set of queries for each text column
2. Keyword queries ("New LLM Query" / "New Keyword Query" tabs)
3. Click a query to filter/highlight its rows in the sidebar
4. Claude as an option alongside OpenAI, **labels only for now** (`_conf` blank, confidence slot ready for the agreed method)

Decided: a keyword query's `_conf` is **1.00**. Whole-word matching isn't confirmed by Alex yet, so it's a per-query checkbox ("Whole words only", default on).

**Estimate: about 4 working days.**

## Branching
- Integration branch **`feature/part2`** from `dev`. Each add-on goes on its own branch from it (`feature/part2-column-workspaces`, `-keyword-queries`, `-sidebar-filter`, `-claude-option`) and merges back into `feature/part2`.
- `feature/part2` → `dev` only after the client says yes. `main`, `staging` and the v1.0.2 zip stay untouched.
- If a v1.0.2 fix lands in `dev`, merge `dev` into `feature/part2` to keep it current.

## 1. Workspace per column (1 day)
Today, changing the text column wipes all results. Now each column keeps its own queries and results, and switching back restores them.
- `ui/ui_models.py`: new `ColumnWorkspace` type (queries, full_runs, test_runs). `AppState` gets `workspaces: dict[str, ColumnWorkspace]`. The existing `queries`/`full_runs`/`test_runs` fields stay as the active column's workspace, so cards, actions and tests keep working unchanged.
- New `ui/workspace_actions.py`:
  - `switch_column(state, column)`: park the active workspace under its column, load the target (or an empty one).
  - `all_workspaces(state)`: every column's workspace, including the active one.
- `ui/upload_section.py`: a column change calls `switch_column` instead of `reset_results`. A new file still keeps the queries and drops all results (same rule as today, now applied to every workspace).
- Column picker label shows the query count, e.g. `transportation_open · 2 queries` (`format_func`).
- `ui/query_actions.free_column_name`: names must be unique across **all** workspaces, because every column's results end up in one CSV.
- `ui/download_section.labeled_table`: for every workspace, insert its completed queries' columns right after **that** column (reuses `add_result_columns(..., after=)`).
- Save/Load queries works on the active column (JSON v1 stays compatible).

## 2. Keyword queries (1 day)
- `labeler/models.py`: `QueryKind(str, Enum)` = `LLM`, `KEYWORD`. `Query` gets `kind` (default LLM) and `whole_words: bool = True`. The keyword list is stored in `text` ("car, truck, bus").
- New `labeler/keyword_matcher.py`:
  - `parse_keywords(text)`: split on commas/new lines, trim, drop duplicates (ignoring case). Phrases like "hit by" are allowed.
  - `match_keywords(texts, keywords, whole_words) -> list[RowLabel]`: case-insensitive. Whole words use `(?<!\w)word(?!\w)`, so "car" doesn't match "scar". Label 1/0, confidence 1.00. Empty rows get note `empty`, as with LLM queries.
- `labeler/labeling_engine.py`: public `run_keyword_query(texts, keywords_text, whole_words) -> RunResult` (cost 0, no API). The UI keeps calling only the engine.
- `labeler/config.py`: `KEYWORD_WHOLE_WORDS_DEFAULT = True`.
- `ui/query_form_section.py`: `st.tabs(["New LLM Query", "New Keyword Query"])` in the top bar.
  - The keyword tab has a one-line words box ("car, truck, bus"), a column name (suggested from the words), a "Whole words only" checkbox (on) and Add.
  - The short-query warning applies to LLM queries only.
- `ui/query_card.py`:
  - A "Keyword" tag in the header, and the estimate line reads "Free: keyword match, no API".
  - Test/Run work without an API key and finish instantly. Edit changes the words and the checkbox.
- `labeler/query_store.py`: saves `kind` and `whole_words`. Old files load as LLM queries.

## 3. Sidebar filter for a query (0.5 day)
- A small "Show in sidebar" icon in each card header sets `state.sidebar_query_id` (new `AppState` field).
- `ui/reading_list_sidebar.py`: when a query with results is chosen:
  - the title reads "transportation_open · person_getting_hit"
  - a filter (`st.segmented_control`): All / Matched / Not matched / Not labelled
  - a × to go back to all answers
  - the table shows text, label and confidence, with matched rows highlighted (pandas Styler, which `st.dataframe` supports)
- Uses the full run if there is one, otherwise the 20 test rows.
- New helper `sidebar_rows(...)` in `ui/result_tables.py`, which already shapes result tables. It reuses `add_result_columns`.
- The selection clears if the query is deleted or belongs to another column.

## 4. Claude option, labels only (1 day)
- `requirements.txt`: add `anthropic==<exact>`, pinned to a release at least 2 weeks old.
- New `labeler/anthropic_client.py`, the only file that talks to Anthropic. `AnthropicClassifier` implements the existing `models.Classifier` protocol:
  - `messages.create` at temperature 0
  - returns `LLMReply(content, tokens=[], usage, refusal=...)`
  - maps errors to `ApiKeyError` / `ApiConfigError` / `ApiCallError` like `openai_client.py`
  - prompt caching on the system prompt to cut cost
- **Confidence:** with no tokens, `response_parser.parse_reply` already returns `confidence=None`, so `_conf` stays blank. A clearly marked `_confidence(...)` hook in the client is where the agreed method goes later. The card shows "Claude: confidence score not available yet".
- New `labeler/classifier_factory.py`: `make_classifier(provider, api_key)` and the model/price lookup per provider.
  - `labeling_engine.run_query` / `estimate_cost` get a `provider` argument.
  - The cache key already includes the model, so the two providers never mix results.
  - `cost_estimator.cost_usd` uses the provider's prices.
- `labeler/config.py`: `PROVIDER = "openai"`, `ANTHROPIC_MODEL`, the 3 `ANTHROPIC_PRICE_*` values, `ANTHROPIC_API_KEY_ENV_VAR`.
  - **The model id and prices come from the `claude-api` skill at build time, never guessed** (default: the current Haiku model, the cheapest).
- `labeler/api_key.py`: `load_api_key(provider)`. `.env.example` gets `ANTHROPIC_API_KEY=`.
- UI:
  - The gear menu gets a provider choice (OpenAI / Claude), stored in `state.provider`.
  - The top-right key status follows the chosen provider.
  - Run is disabled when that provider's key is missing.
- `scripts/run_eval.py` and `run_labeling_cli.py`: `--provider` flag, so accuracy can be compared side by side.

## 5. Tests, docs, checks (0.5 day)
- **Tests** (mocked, no cost):
  - workspaces: switch and restore, unique names across columns, download places each column's queries after its own column
  - keyword matcher: case, whole words ("scar"), phrases, empty rows, 1.00 confidence
  - keyword UI tab and card
  - sidebar filter counts match the run's stats
  - Anthropic client: reply, refusal and error mapping through a fake HTTP transport, like `tests/test_openai_client.py`
  - provider switch and separate cache keys
  - query file round trip with `kind`
- **Docs:**
  - new `docs/milestone-3/pre-development.md` + `post-development.md`, plus `docs/milestone-3/` added to `export-ignore` in `.gitattributes`
  - README (keyword queries, columns, sidebar filter, adding a Claude key)
  - INSTALL-MAC (optional Claude key) and the "What's new" list
  - `docs/architecture.md`, the CLAUDE.md UI/architecture lines, `docs/project-status.md` (Part 2 in house, not merged)

## Verification
1. `pytest`: all pass (87 today).
2. Playwright/Edge end-to-end on `sample.csv`:
   - two queries on `transportation_open`, one on `safety_open`: switching back and forth keeps each set and its results
   - a keyword query (`car, truck, bus`) matches the same rows as a direct regex check, and "scar" doesn't match with whole words on
   - "Show in sidebar" filters to the matched rows, and the count equals "X of Y matched"
   - the download has each query's columns right after its own text column
   - the layout still holds at 1600 / 1100 / 760 px
3. Live Claude check with a small `--limit` (a few cents at most), **only if an `ANTHROPIC_API_KEY` is available**. Otherwise mocked tests only, and that gets reported.
4. Nothing merged into `dev` until the client agrees. `feature/part2` is pushed so Asad can see it.
