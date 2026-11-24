# Milestone 4: Post-development (Alex's "Milestone 3": v1.2.0)

**Branch:** `feature/v1.2` from `dev`. **Built 2026-11-24.** Tests: **140 pass** (130 before). Browser checks: `check_v12` 9/9, `check_test_guide` 29/29, `check_part2` 17/17, `check_scrolling` OK.

## 1. Claude re-check: faster and visible
- `labeler/batch_runner.py`: `run_rounds(rounds, on_progress, on_batch_labelled)` plans each round's batches separately and runs every batch of every round together under the runner's one semaphore. `run()` now calls it with one round (same behaviour). Returns `BatchRoundsOutput` (`models.py`).
- `labeling_engine._vote_check`: same shuffled orders and seeds as before, one `run_rounds` call, then `combine_votes` as before. Same labels as v1.1.0 for the same replies.
- `run_query(..., on_recheck_progress=None)`; the card's bar restarts with "Re-checking the rows Claude was unsure about: done/total". Progress starts at 0/total so the message shows at once.
- **Live (Alex's key, 40 rows, new wording):** 4 batches + 4 re-check rounds = 8 requests, **2.3 s in total**, $0.0007.
- Tests: rounds overlap (a 0.2 s fake finishes well under 3 × 0.2 s), no row twice in one request, re-check progress reported, none when every row is sure.

## 2. Compact cards
- `ui/query_list_section.py`: cards inside `st.container(key="query_cards")`.
- `ui/page_style.css`: `[data-testid="stVerticalBlock"].st-key-query_cards` grid, `repeat(auto-fill, minmax(36rem, 1fr))`, `align-items: start`. 1920 px window with the sidebar open → 2 columns; 1100 px → 1 column (browser check).
- `ui/query_card.py`: stats are one caption line ("53 of 220 matched, 8 not labelled (8 empty) · \$… · 4s · … rows from cache"); the estimate shows only before the first full run; the "Test on 20 rows" expander starts collapsed.

## 3. "No match yet"
- `labeler/theme_coverage.py`: `unmatched_answers(df, column, label_lists)`: non-empty answers with no label 1 in any full run. Blank labels count as no match; runs of another length are ignored.
- `labeler/column_utils.has_text` is now the one "has usable text" rule (used by `count_empty`, `non_empty_answers`, `theme_coverage`).
- `ui/reading_list_sidebar.py`: segmented control **All answers (N) / No match yet (N)** above the list; caption explains that only full runs count. Each column has its own list (workspaces split the runs).
- Sample data: 212 answers → 159 after the keyword query "car" (53 matches).

## 4. Guide
`INSTALL-MAC.md` "Getting a new version" and README "Updating": exact zip name, `rm -rf llm-csv-labeler` first, **Control+C** everywhere, `ls labeler/theme_coverage.py` as a check, "What's new in 1.2.0".

## Pending
- Release v1.2.0 and send Alex the zip + `INSTALL-MAC.md`.
