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
