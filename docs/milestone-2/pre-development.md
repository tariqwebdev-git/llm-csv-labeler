# Milestone 2: Pre-development (Day 3: accuracy fixes, query cards)

## Context
Testing on `merged_all.csv` showed two failures:
- **(a)** Rows whose text is outside the chosen column are skipped as `empty`, and nothing warns the user.
- **(b)** 81 long German rows were wrongly labelled 1 for the query "accident". Re-sent one at a time, only 9 stayed 1, so **batch drift** caused about 72 of them. A clearer query reduced it to 1.

You asked for this fixed first. Then Day 3 of the plan: query cards, the 20-row test run, the cache button and query save/load.

Note on "accurately answer all": no LLM is 100% accurate, so we set measured targets below and verify them on 3 files.

---

## Part A: Accuracy fixes (`feature/accuracy-fixes`)

### A1. Batches sized by text length (fixes the drift)
- New file `labeler/batch_planner.py`: `plan_batches(texts) -> list[list[int]]`. It fills a batch until either `BATCH_SIZE` (50) rows or `MAX_BATCH_ITEM_TOKENS` is reached.
- `MAX_BATCH_ITEM_TOKENS` defaults to 1,500 and lives in `config.py`.
- Short survey answers still go 50 per batch, so speed and cost stay the same. Long German rules go roughly 3–8 per batch.
- `labeler/cost_estimator.py`: make the token counter public as `count_tokens()`. `estimate_tokens()` uses `plan_batches()`, so the estimate matches the real batching.
- `labeler/batch_runner.py`: build batches with `plan_batches()` instead of fixed slices.

### A2. Prompt rule for judging each item alone
`labeler/prompt_builder.py` gets this line in the system prompt: *"Judge each item on its own. Do not let other items influence your answer. Answer 1 only if the item itself clearly matches the criterion."*
This automatically invalidates the cache.

### A3. Empty-rows warning
- `labeler/column_utils.py`: `count_empty(df, column)`.
- `ui/upload_section.py`: after picking a column, show "298 of 1,030 rows are empty in `Auflage`; they will not be labelled".
- If more than 20% are empty, the warning is louder and names the column with the fewest empty rows.

### A4. Query hint
- A caption under the query box: "Write a full sentence describing what counts, e.g. 'Describes a person getting hurt in an accident, such as being hit by a vehicle'."
- If the query has fewer than 3 words, show a warning: "Short queries are often misread; test on 20 rows first."

### A-tests
- `tests/test_batch_planner.py`: short texts → 50 per batch; long texts → split by the budget; one huge text → its own batch.
- Update `test_labeling_engine.py`.

### A-targets (live checks, about $0.03 in total)
| File | Query | Target |
|---|---|---|
| `merged_all.csv` (local only, never committed) | "accident" | wrong 1s go from 81 to **≤ 9** |
| same | full-sentence query | **0–1** wrong 1s; the 2 test sentences, placed in `Auflage`, get **1** |
| `sample.csv` | near-miss query | **≥ 96.7%**, no regression |
| stress test A (5,000 rows) | hit query | **≥ 99.8%**, cost within +10% |

If a target is missed, I'll report it and tune (budget 1,000 or BATCH_SIZE 25), then re-test. I won't merge until the targets pass.

---

## Part B: Query cards and control (`feature/query-cards`)

| File | Change |
|---|---|
| `ui/ui_models.py` | `AppState` holds `queries: list[Query]`, `results: dict[query_id → RunResult]` and `test_results` |
| `ui/session.py` | Helpers: add/delete query, clear results on a new CSV (queries are kept) |
| `ui/query_card.py` (replaces `query_section.py`) | One card: **name as the title**, full query text underneath, status, a **shaded box** ("212 of 1,000 matched, 3 not labelled", notes, cost). Buttons: **Edit / Test / Run / Delete** |
| `ui/query_list_section.py` | "Add query" form (text, then **"New column name (for results)"**), then all cards |
| `ui/query_file_section.py` | Download the queries as `.json`, and upload a `.json` that adds "Not run" cards (`query_store.py` already exists) |
| `ui/sidebar.py` | **Clear cache** button (`labeling_engine.clear_cache`) |
| `ui/download_section.py` | Adds the columns of every query with status Done or Done with errors |

Card behaviour:
- **Test** labels 20 rows (`pick_test_rows`) and shows the matched and unmatched rows, the confidence and the cost. Status becomes Tested.
- **Run** shows the estimate first and a progress bar, then the status becomes Done or Done with errors.
- **Edit** changes the wording in place. A Done card becomes **Out of date** until it's re-run, and only that query re-runs.
- **Delete** asks for confirmation.
- The column name must be unique across the CSV columns and the other queries' 3 columns each.
- **Preview order:** labelled rows by lowest confidence first; **empty rows last**.

### B-tests (`tests/test_app_ui.py`, AppTest with the fake model)
- Add 2 queries; Run disabled without a key.
- Test run uses 20 rows.
- Editing marks the card Out of date.
- Delete needs confirmation.
- The download has both queries' columns.
- Save, then load JSON on a new CSV.
- The empty-rows warning appears.

---

## Docs and git
- Create `docs/milestone-2/pre-development.md` (this plan) and `post-development.md` (results, including the accuracy table). Update CLAUDE.md.
- Each feature branch is merged into `dev` and pushed after `pytest` passes and the live targets are met.
- Progress is reported in % after each item.

## Verification
- `pytest` passes.
- The live accuracy table above.
- A manual browser check: 2 cards on `sample.csv`, then Test, Run, Edit, Delete, save/load and download.

---

# Part J: Alex's UI changes + rest of Milestone 2 (`feature/ui-rework`, 2026-11-09)

## Context
After using v1.0.1, Alex sent a list of changes. Asad split it: **Part 1 (in contract)** is a UI rework that makes the query list the main focus, plus the rest of Milestone 2. **Part 2 (add-ons: Claude option, row filter per query, a workspace per column, keyword queries)** is not started until it's planned with Asad. Hosting is quoted separately.

Estimate: **1 day** (all of Part 1 was done on 2026-11-09).

## Part 1 items
1. **Long responses:** wrap text in every table (sidebar, test previews, results, data preview); click to read the full text. Hover was tried first: `st.dataframe` has no per-cell tooltip, so we use the native click overlay (Asad's fallback).
2. **Collapsible cards:** the whole card collapses to its name (+ status). This uses an arrow button, not an outer expander, because Test and Results are already expanders inside the card.
3. **Save / download:** small buttons in a bar fixed at the bottom of the window.
4. **Top bar:** compact upload + text column fixed at the top, key status and spend small at the top right, Create Query just below. Spreadsheet preview in a section collapsed by default.
5. **Query input:** single line, with the "Write a full sentence…" hint as the placeholder.
6. **Headers:** remove the big headers.
7. **Download column order:** each query's 3 columns go right after the text column (`df.insert`), in query order.
8. **Sidebar reading list:** wider sidebar listing the non-empty answers of the chosen column; it updates when the column changes.

Fixed bars use custom CSS (`.st-key-*` selectors only) and are checked at several window widths.

## Rest of Milestone 2
- Pinned versions: already done (Part E). Streamlit 1.66.1 is pinned, so the CSS can't break on an update.
- README conda commands + conda troubleshooting: mostly done (Part I); add a "Terminal shows (base)" row.
- README + INSTALL-MAC "Updating to a new version" without reinstalling everything.
- Python version check. **Minimum 3.12, not 3.10:** the pinned numpy needs 3.12, so 3.10/3.11 would fail at install anyway.
- Regression check: test run, estimate, cache, refusal flags, save/load.
- Tests for parsing, refusals, missing rows and CSV edge cases, with OpenAI mocked.
- Walkthrough video (≤ 5 min) and the final acceptance-checklist pass.
