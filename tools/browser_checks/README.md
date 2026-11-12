# Browser checks (internal, not in Alex's zip)

Automated checks that drive the real app in Microsoft Edge with Playwright. They complement `pytest`: they catch layout problems (fixed bars, scrolling, narrow windows) that AppTest can't see.

## One-time setup
Use a separate environment, so Playwright never ends up in `requirements.txt`. Edge is already installed on Windows, so no browser download is needed.
```
python -m venv %TEMP%\pwenv
%TEMP%\pwenv\Scripts\pip install playwright pandas
```

## Run
1. Start the app on port 8599 (from the project folder):
   `venv/Scripts/python -m streamlit run app.py --server.headless true --server.port 8599`
2. Run a check: `%TEMP%\pwenv\Scripts\python tools/browser_checks/<script>.py sample_data/sample.csv output/checks`
   Screenshots go to the output folder (`output/` is git-ignored).
3. **Restart the app after code changes.** Streamlit doesn't always reload changed `ui/` modules.

| Script | What it checks | API cost |
|---|---|---|
| `check_test_guide.py` | Every step of Tariq's manual test guide, 29 PASS/FAIL checks: upload, sidebar, short-query warning, 3 queries, test + cache, edit, run, fixed bars, collapse, download column order, save/delete/load, gear menu + Clear cache, resize | under $0.001 |
| `check_scrolling.py` | Only the query area scrolls; bar positions stay identical; last card reachable; 1600/1100/760 px | under $0.001 |
| `check_narrow_window.py` | Sidebar dragged wide on a 1000 px window, then 800/1366/1920 px (screenshots to inspect) | $0 |
| `check_part2.py` | Part 2 add-ons, 14 checks: tabs, keyword query = regex count, sidebar filter, column workspaces, download order across columns, Claude switch without a key. **Needs the Part 2 code (`feature/part2`, or `dev` once merged).** | under $0.001 |
| `take_screenshots.py` | The 3 screenshots for reports (after Run, collapsed cards, a long answer opened) | under $0.001 |

## Locator tips (learned the hard way)
- The query box: `get_by_label("New query", exact=True)`. The text column picker is also a text input.
- The Add button: `.st-key-add_query [data-testid=stBaseButton-primary]` with `.first`. A `help` tooltip adds a second button inside the keyed element.
- Segmented controls are `role="radio"`, not buttons.
- Card buttons under the top bar: use `dispatch_event("click")` if a normal click is blocked.
