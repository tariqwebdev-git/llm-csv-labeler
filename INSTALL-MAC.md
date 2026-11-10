# Installing the LLM CSV Labeler on a Mac

This guide takes you from nothing to a running app. You do it **once**, and it takes about **10 minutes**.

You don't need to know anything about Python or programming. Every step tells you what to do, what to paste, and what you should see. If what you see doesn't match, go to [If something goes wrong](#if-something-goes-wrong) at the end.

> **Already using the app?** You don't need to install it again. Go straight to [Getting a new version](#getting-a-new-version).

## Before you start

You need:
- Your Mac, connected to the internet.
- Your OpenAI API key (it starts with `sk-`).

You will type a few commands into **Terminal**, the Mac's built-in command window. How it works:
- **Paste** a command with **Cmd+V**, then press **Enter** to run it.
- While a command runs, the window may look still for a while. That's normal, so wait until a new line ending in `%` appears.
- Copy each command exactly as shown, one at a time.
- If your Terminal lines start with `(base)`, you have Anaconda/conda installed. That's fine: the commands below always use the app's own environment, so conda can't interfere.

---

## Step 1: Get the project folder

1. Save the zip file you received (e.g. `llm-csv-labeler-v1.0.1.zip`) to your **Downloads** folder.
2. Double-click it. A folder named **`llm-csv-labeler`** appears next to it. (Safari sometimes unzips it for you; then the folder is already there.)
3. Drag the `llm-csv-labeler` folder into your **Documents** folder.

✅ **You should see:** a folder named `llm-csv-labeler` in Documents, containing `app.py`, `README.md` and this guide.

## Step 2: Open Terminal

Press **Cmd+Space**, type **Terminal**, and press **Enter**.

✅ **You should see:** a small window with a line ending in `%`. Keep it open.

## Step 3: Install uv (the tool that sets everything up)

`uv` is a small free tool. It installs the correct Python version and everything else the app needs, and it doesn't touch anything else on your Mac or ask for your password.

Paste:
```
curl -LsSf https://astral.sh/uv/install.sh | sh
```

✅ **You should see:** a few lines ending with **`everything's installed!`**

Now **close Terminal completely** (Cmd+Q) and **open it again** (Step 2). This step matters: the new window is the one that knows about uv.

## Step 4: Go to the project folder

Type `cd` followed by **one space** (don't press Enter yet). Then drag the `llm-csv-labeler` folder from Finder onto the Terminal window. Its location appears after `cd `. Now press **Enter**.

Or simply paste:
```
cd ~/Documents/llm-csv-labeler
```

Check that you're in the right place. Paste:
```
ls
```

✅ **You should see:** a list that includes `app.py`, `README.md` and `requirements.txt`.

If your Mac asks *"Terminal would like to access files in your Documents folder"*, click **Allow**.

## Step 5: Install Python and the app's packages

Paste:
```
uv venv --python 3.12
```

✅ **You should see:** `Using CPython 3.12…` and `Creating virtual environment at: .venv`. If Python 3.12 isn't on your Mac yet, uv downloads it first, which takes a moment. You can ignore the "Activate with…" line.

Then paste:
```
uv pip install --python .venv -r requirements.txt
```

✅ **You should see:** a list of names with `+` in front, and a line like **`Installed 52 packages`** (the number may differ slightly). The first time takes 1–2 minutes.

Check that the app's own Python is ready. Paste:
```
.venv/bin/python --version
```

✅ **You should see:** `Python 3.12` followed by a number, e.g. `Python 3.12.10`.

## Step 6: Add your OpenAI key

Paste:
```
cp .env.example .env
open -e .env
```

TextEdit opens a small file. Its first line is `OPENAI_API_KEY=`

1. Click at the end of that first line and paste your OpenAI key right after the `=`, with **no spaces**. It should look like `OPENAI_API_KEY=sk-...`
2. Press **Cmd+S** to save, then close TextEdit.

Your keys stay only in this file on your Mac. They're never shown in the app, and each is sent only to its own company (OpenAI or Anthropic).

*Optional:* to use Claude as well, paste your Claude key after `ANTHROPIC_API_KEY=` on the last line of the same file. You can skip this; OpenAI is used unless you pick Claude in the app.

## Step 7: Start the app

Paste:
```
.venv/bin/python -m streamlit run app.py
```

If it asks for your **Email**, just press **Enter**. This only happens the first time.

✅ **You should see:** in Terminal, `You can now view your Streamlit app in your browser` and `Local URL: http://localhost:8501`. Your browser opens the app, and the top right corner shows a green **API key**.

**Keep the Terminal window open while you use the app.** Closing it stops the app.

## Step 8: Quick check (costs less than 1 cent)

1. In the app, **upload** `sample_data/sample.csv` from the project folder.
2. Click **Load queries** at the bottom of the window and choose `sample_data/sample_queries.json`.
3. On one of the query cards, click **Test (20 rows)**.

✅ **You should see:** after a few seconds, tables of matched and not matched rows. Everything works, and you're done.

---

## Every day after that

1. Open Terminal (Cmd+Space, type Terminal, Enter).
2. Paste these two lines:
   ```
   cd ~/Documents/llm-csv-labeler
   .venv/bin/python -m streamlit run app.py
   ```
   If your app is in another folder (for example `~/Code/llm-csv-labeler`), use that folder in the first line.
3. The app opens in your browser.

**To stop the app:** click the Terminal window and press **Ctrl+C**, or simply close the window.

## Getting a new version

You don't need to install everything again. Your key, your saved results and the installed packages stay where they are.

**What's new in this version**
- **Keyword queries:** a second tab, **New Keyword Query**. Type words separated by commas (e.g. *car, truck, bus*); a row matches if it contains any of them. Free, instant, no API key needed.
- **Each text column has its own queries and results.** Switch columns and back, and nothing is lost.
- **See one query's rows in the sidebar:** click the sidebar icon on a card. Matched rows are green, with a filter (All / Matched / Not matched / Not labelled).
- **Claude as an option:** add `ANTHROPIC_API_KEY=` with your Claude key to `.env` (open it with `open -e .env`), restart, then pick **Claude** in the gear menu. Claude gives labels without a confidence score for now.
- The query list is now the main part of the page.
- Upload, the text column and the box for a new query stay at the top. Your API key status and what the session has cost sit small in the top right; the gear icon next to them has **Clear cache**.
- **Save queries**, **Load queries** and **Download CSV** are small buttons at the bottom of the window. Only the query cards scroll between the two.
- Click the arrow next to a card's name to collapse it to one line.
- The sidebar lists every answer in the chosen text column, so you can keep reading while you write queries.
- Long answers wrap in every table. Double-click a cell to read the whole answer.
- In the download, each query's new columns sit right after the text column.

**How to update**
1. Stop the app: click the Terminal window and press **Ctrl+C**.
2. Put the new zip in your **Downloads** folder (no need to unzip it).
3. Paste these lines one at a time and press Enter after each:
   ```
   cd ~/Downloads && unzip -o 'llm-csv-labeler-v*.zip'
   cd ~/Code/llm-csv-labeler
   ditto ~/Downloads/llm-csv-labeler .
   rm -rf ~/Downloads/llm-csv-labeler
   uv pip install --python .venv -r requirements.txt
   .venv/bin/python -m streamlit run app.py
   ```
   - The second line goes to the folder where your app is. If you installed it in **Documents** (Step 1), use `cd ~/Documents/llm-csv-labeler` instead.
   - The third line copies the new files over the old ones (the `.` means "this folder"). Your `.env` key, your saved results and the installed packages are kept.
   - If Safari already unzipped the file (there's a `llm-csv-labeler` folder in Downloads), skip the first line.
   - The `rm` line only removes the unzipped copy in Downloads.

✅ **You should see:** the app opens as usual, with the new layout. The install line finishes in a few seconds and only lists packages that changed (or says everything is already installed).

---

## If something goes wrong

| What you see | What to do |
|---|---|
| **Blank page, or the app won't load in the browser** | 1. Wait 10 seconds and refresh the page (Cmd+R). 2. Type `http://localhost:8501` into the address bar yourself. 3. Open a **private window** (Safari or Chrome: **Cmd+Shift+N**) and go to `http://localhost:8501`. If it works there, a browser extension (like an ad blocker) is blocking the app: turn it off for `localhost`, or keep using a private window. 4. Try a different browser (Safari or Chrome). 5. Check that the Terminal window from Step 7 is still open. |
| The browser didn't open by itself | Copy the address after `Local URL:` in Terminal (e.g. `http://localhost:8501`) into your browser. |
| The address shows **8502** (or another number) instead of 8501 | The app is already running in another Terminal window. Use the address shown, or close the other Terminal window. |
| `command not found: uv` | Close Terminal completely (Cmd+Q) and open it again. If it still appears, paste `source $HOME/.local/bin/env` and try again. |
| `No such file or directory` or `File not found: requirements.txt` | Terminal is not in the project folder. Repeat Step 4; `ls` must show `app.py`. |
| An error during Step 5 | Check your internet connection and paste the same command again. It's safe to repeat. |
| A yellow warning says **"The app is not running from its own environment"**, or an error like `process() takes no keyword arguments` | The app was started with another Python (often conda's `(base)`). Stop it (Ctrl+C) and start it with the Step 7 command: `.venv/bin/python -m streamlit run app.py`. If the error stays, rebuild the environment: paste `rm -rf .venv`, repeat Step 5, then Step 7. |
| `.venv/bin/python: No such file or directory` | Step 5 wasn't finished in this folder. Repeat Step 4 and Step 5. |
| Terminal asks for an **Email** | Press Enter. It's optional. |
| **API key missing** (red box at the top) | The `.env` file is missing or the key wasn't saved. Repeat Step 6, then stop the app (Ctrl+C) and start it again (Step 7). |
| **OpenAI rejected the API key** | The key was mistyped or deleted. Paste it again (Step 6), or create a new key in your OpenAI account. Then restart the app. |
| Every row is marked **failed** | Your OpenAI account may be out of credit or at its spending limit. Check **Billing** on the OpenAI website, then click **Run** again. Only the failed rows are re-sent. |
| The app suddenly stopped working | The Terminal window was closed. Start the app again (see "Every day after that"). |
| Strange characters when opening the result in Excel | Open the downloaded CSV with a double-click instead of using Excel's import. |
| Something else | Stop the app (Ctrl+C), start it again (Step 7), and refresh the browser. |

For how to use the app and write good queries, see [README.md](README.md).
