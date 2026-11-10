# Project status and handover log (internal)

**Read this first in every new session.** Update it whenever something is sent to Alex, he replies, or a decision is made. This file is internal: `export-ignore` keeps it out of Alex's zip.

Last updated: 2026-11-10

## Where we are
**`v1.0.2` is released** (on `main`, zip built and checked), but **not yet sent to Alex**: wait for Asad's go-ahead (Tariq's day-4 update). Still waiting for Alex to confirm the app runs after the conda fix.

| Date | What happened |
|---|---|
| 2026-11-04 | Plan received; development started. |
| 2026-11-05 | Daily report to Alex: app built, now testing edge cases. |
| 2026-11-05 | Released `v1.0.0`, then `v1.0.1` (cleaner zip). Walkthrough video recorded on Alex's election CSV. |
| 2026-11-05/06 | **Handover sent:** zip `llm-csv-labeler-v1.0.1.zip`, `INSTALL-MAC.md`, the video and a short message (start with INSTALL-MAC.md; delete the "highlighter-dev" key once his own key works). |
| 2026-11-06 | Alex installed it but his first **Test** failed: `TypeError: process() takes no keyword arguments`. Second issue in his screenshot: the estimate line rendered garbled (`$` read as a maths formula). |
| 2026-11-06 | Sent the fix by message (no new zip): rebuild `.venv` and use the conda-proof commands below. |
| 2026-11-06 | On `dev` (not released): conda-proof guide/README, sidebar wrong-environment warning, `$` fix (Part I in `milestone-2/post-development.md`). |
| 2026-11-09 | Alex sent a list of changes; Asad split it into Part 1 (in contract: 8 UI items + rest of Milestone 2) and Part 2 (add-ons, **not started**: Claude option, row filter per query, a workspace per column, keyword queries; hosting quoted separately). Estimate for Part 1: 1 day. Asad wants a short update with screenshots at the end of each day. |
| 2026-11-09 | Part 1 UI built on `feature/ui-rework` (Part J in `milestone-2/post-development.md`); 87 tests pass and a live browser check passed. Python minimum is 3.12 (Asad said 3.10; numpy needs 3.12), so tell Asad. |
| 2026-11-10 | Tariq tested Part 1. Fixes from his test: scrolling (now a one-window layout where only the query area scrolls) and narrow windows (sidebar capped at 45%, top bar wraps). Merged into `dev` and pushed. Video: not re-recorded (round 2; the earlier one stands). |
| 2026-11-10 | **Released `v1.0.2`** (`dev` → `staging` → `main`, tag pushed). Zip `output/llm-csv-labeler-v1.0.2.zip`: 81 files, no internal files, no Asad/Upwork mentions. Clean install with uv (Python 3.12.10): 87 tests pass and the app starts. Old v1.0.1 zip deleted. |
| 2026-11-10 | `INSTALL-MAC.md`: "Already using the app?" pointer at the top, plus "What's new" and update steps that work from the app folder (shown with Alex's `~/Code/llm-csv-labeler`). README matched. **v1.0.2 rebuilt:** tag moved to the new `main` commit and force-pushed (nobody had the old zip). Only docs changed, so the clean-install check still holds. **Alex gets only the zip:** no separate message or guide; the update steps are in the guide inside it. |
| 2026-11-10 | **Part 2 built in house on `feature/part2`** (Alex said don't start; Asad said build in house): workspace per column, keyword queries (confidence 1.00, whole-words checkbox), sidebar filter per query, Claude option (labels only; confidence method to agree with the client). 112 tests, 14/14 browser checks. **Not merged into `dev`.** Details: `docs/milestone-3/post-development.md`. |

## Alex's environment
- macOS. **Conda `(base)` is always active** in his Terminal, and his Python setup is "a bit of a mess" (his words).
- Project folder: **`~/Code/llm-csv-labeler`**, not Documents.
- **Cause of his error:** with conda active, `uv pip install` / `uv run` used conda's base environment. That environment has `brotli` 1.0.9, and httpx2 (inside the OpenAI SDK) calls `brotli…process(data, output_buffer_limit=…)`, which brotli < 1.2 rejects. A clean `.venv` has no brotli, so it works.
- **His commands now** (always target `.venv`, so conda can't interfere):
  ```
  uv venv --python 3.12
  uv pip install --python .venv -r requirements.txt
  .venv/bin/python -m streamlit run app.py      # daily start
  ```
- Note: the 20-row test that failed did reach OpenAI (it failed while decoding the reply), so it may have cost a fraction of a cent.

## Waiting on / next steps
1. **Tariq's day-4 update to Asad:** Part 1 done, v1.0.2 zip, Python 3.12 (not 3.10, numpy needs it), hover not possible so double-click. Ask whether to send v1.0.2 to Alex, and when to plan Part 2.
2. **After Asad agrees:** send Alex `llm-csv-labeler-v1.0.2.zip` only. The guide inside it starts with "Already using the app?" and links to "Getting a new version" (what's new and in-place update steps; his `.venv`, `.env` and `cache.db` stay).
3. **Alex confirms:** the app runs (conda fix), the update steps work (`ditto`, macOS-only, untested here), and the CSV opens in Excel. If it fails, ask for the full error and `.venv/bin/python --version`.
4. **Part 2** is built on `feature/part2`, **not merged**. Merge into `dev` and release only when the client agrees. Still open: Alex confirms whole-word keyword matching; the Claude confidence method (stated score + vote check, to agree with the client); a live Claude check needs an `ANTHROPIC_API_KEY`. Hosting is quoted separately.
5. **Optional, only if Alex asks:** his 20 hand-labelled rows per query; v2 ideas ("invert" for "does not" queries, several columns combined).

**If a push is refused (403):** Windows Credential Manager may hold a different GitHub account (it once held `aasimdev`). Remove the `git:https://github.com` credential and sign in as `tariqwebdev-git`.

## How to release a zip
1. Merge the feature branch into `dev`, run `pytest`, then `dev` → `staging` → `main` (`--no-ff`). Then `git tag -a vX.Y.Z` on `main`, and push the branches and the tag.
2. Build: `git archive --format=zip --prefix=llm-csv-labeler/ -o output/llm-csv-labeler-vX.Y.Z.zip vX.Y.Z` (`output/` is git-ignored). **Delete older zips** in `output/` so the wrong one isn't sent.
3. Check the zip: no `CLAUDE.md`, `docs/milestone-*`, `docs/walkthrough-script.md`, `docs/acceptance-checklist.md`, `docs/project-status.md`, `.env`, `cache.db` or `data/`, and a search for "asad|upwork" finds nothing. Unzip into a temp folder, install with the commands above, run `pytest`, and check that the app starts.
4. Internal files are kept out of the zip by `export-ignore` in `.gitattributes`. Add any new internal doc there.

## Decisions (and why)
- **Delivery is a zip only;** Alex has no GitHub access. The zip has no git history.
- **Only Tariq is shown as author** in commits (no Claude co-author line). The whole history was rewritten on 2026-11-05 to remove it; a backup bundle was saved in the session scratchpad (temporary).
- **Internal docs stay out of the zip:** CLAUDE.md names the senior; the milestone docs and checklist hold internal numbers and asks.
- **Model:** `gpt-6-luna` with `REASONING_EFFORT="none"`; `gpt-4o-mini` shuts down 2027-01-14. See `milestone-2/post-development.md` Part E.
- **Hosting** (discussed, not agreed with Alex; the plan's scope is a local app):
  - **Streamlit Community Cloud is the best free option** (private app, key in Secrets), but its cache resets on restart.
  - **Render free** has no disk (cache lost), no login and 512 MB, so it's not recommended.
  - A **browser-storage cache** is fragile, so it's not recommended.
  - To keep the cache when hosted: a free Postgres (e.g. Neon). Only `result_cache.py` would change.
  - It also means his CSVs leave his Mac.

## Client communication
Rules are in memory (`client-message-style`): short, natural, senior tone, match his length, no numbers (speed, cost, accuracy), don't ask him for anything unless Tariq says so, no tips, never mention Asad. Tariq sends all messages himself; drafts end with "Regards, Tariq".
