# Claude confidence score: options and recommended method (internal)

**Status (2026-11-12):** Claude labels work on `feature/part2`, with `_conf` blank. Alex paid for the Claude milestone, whose wording says "Claude's API does not return the token probabilities the confidence score is built on, so I would replace it with a different method". **The method below is the one to build next.** Code goes in `labeler/anthropic_client.py` (`AnthropicClassifier.classify`), plus a calibration table in `config.py`.

## The problem
With OpenAI, confidence comes from token logprobs: how likely the model thought "1" vs "0" was. Claude's API returns no logprobs, so we must measure certainty another way.

## Options considered
| # | Method | Cost | Strength | Weakness |
|---|---|---|---|---|
| 1 | **Stated score:** reply format `id|label|score` (e.g. `3|1|85`), score 50–100 | Same as now (1 call) | Cheap, simple | Models are overconfident and repeat stock numbers (90, 95). Order is useful; calibration is poor |
| 2 | **Vote check (self-consistency):** ask the same batch ~5 times with some randomness; label = majority, confidence = share of votes (1.00 / 0.80 / 0.60) | ~5× | Most honest: rows Claude flip-flops on really are unsure | Expensive, slow, coarse values; runs vary (the cache keeps reruns identical) |
| 3 | **Mix (recommended):** 1 for every row, 2 only for doubtful rows | ~1.5× typical | Close to normal cost; doubtful rows get a real check | A little more code |

## Recommended method (3): stated score + vote check + calibration
1. **First pass, one call per batch as today.** Reply `id|label|score`. Anchor the scale in the prompt so it's used fully: *100 = the answer says it clearly; 75 = it's implied; 50 = can't tell*. No sampling settings (Claude Haiku 5.5 rejects `temperature`).
2. **Re-check doubtful rows.** Rows with score under ~80 are asked 4 more times, shuffled within the batch so neighbouring rows can't sway them. Final label = majority of the 5 votes. Usually only 10–20% of rows are re-checked.
3. **Combine.** Confidence = vote share combined with the average stated score, mapped into 0.50–1.00 like today. A row that flip-flops always ends up low, even if it claimed to be sure.
4. **Calibrate once.** Run on the hand-labelled `sample.csv` (`scripts/run_eval.py --provider anthropic`), measure how often each score band is actually right, and store a small mapping table in `config.py`. Then "0.80" means "about 80% of rows like this are correct".
5. **Prove it.** On `sample.csv` (and Alex's file if available), the wrong labels must gather at the low-confidence end, because that's what Alex uses the score for. Compare side by side with OpenAI's logprob confidence.

**Fits the code:** the parser gets an optional third field. Everything else (columns, sorting, cache, UI) stays the same, and the cache stores the final answer, so reruns are identical and free. **Needs a Claude API key** (requested from Alex on 2026-11-12) for the calibration and live checks; the cost is a few cents.

## For the client (plain words)
"Claude doesn't expose probabilities, so we have it rate its own certainty and re-ask only the doubtful rows, then tune the scores against hand-checked answers. Cost stays close to a single pass, and low scores point to the rows worth checking."
