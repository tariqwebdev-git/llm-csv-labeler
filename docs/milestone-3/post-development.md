# Milestone 3: Post-development (Part 2 add-ons, built in house)

**Branch:** `feature/part2`, not merged into `dev`. Alex said not to start yet; Asad said build in house. Merge only when the client agrees. Sub-branches: `feature/part2-column-workspaces`, `-keyword-queries`, `-sidebar-filter`, `-claude-option`, `-docs`.

**Built 2026-11-10.** Tests: **112 pass** (87 before). Browser check (Playwright/Edge, `sample.csv`): **14/14**.

## 1. Workspace per text column
- `ColumnWorkspace` (in `ui/ui_models.py`) holds queries, full runs and test runs. The active column's workspace stays in `state.queries/full_runs/test_runs`, so the cards and actions didn't change. Other columns wait in `state.workspaces`.
- `ui/workspace_actions.py`:
  - `switch_column` parks the active workspace and restores the target one
  - `all_workspaces` lists every column's workspace
  - `query_counts` feeds the column picker ("transportation_open · 2 queries")
  - `reset_all_results` handles a new file: keep queries, drop results
- Column names are unique across all columns (`free_column_name`), because everything lands in one CSV.
- **Download:** each column's completed queries are inserted right after that column. Checked live: `transportation_open, person_getting_hit(+2), car_truck_bus(+2), housing_open, safety_open, night_dark(+2)`.
- Save/Load queries works on the active column.

## 2. Keyword queries
- `labeler/keyword_matcher.py`:
  - `parse_keywords` splits on commas, semicolons and new lines, trims, and drops case-insensitive duplicates
  - `keyword_pattern`: case-insensitive; whole words via `(?<!\w)…(?!\w)`; phrases match any spacing
  - `match_keywords`: label 1/0, **confidence 1.00** (decided by Tariq), empty rows noted `empty`
- `labeling_engine.run_keyword_query`: no API, cost 0. Shares the stats helper `_run_stats` with LLM runs.
- `Query.kind` (`QueryKind.LLM`/`KEYWORD`) and `Query.whole_words`. **Whole words isn't confirmed by Alex yet**, so it's a per-query checkbox, default on (`KEYWORD_WHOLE_WORDS_DEFAULT`).
- **UI:**
  - two tabs, "New LLM Query" / "New Keyword Query"
  - the keyword card shows a "Keyword" tag and "Free: keyword match"
  - Test/Run work without an API key
  - Edit changes the words and the checkbox (a finished query becomes Out of date)
- Query file: saves `kind` and `whole_words`; old files load as LLM queries.
- Checked: on `sample.csv`, `car, truck, bus` matched 78 rows, exactly the same as an independent regex.

## 3. Sidebar filter for one query
- A sidebar icon in each card header (disabled until a Test or Run) sets `state.sidebar_query_id`.
- The sidebar shows "column · rows of query", with a filter (All / Matched / Not matched / Not labelled, `st.segmented_control`) and × to go back. Matched rows are green (pandas Styler, light/dark-safe colour).
- Uses the full run, otherwise the 20 test rows. Empty rows are left out. Helpers: `result_tables.query_rows` / `filter_rows`.

## 4. Claude option (labels only)
- `anthropic==2.3.0` pinned. It's the newest release at least 2 weeks old (23 Oct 2026; 2.4–2.7 are newer). `pip check` is clean next to `openai==3.45.0`.
- `labeler/anthropic_client.py` is the only Anthropic caller, model **`claude-haiku-5-5`**:
  - **no temperature**: this model rejects sampling settings with a 400
  - `thinking: {"type": "disabled"}` (allowed at the default effort): one `id|label` line per row needs no reasoning
  - `cache_control` on the system prompt
  - errors map to ApiKeyError / ApiConfigError / ApiCallError
  - a `refusal` stop reason leaves rows unanswered → retried alone → note `refused`
- **Prices:** $0.10 input, $0.01 cache reads, $0.50 output per 1M tokens (prompts up to 100K). Source: the Claude API reference, checked 2026-11-10.
- **Confidence:** `tokens=[]` → `parse_reply` gives `confidence=None` → `_conf` blank. The method (stated score + vote check on doubtful rows + calibration, explained to Tariq) plugs into `AnthropicClassifier.classify` once agreed with the client.
- `provider_settings.py` holds the model, prices, key name and `has_confidence` per provider; `classifier_factory.make_classifier`.
  - The engine and `estimate_cost` take `provider`.
  - The cache key already includes the model, so the providers never share results (tested).
- **UI:**
  - The gear menu has a provider radio, which sets `state.provider` through a callback, so the right key loads on the same click.
  - The key status reads "OpenAI key" / "No Claude key".
  - The missing-key error names `ANTHROPIC_API_KEY`.
  - The estimate line says "Claude: labels without a confidence score for now".
  - LLM Run is disabled without that provider's key; keyword queries still run.
- `.env.example` gets `ANTHROPIC_API_KEY=` (optional). The scripts get `--provider`.
- **Not tested live:** there's no Claude key here. The fake-HTTP tests cover the request body (model, no temperature, thinking off, cache_control), reply, retry, 401, 404, refusal, usage and cache separation. Run a live `--limit 20` check once a key exists.

## Docs
- README: two query kinds, column workspaces, sidebar filter, "Using Claude instead of OpenAI", settings rows.
- INSTALL-MAC: "What's new" bullets, optional Claude key in Step 6.
- `docs/architecture.md` file tree, CLAUDE.md, `.gitattributes` (`docs/milestone-3/` export-ignored).

## Pending
1. Client agreement → merge `feature/part2` into `dev` → release (new version, zip, the release checks in `project-status.md`).
2. Alex confirms whole-word matching (the default stays on).
3. The Claude confidence method, agreed with the client, then built in `anthropic_client.py`, calibrated with `scripts/run_eval.py --provider anthropic`.
4. A live Claude check once a key is available.
