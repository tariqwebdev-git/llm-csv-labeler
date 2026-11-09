# Project status and handover log (internal)

**Read this first in every new session.** Update it whenever something is sent to Alex, he replies, or a decision is made. This file is internal: `export-ignore` keeps it out of Alex's zip.

Last updated: 2026-11-09

## Where we are
The app is built, released (`v1.0.1` on `main`) and delivered. **We're waiting for Alex to confirm the app runs after the conda fix.**

| Date | What happened |
|---|---|
| 2026-11-04 | Plan received; development started. |
| 2026-11-05 | Daily report to Alex: app built, now testing edge cases. |
| 2026-11-05 | Released `v1.0.0`, then `v1.0.1` (cleaner zip). Walkthrough video recorded on Alex's election CSV. |
| 2026-11-05/06 | **Handover sent:** zip `llm-csv-labeler-v1.0.1.zip`, `INSTALL-MAC.md`, the video and a short message (start with INSTALL-MAC.md; delete the "highlighter-dev" key once his own key works). |
| 2026-11-06 | Alex installed it but his first **Test** failed: `TypeError: process() takes no keyword arguments`. Second issue in his screenshot: the estimate line rendered garbled (`$` read as a maths formula). |
| 2026-11-06 | Sent the fix by message (no new zip): rebuild `.venv` and use the conda-proof commands below. |
| 2026-11-06 | On `dev` (not released): conda-proof guide/README, sidebar wrong-environment warning, `$` fix (Part I in `milestone-2/post-development.md`). |

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
1. **Alex confirms the app runs** with the commands above. If it still fails, ask for the full traceback and the output of `.venv/bin/python --version` and `.venv/bin/python -m pip list`.
2. **Release `v1.0.2`** (everything in Part I) the next time Alex needs a new zip. **Don't send a zip just for this:** his setup works with the message fix.
3. **Optional, only if Alex asks:**
   - a hosted version (see Decisions)
   - his 20 hand-labelled rows per query (we don't ask him for these)
   - v2 ideas: "invert" for "does not" queries, several columns combined

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
