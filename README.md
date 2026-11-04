# LLM CSV Labeler

Upload a CSV, write plain-English yes/no queries, and download your file with a label column, a confidence column and a note column added for each query.

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

1. **Upload a CSV.** You'll see the row count, the column names and the first rows.
2. **Choose the text column.** The column with the longest text is picked automatically, and you can change it.
3. **Write a query**, for example *"Mentions a person getting hit by a car or other vehicle, or almost getting hit (near misses count)"*. A short column name is suggested, and you can edit it.
4. Check the **estimated cost**, then click **Run**. A progress bar shows the batches.
5. **Review the result:** the box shows how many rows matched and how many weren't labelled. The table lists the rows with the lowest confidence first.
6. **Download** the original CSV with the new columns added.

### Output columns
| Column | Values | Meaning |
|---|---|---|
| `name` | 1, 0 or blank | Match, no match, or not labelled |
| `name_conf` | 0.50 to 1.00 | How sure the model was. Close to 0.50 means unsure |
| `name_note` | empty, trimmed, refused, blocked, failed | Only filled when a row needs attention |

The app never guesses a label. A row the model refuses or fails on is left blank and given a note.

### Tips
- Say exactly what counts. For example, add "near misses count" if they should be a match.
- Queries with "not" (negation) are the hardest for the model, so check their results carefully.
- Re-running the same query on the same rows is free, because results are cached in `cache.db`.

## Settings
Everything you may want to change is in `labeler/config.py`: the model, prices, batch size, concurrency and row limits.

## Troubleshooting
| Problem | Fix |
|---|---|
| "API key missing" | Check that `.env` exists in the project folder and contains `OPENAI_API_KEY=sk-...`, then restart the app |
| "OpenAI rejected the API key" | The key is wrong or was deleted. Create a new one in your OpenAI account |
| Rate limit / slow runs | Lower `MAX_CONCURRENT` in `config.py` (for example to 5) |
| CSV won't load | Save it as "CSV UTF-8" from Excel. The file needs a header row and at least one data row |
| Strange characters in Excel | The download is UTF-8 with BOM, so open it with a double-click rather than importing it as plain text |
| Model unavailable | Set another standard chat model in `MODEL` in `config.py` (not a reasoning model) |

## For developers
```bash
pytest                                   # all tests, no API cost
python scripts/run_labeling_cli.py --help  # run a query from the terminal
```
See `CLAUDE.md` and `docs/` for the architecture and milestone notes.
