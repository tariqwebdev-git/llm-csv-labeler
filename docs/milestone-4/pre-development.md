# Milestone 4: Pre-development (Alex's "Milestone 3": v1.2.0)

Naming: our `milestone-3` docs are Alex's Milestone 2 (four features, v1.1.0). This folder is his **Milestone 3**.

## Why
Alex tested v1.1.0 (2026-11-20, "looks terrific") and asked 5 things. After our reply (2026-11-23) he opened a new milestone:
1. **Progress bar fills, then 30–60 s more** (Claude only). Cause: `_vote_check` re-asked unsure rows in 4 rounds one after another, with nothing on screen. **Free fix.**
2. Confidence 0.50–1.00 for either label: answered, no work.
3. Keyword spaces are trimmed: answered, no work (`keyword_matcher.parse_keywords`).
4. **Cards waste space on a big monitor:** slimmer cards, two columns on wide screens, results folded. **Free polish.**
5. **"No match yet" view per column:** answers that no query on the column has matched, to spot missing themes. **New feature, $70.**

Plus: his v1.1.0 update copied old files, because the guide's `unzip 'llm-csv-labeler-v*.zip'` also unpacked older zips in Downloads (in no fixed order on macOS).

## Plan
1. **Re-check:** `BatchRunner.run_rounds` runs all re-check rounds at the same time under one concurrency limit, each round in its own batches (a row never appears twice in one request). `run_query(on_recheck_progress=...)` drives the bar: "Re-checking the rows Claude was unsure about: done/total".
2. **Cards:** `st.container(key="query_cards")` with a CSS grid (`minmax(36rem, 1fr)`): two columns when wide, one otherwise. One-line stats caption, estimate only before the first run, test results collapsed.
3. **No match yet:** `labeler/theme_coverage.unmatched_answers` (no Streamlit); sidebar toggle **All answers / No match yet (N)** using the active column's full runs.
4. **Guide:** exact zip name, remove the old unzipped copy first, Control+C, an `ls` check.
5. Docs, tests, browser check `check_v12.py`, release v1.2.0.

Not in scope: a download column for "no match yet" (only if Alex asks), hosting.
