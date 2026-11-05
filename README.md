# LLM CSV Labeler

Upload a CSV, write plain-English yes/no queries, and download your file with three new columns per query: a label (1/0), a confidence score and a note.

## Setup (macOS)

**New to Terminal? Follow [INSTALL-MAC.md](INSTALL-MAC.md)**: a step-by-step guide with what you should see at each step.

Short version. [uv](https://docs.astral.sh/uv/) installs Python 3.12 and the packages, whatever Python your Mac has:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh      # once; then open a new Terminal window
cd ~/Documents/llm-csv-labeler
uv venv --python 3.12
uv pip install -r requirements.txt
cp .env.example .env && open -e .env                  # paste your key after OPENAI_API_KEY=
uv run streamlit run app.py                           # opens the app in your browser
```
Next time, you only need the `cd` line and `uv run streamlit run app.py`.

## How to use

1. **Upload a CSV.** You'll see the row count, the columns and the first 10 rows.
2. **Choose the text column.** The column with the longest text is picked automatically, and you can change it. If many rows in that column are empty, a warning names a better column.
3. **Add a query.** Write it as a full sentence, for example *"Mentions a person getting hit by a car or other vehicle, or almost getting hit (near misses count)"*. A short column name is suggested, and you can edit it. Each query becomes a **card**.
4. **Test (20 rows)** shows which rows matched and which didn't, with confidence and cost. If the results look wrong, click **Edit**, reword the query and test again.
5. **Run** labels every row. A progress bar shows the batches. The card then shows "X of Y matched, Z not labelled".
6. **Add more queries** as needed. Each one gets its own card and its own columns.
7. **Download** the original CSV with the columns of every finished query added.
8. **Save the queries** (`.json`) to reuse them on a new CSV. Loaded queries never run by themselves.

Each card shows the estimated cost of a test and of a full run before you click. The sidebar shows the total spend for this session.

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
| `MODEL` / `REASONING_EFFORT` | `gpt-6-luna` / `"none"` | OpenAI retires a model. Pick a current one from OpenAI's deprecations page and update the 3 `PRICE_*` values. Older chat models (e.g. `gpt-4o-mini`) need `REASONING_EFFORT = None`; newer reasoning models need `"none"` (otherwise there's no confidence score). Run `python scripts/run_eval.py --model <name>` to compare accuracy first |
| `BATCH_SIZE` | 10 | Keep it at 20 or less. Bigger batches make answers drift between rows |
| `MAX_BATCH_ITEM_TOKENS` | 1000 | Long texts are batched by length so they stay accurate |
| `MAX_CONCURRENT` | 10 | Lower it (e.g. 5) if you see rate-limit errors |
| `TEST_SIZE` | 20 | Rows in a test run |
| `MAX_ROW_CHARS` | 2000 | Longer answers are trimmed (note `trimmed`) |

The model instructions are in `labeler/prompt_builder.py` (`SYSTEM_PROMPT`). Changing them automatically makes old cached results unused.

**After changing settings, restart the app and click "Clear cache" in the sidebar.**

## Troubleshooting
| Problem | Fix |
|---|---|
| "API key missing" | Check that `.env` exists in the project folder and contains `OPENAI_API_KEY=sk-...`, then restart the app |
| "OpenAI rejected the API key" | The key is wrong or was deleted. Create a new one in your OpenAI account |
| Rows marked `failed` / rate-limit errors | Lower `MAX_CONCURRENT` in `config.py`, then Run again. Only failed rows are re-sent |
| Blank page / the app won't load | Refresh, or open `http://localhost:8501` yourself. Try a private window (Cmd+Shift+N): if it works there, a browser extension is blocking it, so turn it off for `localhost`. Check that Terminal is still open. More fixes in [INSTALL-MAC.md](INSTALL-MAC.md#if-something-goes-wrong) |
| An error after updating the code | Stop the app (Ctrl+C in Terminal) and run `uv run streamlit run app.py` again. A browser refresh isn't enough |
| Install fails / "requires a different Python" | Delete the `.venv` folder and run `uv venv --python 3.12` and `uv pip install -r requirements.txt` again |
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
