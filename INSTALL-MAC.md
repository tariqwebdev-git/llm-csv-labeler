# Installing the LLM CSV Labeler on a Mac

This guide takes you from nothing to a running app. You do it **once**, and it takes about **10 minutes**.

You don't need to know anything about Python or programming. Every step tells you what to do, what to paste, and what you should see. If what you see doesn't match, go to [If something goes wrong](#if-something-goes-wrong) at the end.

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

TextEdit opens a small file with one line: `OPENAI_API_KEY=`

1. Click at the end of that line and paste your key right after the `=`, with **no spaces**. It should look like `OPENAI_API_KEY=sk-...`
2. Press **Cmd+S** to save, then close TextEdit.

Your key stays only in this file on your Mac. It's never shown in the app or sent anywhere except OpenAI.

## Step 7: Start the app

Paste:
```
.venv/bin/python -m streamlit run app.py
```

If it asks for your **Email**, just press **Enter**. This only happens the first time.

✅ **You should see:** in Terminal, `You can now view your Streamlit app in your browser` and `Local URL: http://localhost:8501`. Your browser opens the app, and the left sidebar shows a green **API key found**.

**Keep the Terminal window open while you use the app.** Closing it stops the app.

## Step 8: Quick check (costs less than 1 cent)

1. In the app, **upload** `sample_data/sample.csv` from the project folder.
2. In **Save or load queries**, load `sample_data/sample_queries.json`.
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
3. The app opens in your browser.

**To stop the app:** click the Terminal window and press **Ctrl+C**, or simply close the window.

## Getting a new version

1. In Documents, rename the old folder to `llm-csv-labeler-old`.
2. Unzip the new version and move it into Documents (Step 1).
3. Copy your `.env` file from the old folder into the new one. It's hidden in Finder: press **Cmd+Shift+.** (full stop) to show hidden files.
4. In Terminal, run Step 4 and Step 5 again, then start the app as usual.

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
| The sidebar says **"The app is not running from its own environment"**, or an error like `process() takes no keyword arguments` | The app was started with another Python (often conda's `(base)`). Stop it (Ctrl+C) and start it with the Step 7 command: `.venv/bin/python -m streamlit run app.py`. If the error stays, rebuild the environment: paste `rm -rf .venv`, repeat Step 5, then Step 7. |
| `.venv/bin/python: No such file or directory` | Step 5 wasn't finished in this folder. Repeat Step 4 and Step 5. |
| Terminal asks for an **Email** | Press Enter. It's optional. |
| **API key missing** in the sidebar | The `.env` file is missing or the key wasn't saved. Repeat Step 6, then stop the app (Ctrl+C) and start it again (Step 7). |
| **OpenAI rejected the API key** | The key was mistyped or deleted. Paste it again (Step 6), or create a new key in your OpenAI account. Then restart the app. |
| Every row is marked **failed** | Your OpenAI account may be out of credit or at its spending limit. Check **Billing** on the OpenAI website, then click **Run** again. Only the failed rows are re-sent. |
| The app suddenly stopped working | The Terminal window was closed. Start the app again (see "Every day after that"). |
| Strange characters when opening the result in Excel | Open the downloaded CSV with a double-click instead of using Excel's import. |
| Something else | Stop the app (Ctrl+C), start it again (Step 7), and refresh the browser. |

For how to use the app and write good queries, see [README.md](README.md).
