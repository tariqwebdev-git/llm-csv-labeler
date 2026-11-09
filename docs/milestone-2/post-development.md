# Milestone 2: Post-development

## Part A: Accuracy fixes (done)

### Root cause found
Answers **drift between items in the same request**. Once a batch has many similar items, the model tends to give the same answer to the rest. It happened in both directions:
- 81 German building rules were wrongly labelled 1 for "accident" in batches of 50.
- In a batch of about 30, "My coworker was hit by a motorcycle" was labelled **0, with confidence 1.0**.

Sent one at a time, every one of them was correct. Batches of **20 or fewer** showed no drift (120 of 120 hits found). Above that, drift appeared.

### Changes
| Fix | Where |
|---|---|
| Batches capped at **10 rows** and **1,000 text tokens** | `labeler/batch_planner.py` (new), `config.py`, `batch_runner.py` |
| Token counting in its own module | `labeler/token_counter.py` (new); `cost_estimator.py` uses the same batching for estimates |
| Prompt: "Judge each item on its own…" | `prompt_builder.py` |
| Empty-rows warning; names the column with the most text | `column_utils.count_empty / column_with_fewest_empty`, `ui/upload_section.py` |
| Query hint plus a short-query warning; label renamed to "New column name (for results)" | `ui/query_section.py` |

### Results (fresh cache)
| Check | Before | After |
|---|---|---|
| `merged_all.csv`, query "accident" | 81 rows = 1 | 27 = 1. The rest are rules the model honestly reads as "accident" (e.g. "Unfallsicherheit"); a one-word query is ambiguous |
| `merged_all.csv`, full-sentence query; 2 test sentences moved into `Auflage` | n/a | **Both test sentences = 1 (confidence 1.00); 1 wrong row (confidence 0.68, flagged as unsure)** |
| Stress A, 5,000 rows | 99.8% | **100% (5,000 of 5,000)** |
| `sample.csv` | 96.7% rows | 95.3% rows. **Same 4 debatable unique texts wrong**; one of them repeats 4× in the file |
| Speed, 1,000 rows | ~8 s | **~15 s** (more requests; concurrency 20 didn't help because of the account rate limit) |
| Cost, 1,000 rows | $0.009 | **$0.012** |

Both are still well inside the plan's targets (under 2 minutes, a few cents).

### Notes
- Cache results made under the old batching were cleared locally. Alex's machine has no old cache.
- The cache key doesn't include batch settings. After changing batching, use **Clear cache** (Part B adds the button).

## Part B: Query cards and control (done)
- **Query cards** (`ui/query_card.py`): the short name is the title, the full text sits underneath, then the status and a shaded result box ("X of Y matched, Z not labelled", notes, cost, time). Buttons: **Edit / Test (20 rows) / Run / Delete**.
- **Test run:** 20 fixed-seed rows, shown as Matched, Not matched and Not labelled tables, plus the cost.
- **Full run:** an estimate is shown on every card (cached per file, column and wording), then a progress bar. The status becomes Done, or **Done with errors** if any row was refused, blocked or failed.
- **Edit:** the wording changes in place. A Done query becomes **Out of date** and drops out of the download until it's re-run.
- **Delete** asks for confirmation.
- **Column names** never clash with CSV columns or with other queries' `_conf` / `_note` columns.
- **Preview order:** rows needing attention first, then lowest confidence, empty rows last.
- **Save/load queries** as JSON; loaded queries arrive as "Not run" cards and nothing runs automatically.
- **Sidebar:** a Clear cache button.
- A new CSV or column clears the results and keeps the queries.
- **Download** includes every Done / Done-with-errors query.
- State rules live in `ui/query_actions.py` (no drawing) and table shaping in `ui/result_tables.py`. `ui/query_section.py` was replaced.
- **Tests:** 60 pass, including 11 AppTest UI tests (cards, test run, run, edit, delete, JSON load, download, warnings) and 4 state-rule tests.

## Pending (Day 4)
- A manual browser check plus screenshots for Alex.
- Day 4 hardening: README final, code-comment pass, screen recording, Alex's real data, the accuracy target from Alex's 20 hand-labelled rows.

## Part C: Prompt hardening and evaluation (done)
`scripts/run_eval.py` scores 4 queries on `sample.csv` against hand-made keys (`sample_data/sample_extra_keys.py`; a blank key means ambiguous, not scored). Each run uses a fresh cache.

### Prompt variants tested (wrong unique texts per query: hit / buses / no-vehicle / insult)
| Variant | Wrong | Notes |
|---|---|---|
| Baseline (Day 3 prompt) | 4 / 4 / 3 / 0 = **11** | injection wrong on the negation query |
| + reminder after items + negation rule + "apply exactly" rule | 7 / 2 / 1 / 0 = 10 | **the hit query got worse** (missed golf cart, cyclist, hit-and-run) |
| **+ reminder + negation rule (chosen)** | 3 / 3 / 2 / 0 = **8** | best balance; the injection on the negation query is still wrong but flagged (confidence 0.56) |
| + balanced "meaning" rule | 6 / 1 / 1 / 0 = 8 | the hit query got worse again |

**Finding:** with `gpt-4o-mini`, any rule that tightens one query loosens another. The model is at its limit, and further prompt tweaks only move errors around.

### Model comparison (chosen prompt)
| Model | Wrong | Cost per 1,000 rows | Notes |
|---|---|---|---|
| **gpt-4o-mini (kept)** | 8 | ~$0.005 | |
| gpt-4o | 7 | ~$0.08 (16×) | buses query 100%, all injections resisted; but says scooters/cyclists aren't vehicles (debatable) |

Decision: keep `gpt-4o-mini`. `gpt-4o` is a one-line switch in `config.py` for hard queries.

### Regression checks
- Stress A: **100%** (5,000 of 5,000). Cost +11% (reminder text): $0.065 per 5,000 rows.
- Insult query: 100%.

### Also
- Cards now show **"Estimate: test $x for 20 rows · full run $y"** before running.
- 61 tests pass.

### Remaining errors (honest)
Debatable rows ("bike hit while parked", "hit my dog", "teenagers nearly knocked me over", the ferry), plus the injection row on the negation query, which is flagged as unsure. These need Alex's query wording or a v2 "invert" option for negation queries.

## Part D: Day 4 hardening and handover (done)
| Item | Result |
|---|---|
| Rate-limit test | `tests/test_openai_client.py`: the real client against a fake HTTP server (429 → retry → labelled; 429 forever → `failed`; 401 → clear error, key not echoed). `OpenAIClassifier` takes an optional `http_client` (tests only) |
| Mid-run kill test | `tests/test_cache_crash_safety.py`: hard-kills a run, then `PRAGMA integrity_check = ok` and the saved batches are kept |
| Acceptance checklist | `docs/acceptance-checklist.md`: every section 8 item ✅ with evidence, or ⏳ where it needs Alex (his data, the [X]-of-20 target, his install, Excel on his Mac) |
| README | Rewritten for cards: usage, query-writing tips, statuses, settings table (incl. `gpt-4o` switch), troubleshooting |
| Docstrings | Every public function in `labeler/` and `ui/` |
| Sample queries | `sample_data/sample_queries.json` |
| Walkthrough script | `docs/walkthrough-script.md` (≤ 5 min; recorded by Tariq) |
| Tests | 65 pass |

## Pending (needs Alex)
1. His real CSV plus 20 hand-labelled rows per query; then run `scripts/run_eval.py`-style checks and fill in the ⏳ rows.
2. His install from the README; then he deletes the "highlighter-dev" key.
3. ~~Release~~ Done: `v1.0.0` on `main` (Part G).

## Part E: Production hardening (done)
### Model replaced: `gpt-4o-mini` → `gpt-6-luna`
OpenAI marks `gpt-4o-mini` and `gpt-4o` as deprecated, **shutting down 2027-01-14** (deprecations page, checked 2026-11-05). The replacement `gpt-6-luna` is a reasoning model. A live probe showed it **returns logprobs only with `reasoning_effort="none"`** (without it the request is rejected); `temperature=0` works. New setting: `config.REASONING_EFFORT` (sent only when set; test `test_reasoning_effort_sent_only_when_configured`).

| Accuracy (rows) | gpt-4o-mini | **gpt-6-luna** | gpt-5.6-luna |
|---|---|---|---|
| sample.csv: hit / buses / no-vehicle / insults | 97.2 / 95.5 / 95.2 / 100 | **100 / 100 / 99.4 / 100** | 100 / 98.0 / 97.6 / 98.1 |
| Alex's file: ID / electoral / non-citizen / foreign / insults | 100 / 100 / 86.7 / 100 / 89.4 | **98.2 / 100 / 100 / 100 / 100** | 98.2 / 100 / 100 / 100 / 87.9 |
| Stress A (5,000 rows) | 100% | **100%**, 64 s | n/a |
| Cost per 1,000 short rows | ~$0.013 | **~$0.009** | ~$0.019 |

A vague query ("rows with voter id") stays poor on any model (~1 in 10 ID answers missed), so it's a wording issue; a tip was added to the README.

### Dependencies and Python
- `requirements.txt` pinned exactly (openai 3.45.0, pandas 3.1.0, numpy 2.5.4, streamlit 1.66.1, tiktoken 0.14.0, python-dotenv 1.2.4, pytest 9.2.0). Checked with a fresh venv: install plus 67 tests pass.
- **Python 3.12+ required** (numpy 2.5 needs ≥ 3.12; pandas and streamlit need ≥ 3.11). README fixed (it said 3.10) with a troubleshooting row added.
- Prices verified on OpenAI's model pages (2026-11-05); source and date noted in `config.py`.

## Part F: Mac install guide (done)
Alex installs alone, with no screen share and no Mac on our side, and may have an old Python or none.
- **`INSTALL-MAC.md`** (repo root): a step-by-step guide for a non-technical user. Each step says what to do, gives one command to paste, and shows "✅ You should see" with the real output. It covers getting the zip, opening Terminal, installing [uv](https://docs.astral.sh/uv/) (no admin password; it installs Python 3.12 into the project), installing the pinned packages, adding the key with TextEdit, starting the app and a quick check on the sample, followed by daily use and updating to a new version.
- **"If something goes wrong" table:** blank page / the app won't load (refresh, direct URL, private window to detect a blocking extension, another browser, Terminal still open), browser didn't open, port 8502, `uv` not found, wrong folder, install error, email prompt, key missing or rejected, all rows failed (billing / spend limit), app stopped, Excel characters.
- **README Setup** now points to the guide, and its short version uses the same uv commands (one way to install). The troubleshooting table has a blank-page row.
- The walkthrough script and acceptance checklist were updated.
- **Verified on a clean copy** (`git archive`, Windows): `uv venv --python 3.12` + `uv pip install -r requirements.txt` → 52 packages, `uv run pytest` → 67 pass, and `uv run streamlit run app.py` → health check 200. Not tested on a real Mac (none available); the commands are uv's standard cross-platform ones.

## Part G: Release v1.0.0 (done)
- **Handover:** Alex gets a zip (no GitHub access). It is built from the tag: `git archive --format=zip --prefix=llm-csv-labeler/ -o output/llm-csv-labeler-v1.0.0.zip v1.0.0`, so it unzips to the folder name used in `INSTALL-MAC.md`.
- **Left out of the zip** (`export-ignore` in `.gitattributes`): `CLAUDE.md`, `docs/milestone-*`, `docs/walkthrough-script.md` and `.gitattributes`, which are internal notes. `.env`, `cache.db` and `data/` are never in git, so they're never in the zip.
- **The zip contains:** the app, `labeler/`, `ui/`, `tests/`, `scripts/`, `sample_data/`, `README.md`, `INSTALL-MAC.md`, `requirements.txt`, `.env.example`, `docs/architecture.md` and `docs/acceptance-checklist.md`.
- `INSTALL-MAC.md` step 1 was changed for the zip. The README's developer note points to `docs/architecture.md`.
- The walkthrough script was rewritten for Alex's election CSV.
- Released `dev` → `staging` → `main`, tagged `v1.0.0`.

## Part H: v1.0.1 zip cleanup (done)
- **`docs/acceptance-checklist.md` left out of the zip** (`export-ignore`). It shows accuracy figures, asks Alex for hand-labelled rows and an accuracy target, and links to an internal doc. It stays in the repo.
- **`docs/architecture.md` brought in line with the code** (it's the maintenance doc in Alex's zip):
  - the folder tree now matches the zip, adding `batch_planner`, `token_counter`, all scripts and `INSTALL-MAC.md`, and dropping `CLAUDE.md` and the milestone folders
  - batches are ≤ 10 rows / 1,000 tokens with ids 1–10
  - the reply cap is rows × 8
  - the Model section covers `gpt-6-luna` + `REASONING_EFFORT` and how to change the model
  - the internal "Changes from the plan" and Git sections are removed
- `INSTALL-MAC.md` step 1 names the zip version-free ("e.g. …v1.0.1.zip").
- No app code changed; the walkthrough video recorded on v1.0.0 is still valid.

## Note: commit history
On 2026-11-05 the history was rewritten (all branches and tags, force-pushed) to remove the `Co-Authored-By` trailer from 25 commit messages. Tariq is the only author. Code is unchanged: every branch and tag points to the same tree as before, and only the commit IDs changed. Other clones must re-clone.

## Part I: Conda-proof setup and `$` display fix (on `dev`, not released yet)
**Alex's first test failed** with `TypeError: process() takes no keyword arguments`.
- **Cause:** his conda `(base)` was active, so `uv pip install` / `uv run` used conda's base environment instead of `.venv`. That environment has `brotli` 1.0.9. When brotli is importable, httpx2 (inside the OpenAI SDK) asks for brotli-compressed replies and decodes them with `process(data, output_buffer_limit=…)`, which brotli < 1.2 doesn't accept. In a clean `.venv` brotli isn't installed, so this never happens.
- **Fixed for Alex by message** (no new zip): `uv pip install --python .venv -r requirements.txt` and `.venv/bin/python -m streamlit run app.py`.
- **Repo changes:**
  - `INSTALL-MAC.md` and the README use those conda-proof commands, with a `.venv/bin/python --version` check, a conda note and troubleshooting rows.
  - New `labeler/environment_check.py` plus a sidebar warning when the app isn't started from the project's own environment.
- **`$` display bug** (seen in Alex's screenshot): Streamlit read the text between the two `$` signs in the card's estimate line as a maths formula. All `$` in card text are now escaped (`\$`).
- **Tests:** 70 pass (new: environment check ×2, wrong-environment UI warning; the estimate test checks the escaping).
- To be released as `v1.0.2` (`staging` → `main`, tag, zip) the next time Alex gets a new zip.

## Part J: Alex's UI changes (on `feature/ui-rework`, not released yet)
Built from Alex's list (plan: `pre-development.md` Part J).

| # | Item | How |
|---|---|---|
| 1 | Long responses | `ui/answer_table.py` is used by every answers table. Rows are 80 px, and Streamlit wraps text when rows are taller than 4rem (checked in the frontend code), so about 3 lines show. **Double-click a cell** (or click it twice) for the full text in an overlay. Hover isn't possible: `st.dataframe` has no per-cell tooltip. |
| 2 | Collapsible cards | Arrow button in the card header; collapsed shows name + status. State in `st.session_state["collapsed_<id>"]`. |
| 3 | Save / download | Bottom bar (`key="bottom_bar"`): small **Save queries**, **Load queries** (popover with the uploader), **Download CSV**. Load messages are toasts. |
| 4 | Top bar + preview | Top bar (`key="top_bar"`): compact uploader + text column, key status + spend + Settings popover (model, Clear cache) at the right, then the add form. Warnings (no key, wrong env) show full-width under the bar. **Data preview** expander, collapsed. |
| 5 | Query input | `st.text_input` with the hint as its placeholder; Enter suggests the column name. |
| 6 | Headers | All `st.title`/`st.header` removed. |
| 7 | Column order | `add_result_columns(..., after=)` uses `df.insert`. The download puts each query's 3 columns after the text column, then after the previous query's note column. Checked live: `…, transportation_open, person_getting_hit, _conf, _note, housing_open, …`. |
| 8 | Sidebar list | `ui/reading_list_sidebar.py`: 480 px sidebar (`initial_sidebar_state=480`, drag to resize), the non-empty answers of the chosen column with row numbers, wrapped, 650 px high, scrolls inside. |

**Fixed bars, how:**
- **First try: `position: sticky`** on the bars. Tariq's test showed it was unreliable: bars drifted, cards overlapped them, and stale elements showed through during reruns.
- **Final: one-window layout.** `stMainBlockContainer` is `height: 100vh` and a flex column. The top bar and bottom bar keep their height, and the wrapper of `st.container(key="query_area")` (warnings, data preview, cards) takes the rest with `overflow-y: auto`. The page itself never scrolls; only the query area does. Checked in Edge: bar positions stay identical while scrolling, the last card is reachable, and it holds at 1600×900, 1100×800 and 760×700.
- **Gotcha:** Streamlit's HTML sanitizer drops a `<style>` block whose text contains `<` followed by a letter (a CSS comment with `<key>` silently disabled everything). The CSS file says so, and `tests/test_page_style.py` guards it.
- No theme pin is needed (the bars have no background colour), so the app follows the system light/dark theme as before.
- **Narrow windows** (Tariq's test: sidebar dragged wide on a ~1000 px window squeezed the top bar to a few letters per line):
  - The sidebar is capped at 45% of the window.
  - Top-bar columns have a minimum width and wrap onto a new line.
  - The query area keeps at least 14rem.
  - Session info is compact (key status, spend, gear menu).
  - Bottom-bar buttons are smaller.
  - Checked at 1000 px with a wide sidebar, and at 800, 1366 and 1920 px.

**Milestone 2 rest:**
- **Python check:** `labeler/python_version_check.py` (no 3.10+ syntax) runs first in `app.py`. Below `config.MIN_PYTHON` (3.12) the app shows a clear error with the start command and stops. Minimum is 3.12 (not 3.10 as asked) because numpy 2.5 needs it.
- **README:** "How to use" rewritten for the layout, new **Updating to a new version** section, troubleshooting rows for `(base)` and the Python message.
- **INSTALL-MAC:** "Getting a new version" now updates in place without reinstalling (`unzip -o '…v*.zip'` + `ditto` over the old folder; `.venv`, `.env` and `cache.db` stay; `uv pip install` only fetches changed packages). Also sidebar wording fixed. Tested: quoted `unzip` wildcard with 2 zips → the newer one wins. `ditto` is macOS-only, so it isn't tested here.
- **Tests: 87 pass** (was 70):
  - new: version check ×3, column order ×2, non-empty answers, prose reply never guessed, duplicate headers survive, BOM-only file rejected, CSS guard ×2
  - UI: one-line box + placeholder, no headers, card collapse, download order, sidebar follows column, old Python stops
- **Live regression in Edge (Playwright, `sample.csv`):** upload → add → Test (20 rows, $0.0002) → re-test from cache ($0.0000) → Run (46 of 220 matched, 8 empty, 1 trimmed) → Download CSV (column order checked) → Save queries → Load queries (loaded as `person_getting_hit_2`). Screenshots at 1600 / 1100 / 760 px: bars stay fixed while scrolling, nothing overlaps.

**Done in 1 day (2026-11-09).** Walkthrough video recorded and sent by Tariq. Still to do: Tariq's review and merge into `dev`, then release v1.0.2 when Asad says.
