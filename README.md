# LLM CSV Labeler

Upload a CSV, write plain-English yes/no queries, and download your file with three new columns per query: a label (1/0), a confidence score and a note.

## Setup (macOS)

1. **Python 3.10 or newer.** In Terminal, run `python3 --version`. If it's missing or older, install it from [python.org](https://www.python.org/downloads/).
2. **Get the project folder** (GitHub or zip) and open Terminal inside it.
3. **Create a virtual environment and install:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
4. **Add your OpenAI API key:** copy `.env.example` to `.env`, then paste your key after `OPENAI_API_KEY=`.
   ```bash
   cp .env.example .env
   open -e .env
   ```
5. **Start the app:**
   ```bash
   streamlit run app.py
   ```
   It opens in your browser. Next time, you only need `source venv/bin/activate` and `streamlit run app.py`.

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

### Status of a card
Not run → Tested → Done (or Done with errors). Editing a finished query marks it **Out of date**: its columns leave the download until you click Run again.

## Speed and cost (`gpt-4o-mini`)
About **15 seconds and $0.013 per 1,000 short answers**. Re-running an unchanged query is free, because results are cached in `cache.db`.

## Settings (`labeler/config.py`)
| Setting | Default | Change it when |
|---|---|---|
| `MODEL` | `gpt-4o-mini` | You need higher accuracy on hard queries: `gpt-4o` is about 16× the cost (also update the 3 `PRICE_*` values: 2.50 / 1.25 / 10.00) |
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
| An error after updating the code | Stop the app (Ctrl+C in Terminal) and run `streamlit run app.py` again. A browser refresh isn't enough |
| CSV won't load | Save it as "CSV UTF-8" from Excel. The file needs a header row and at least one data row |
| Many rows "empty" | Those rows have no text in the chosen column. Pick the column named in the warning |
| Strange characters in Excel | The download is UTF-8 with BOM, so open it with a double-click rather than importing it as plain text |
| Model unavailable | Set another standard chat model in `MODEL` in `config.py` (not a reasoning model: confidence needs log probabilities) |
| Results lost after a browser refresh | Re-add or load your queries and click Run. Cached rows come back instantly at no cost |

## For developers
```bash
pytest                                       # all tests, no API cost
python scripts/run_labeling_cli.py --help    # run one query from the terminal
python scripts/run_eval.py                   # accuracy of 4 queries on sample.csv (~$0.005)
python sample_data/make_stress_sample.py && python scripts/run_stress_test.py   # 5,000-row stress test (~$0.19)
```
`sample_data/sample_queries.json` holds example queries to load in the app. See `CLAUDE.md` and `docs/` for the architecture and milestone notes.
