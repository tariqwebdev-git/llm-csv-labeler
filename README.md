# LLM CSV Labeler

Upload a CSV, write plain-English yes/no queries, and download your file with three new columns per query: a label (1/0), a confidence score and a note.

## Setup (macOS)

**New to Terminal? Follow INSTALL-MAC.md** (the install guide sent with the zip): a step-by-step guide with what you should see at each step.

Short version. [uv](https://docs.astral.sh/uv/) installs Python 3.12 and the packages, whatever Python your Mac has:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh      # once; then open a new Terminal window
cd ~/Documents/llm-csv-labeler
uv venv --python 3.12
uv pip install --python .venv -r requirements.txt
cp .env.example .env && open -e .env                  # paste your key after OPENAI_API_KEY=
.venv/bin/python -m streamlit run app.py              # opens the app in your browser
```
Next time, you only need the `cd` line and `.venv/bin/python -m streamlit run app.py`. These commands always use the project's own `.venv`, so an active conda `(base)` can't interfere.

## Updating to a new version
Your `.venv`, `.env` key and `cache.db` (saved results) stay in place. Only the app files are replaced, and only changed packages are downloaded. Stop the app first (Ctrl+C), then, with the new zip in Downloads:
```bash
cd ~/Downloads && unzip -o 'llm-csv-labeler-v*.zip'      # makes ~/Downloads/llm-csv-labeler
cd ~/Code/llm-csv-labeler                               # your app folder (e.g. ~/Documents/llm-csv-labeler)
ditto ~/Downloads/llm-csv-labeler .                     # copies the new files over the old ones
rm -rf ~/Downloads/llm-csv-labeler                      # tidy up, ready for next time
uv pip install --python .venv -r requirements.txt       # only changed packages
.venv/bin/python -m streamlit run app.py
```
Step-by-step version, with what's new: "Getting a new version" in INSTALL-MAC.md (sent with the zip).

## How to use

The top bar stays in view: the file and text column on the left, the API key status and session spend on the right, and the box for a new query below them. The query cards fill the page. **Save queries**, **Load queries** and **Download CSV** stay at the bottom of the window.

1. **Upload a CSV** in the top bar. **Data preview** (closed by default) shows the row count, the columns and the first 10 rows.
2. **Choose the text column** next to the file. The column with the longest text is picked automatically. If many rows in that column are empty, a warning names a better column. The **sidebar** lists every non-empty answer in that column, so you can read them while you write queries. Drag the sidebar's edge to make it wider or narrower. **Each text column keeps its own queries and results:** switch columns and back, and nothing is lost. The column picker shows how many queries each column has.
3. **Add a query.** There are two kinds, each with its own tab at the top:
   - **New LLM Query:** write a full sentence, for example *"Mentions a person getting hit by a car or other vehicle, or almost getting hit (near misses count)"*, and press Enter. The AI reads every row and answers yes or no.
   - **New Keyword Query:** type words separated by commas, for example *car, truck, bus, respect\**. A row matches if it contains any of them, as whole words, with upper/lower case ignored: "car" matches "Car", "car." and "car's" but not "scar" or "carpet". A **\*** at the end of a word matches every word that starts with it: *respect\** matches respect, respects, respected and respecting. Keyword queries are free and instant and need no API key; their confidence is always 1.00.

   A short column name is suggested, and you can edit it. Click **Add** and the query becomes a **card**.
4. **Test (20 rows)** shows which rows matched and which didn't, with confidence and cost. If the results look wrong, click **Edit**, reword the query and test again.
5. **Run** labels every row. A progress bar shows the batches. The card then shows "X of Y matched, Z not labelled".
6. **Add more queries** as needed. Each one gets its own card and its own columns. The card header shows the number of matches (e.g. *traffic_accidents: 45 matches*), also when the card is collapsed: click the arrow next to its name to collapse it to one line.
7. **See a query's rows in the sidebar:** click the sidebar icon on the right of a card (after a Test or Run). The sidebar then lists that query's rows with its label and confidence, with the matched rows highlighted in green. Click × to go back to all answers. (To get filter buttons instead, All / Matched / Not matched / Not labelled, set `SIDEBAR_FILTER_BUTTONS = True` in `labeler/config.py`.) Answers in the sidebar sit on white cells, for easy reading.
8. **Download CSV** gives the original file with 3 columns per finished query. Each query's columns sit right after the text column it was run on, including queries on other columns.
9. **Save queries** (`.json`) saves the queries of the current column, to reuse them on a new CSV; **Load queries** brings them back into the current column. Loaded queries never run by themselves.

**Long answers:** in every table, long answers wrap over a few lines. Double-click a cell to read the whole answer.

Each card shows the estimated cost of a test and of a full run before you click.

### Using Claude instead of OpenAI (optional)
1. Add a line with your Claude key to `.env`: `ANTHROPIC_API_KEY=sk-ant-...` (open it with `open -e .env`), then restart the app.
2. Click the **gear icon** (top right) and choose **Claude**. The key status shows which AI is in use.

Claude labels the rows the same way. **Its confidence score is built differently**, because Claude doesn't give the probabilities OpenAI's score comes from:
- Claude rates how sure it is for every row (50 to 100).
- Rows it's unsure about (under 80) are asked again 4 more times; the majority answer wins, and the score reflects how many answers agreed.
- Checked against hand-checked answers: low scores point to the rows worth checking.

Claude costs about twice as much as OpenAI here (still well under a cent per 1,000 short answers); the card's estimate includes the re-checks. Each AI keeps its own saved results, so switching back and forth never mixes them. Keyword queries don't use either AI.

### Output columns (per query, e.g. `kids`)
| Column | Values | Meaning |
|---|---|---|
| `kids` | 1, 0 or blank | Match, no match, or not labelled |
| `kids_conf` | 0.50 to 1.00 | How sure the model was. Close to 0.50 means unsure, so check those rows |
| `kids_note` | empty, trimmed, refused, blocked, failed | Only filled when a row needs attention |

The app never guesses. A row the model refuses or fails on is left blank and given a note, and the card status shows **Done with errors**.

### Writing good queries
- **Use a full sentence that says what counts.** "accident" alone is often misread; "Describes a person getting hurt in an accident" works.
- **Say how to treat borderline cases**, e.g. "(near misses count)".
- **"Does not mention…" queries are the hardest.** Always test them on 20 rows first.
- **Look at the lowest-confidence rows** in the results; that's where the model was unsure.
- **Use "Explicitly mentions…"** when you mean words actually in the answer. Otherwise the model may also count answers that only imply it (e.g. "Voter ID" counted as "stopping non-citizens").
- **Avoid subjective words** like "offensive". Say what counts, e.g. "swear words or name-calling".
- **Describe the opinion, not the search.** Write "Supports requiring voter ID to vote", not "rows with voter id". The second one missed about 1 in 10 matching answers in testing.

### Status of a card
Not run → Tested → Done (or Done with errors). Editing a finished query marks it **Out of date**: its columns leave the download until you click Run again.

## Speed and cost (`gpt-6-luna`)
About **13 seconds and $0.009 per 1,000 short answers**. Re-running an unchanged query is free, because results are cached in `cache.db`.

## Settings (`labeler/config.py`)
| Setting | Default | Change it when |
|---|---|---|
| `PROVIDER` / `ANTHROPIC_MODEL` | `"openai"` / `claude-haiku-5-5` | You want the app to start with Claude (`"anthropic"`), or Anthropic retires the model (update the 3 `ANTHROPIC_PRICE_*` values too). The gear icon switches provider while the app runs |
| `SIDEBAR_FILTER_BUTTONS` | `False` | You prefer filter buttons (All / Matched / Not matched / Not labelled) over highlighting in the sidebar |
| `VOTE_CHECK_BELOW` / `VOTE_CHECK_ROUNDS` | `0.80` / `4` | Claude only: which rows are re-checked and how many extra times. Higher or more costs more |
| `CLAUDE_CONFIDENCE_CALIBRATION` | from `scripts/calibrate_claude_confidence.py` | Re-run that script after changing `ANTHROPIC_MODEL` and paste its table here |
| `MODEL` / `REASONING_EFFORT` | `gpt-6-luna` / `"none"` | OpenAI retires a model. Pick a current one from OpenAI's deprecations page and update the 3 `PRICE_*` values. Older chat models (e.g. `gpt-4o-mini`) need `REASONING_EFFORT = None`; newer reasoning models need `"none"` (otherwise there's no confidence score). Run `python scripts/run_eval.py --model <name>` to compare accuracy first |
| `BATCH_SIZE` | 10 | Keep it at 20 or less. Bigger batches make answers drift between rows |
| `MAX_BATCH_ITEM_TOKENS` | 1000 | Long texts are batched by length so they stay accurate |
| `MAX_CONCURRENT` | 10 | Lower it (e.g. 5) if you see rate-limit errors |
| `TEST_SIZE` | 20 | Rows in a test run |
| `MAX_ROW_CHARS` | 2000 | Longer answers are trimmed (note `trimmed`) |

The model instructions are in `labeler/prompt_builder.py` (`SYSTEM_PROMPT`). Changing them automatically makes old cached results unused.

**After changing settings, restart the app and click "Clear cache" (gear icon, top right).**

## Troubleshooting
| Problem | Fix |
|---|---|
| "API key missing" | Check that `.env` exists in the project folder and contains `OPENAI_API_KEY=sk-...`, then restart the app |
| "OpenAI rejected the API key" | The key is wrong or was deleted. Create a new one in your OpenAI account |
| Rows marked `failed` / rate-limit errors | Lower `MAX_CONCURRENT` in `config.py`, then Run again. Only failed rows are re-sent |
| Blank page / the app won't load | Refresh, or open `http://localhost:8501` yourself. Try a private window (Cmd+Shift+N): if it works there, a browser extension is blocking it, so turn it off for `localhost`. Check that Terminal is still open. More fixes in "If something goes wrong" in INSTALL-MAC.md |
| An error after updating the code | Stop the app (Ctrl+C in Terminal) and run `.venv/bin/python -m streamlit run app.py` again. A browser refresh isn't enough |
| "This app needs Python 3.12 or newer" | The app was started with an older Python (for example conda's, or the Mac's own). Start it with `.venv/bin/python -m streamlit run app.py`. If `.venv` is missing, run the Setup commands again |
| Install fails / "requires a different Python" | Delete the `.venv` folder and run `uv venv --python 3.12` and `uv pip install --python .venv -r requirements.txt` again |
| Terminal shows `(base)` (conda is active) | That's fine if you use the commands above exactly: they always use the project's own `.venv`. Don't type `pip install`, `uv run` or `streamlit run` on their own, because with conda active they use conda's Python and its old packages. To switch conda off for the current window, run `conda deactivate` |
| A warning says "not running from its own environment", or `process() takes no keyword arguments` | The app was started with another Python (e.g. conda's base), which has different package versions. Start it with `.venv/bin/python -m streamlit run app.py`. If the error stays, delete `.venv` and repeat the install |
| CSV won't load | Save it as "CSV UTF-8" from Excel. The file needs a header row and at least one data row |
| Many rows "empty" | Those rows have no text in the chosen column. Pick the column named in the warning |
| Strange characters in Excel | The download is UTF-8 with BOM, so open it with a double-click rather than importing it as plain text |
| Model unavailable / "logprobs is not supported" | The model was retired, or `REASONING_EFFORT` doesn't fit it. See the `MODEL` row in Settings |
| Results lost after a browser refresh | Re-add or load your queries and click Run. Cached rows come back instantly at no cost |

## For developers
```bash
pytest                                       # all tests, no API cost
python scripts/run_labeling_cli.py --help    # run one query from the terminal
python scripts/run_eval.py                   # accuracy of 4 queries on sample.csv (~$0.005)
python sample_data/make_stress_sample.py && python scripts/run_stress_test.py   # 5,000-row stress test (~$0.19)
```
`sample_data/sample_queries.json` holds example queries to load in the app. See `docs/architecture.md` for how the code is organised.
