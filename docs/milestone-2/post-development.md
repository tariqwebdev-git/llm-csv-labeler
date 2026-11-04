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

## Part B: Query cards (pending)
