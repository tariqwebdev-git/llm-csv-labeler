# Project status and handover log (internal)

**Read this first in every new session.** Update it whenever something is sent to Alex, he replies, or a decision is made. This file is internal: `export-ignore` keeps it out of Alex's zip.

Last updated: 2026-11-12

## Where we are
- **Alex tested v1.0.2 and is happy** ("looks terrific"). He **activated Milestone 2 "Four additional features" ($400)**: Claude option, highlight/filter a query's rows in the sidebar, a workspace per column, keyword queries. That's exactly Part 2, already built on `feature/part2`.
- **v1.1.0 released on 2026-11-13** (Milestone 2): Part 2, white sidebar cells, highlight-only sidebar, match count on cards, keyword rules (whole words, `*` wildcard), Claude with confidence (stated score + vote check), checked live with Alex's key. Zip `output/llm-csv-labeler-v1.1.0.zip`. **Tariq sends one end-of-day report to the senior, and the zip with a short note for Alex.**
- **People:** Asad (senior) has left. The new senior is new to the project and forwards client messages directly; Tariq writes the replies. Don't mention any senior in client messages.

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
| 2026-11-10 | **Part 2 built in house on `feature/part2`** (Asad: build in house; Alex had said don't start yet): workspace per column, keyword queries (confidence 1.00, whole-words checkbox), sidebar filter + green highlight per query, Claude option (labels only). 112 tests, 14/14 browser checks. Pushed, not merged. Notes: `docs/milestone-3/` on that branch. |
| 2026-11-12 | **Alex's feedback on v1.0.2:** looks great. Two small requests for the next version: (1) **white background for the answer cells in the sidebar** (grey cells are hard to read); (2) **match count on each card, also when collapsed** ("traffic_accidents: 45 matches"). His third point (click doesn't show full text) he withdrew: double-click works. |
| 2026-11-12 | **Alex activated Milestone 2 "Four additional features", $400** (Claude $140, sidebar filter/highlight $70, workspace per column $105, keyword queries $105). For the sidebar: **highlight first**; he asked if switching to filter later is easy (yes; we already have both). Still interested in the **hosting quote**. |
| 2026-11-12 | **Reply sent to Alex** (by Tariq): starting the four features; the 2 small changes come in the same version; highlight first, filter is an easy switch; **asked for a Claude API key** (console.anthropic.com, low spend limit, delete after); **hosting quote** (see Decisions). Waiting for his answers. |
| 2026-11-12 | Asad has left the company; the new senior is new to the project. |
| 2026-11-12 | **v1.1.0 built on `dev`** (plan approved by Tariq: highlight only, release waits for the Claude key). Details: `docs/milestone-3/post-development.md` (v1.1.0 section). |
| 2026-11-13 | Senior forwarded **Alex's Claude key** (in `.env` only, about a $5 limit; Alex deletes it after) and the Milestone 2 work order. He asked for the Claude plan (model, confidence, cost per 1,000 rows) and a time estimate. **Keyword rules confirmed by Alex:** whole words, case ignored, OR, `*` at the end = word starts, punctuation handled, keywords escaped. Hosting: Alex leans to **Full**, no work until he confirms. Popup: skip. |
| 2026-11-13 | Built the keyword rules (removed the whole-words checkbox). **Live Claude check:** 20/20 on the main query; eval vs OpenAI 100/98/94.6/100% vs 100/98/99.4/100%; about 2x OpenAI's cost; wrong labels get the lowest scores. Calibration table kept as identity (too few unsure rows). Test spend about $0.012. |
| 2026-11-13 | **Released v1.1.0.** (Rebuilt the same day without `INSTALL-MAC.md`, which is now always sent separately; tag moved, zip not yet sent.) Messages to send at the end of the day: one report to the senior (status, Claude plan with the measured cost) and the zip with a short note for Alex. |

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
1. **Send** (Tariq, end of day): the report to the senior, then the v1.1.0 zip + a short note to Alex (the guide's "Getting a new version" has the update steps).
2. **Waiting for Alex:**
   - feedback on v1.1.0; he deletes the Claude test key once he's happy
   - **hosting:** he leans to the Full option; plan it as its own milestone when he confirms (quote under Decisions)
3. **Hosting:** after his answers, plan it as its own milestone (quote and options under Decisions).
4. Still unconfirmed by Alex: the update steps (`ditto`, macOS-only) and the CSV opening in Excel on his Mac.
5. **Optional, only if Alex asks:** his 20 hand-labelled rows per query; v2 ideas ("invert" for "does not" queries, several columns combined).

**If a push is refused (403):** Windows Credential Manager may hold a different GitHub account (it once held `aasimdev`). Remove the `git:https://github.com` credential and sign in as `tariqwebdev-git`.

## How to release a zip
1. Merge the feature branch into `dev`, run `pytest`, then `dev` → `staging` → `main` (`--no-ff`). Then `git tag -a vX.Y.Z` on `main`, and push the branches and the tag.
2. Build: `git archive --format=zip --prefix=llm-csv-labeler/ -o output/llm-csv-labeler-vX.Y.Z.zip vX.Y.Z` (`output/` is git-ignored). **Delete older zips** in `output/` so the wrong one isn't sent.
3. Check the zip: no `CLAUDE.md`, `docs/milestone-*`, `docs/walkthrough-script.md`, `docs/acceptance-checklist.md`, `docs/project-status.md`, `INSTALL-MAC.md`, `.env`, `cache.db` or `data/`, and a search for "asad|upwork" finds nothing. Unzip into a temp folder, install with the commands above, run `pytest`, and check that the app starts.
4. Internal files are kept out of the zip by `export-ignore` in `.gitattributes`. Add any new internal doc there.

## Decisions (and why)
- **Claude confidence:** stated score + vote check on doubtful rows + calibration (`docs/claude-confidence-method.md`). Keyword query confidence is 1.00.
- **Browser checks** live in `tools/browser_checks/` (Playwright + Edge, separate venv, internal only).
- **Delivery is a zip only;** Alex has no GitHub access. The zip has no git history.
- **`INSTALL-MAC.md` is never in the zip** (Tariq's rule, 2026-11-13): Tariq sends it separately next to the zip. It is `export-ignore`d, and the README names it in plain text (no links that would break in the zip).
- **Only Tariq is shown as author** in commits (no Claude co-author line). The whole history was rewritten on 2026-11-05 to remove it; a backup bundle was saved in the session scratchpad (temporary).
- **Internal docs stay out of the zip:** CLAUDE.md names the senior; the milestone docs and checklist hold internal numbers and asks.
- **Model:** `gpt-6-luna` with `REASONING_EFFORT="none"`; `gpt-4o-mini` shuts down 2027-01-14. See `milestone-2/post-development.md` Part E.
- **Hosting quote sent 2026-11-12** (prices are Tariq's/company's call; these are what was sent):
  - **Basic $250:** Streamlit Community Cloud, private and invite-only by email (Google sign-in or one-time email link), saved results in a free online database (Neon), spending cap, $0 a month. Caveats told to Alex: it **sleeps after 12 h unused** (one click wakes it), and **invited viewers can invite others** (and see usage stats), so it suits a small trusted group.
  - **Full $450 (recommended):** own small server, Google/Microsoft login, user list only Alex controls, spending cap per user, usage log, about $15 a month (estimate; confirm the provider and price before committing).
  - Both: uploaded CSVs aren't stored; keys in the server's secret settings; the results cache stores only a hash of each text plus the label.
  - **Community Cloud facts (docs checked 2026-11-12):**
    - only **one private app** per account
    - deploying needs GitHub admin rights on the repo (Alex has no GitHub)
    - about 2.7 GB memory at most; limits "may change at any time"
    - extra resources only for non-profit/educational apps
    - the docs don't say whether local files survive a restart, so use Neon for the cache
  - Effort: about 3–4 days (≈ $100/day, in line with the $400 milestone).
  - Asad told Alex about a "security approach" that Alex liked; it isn't in our notes, so check the Upwork chat before planning hosting.
- **Hosting background** (the plan's scope is a local app):
  - **Streamlit Community Cloud is the best free option** (private app, key in Secrets), but its cache resets on restart.
  - **Render free** has no disk (cache lost), no login and 512 MB, so it's not recommended.
  - A **browser-storage cache** is fragile, so it's not recommended.
  - To keep the cache when hosted: a free Postgres (e.g. Neon). Only `result_cache.py` would change.
  - It also means his CSVs leave his Mac.

## Client communication
Rules are in memory (`client-message-style`): short, natural, senior tone, match his length, no numbers (speed, cost, accuracy), don't ask him for anything unless Tariq says so, no tips, never mention Asad. Tariq sends all messages himself; drafts end with "Regards, Tariq".
