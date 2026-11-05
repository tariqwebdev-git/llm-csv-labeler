# Walkthrough video script (≤ 5 minutes)

Record on Alex's election CSV (`data/elections_sample.csv`: local only, git-ignored, never committed). About $0.03 of API use.

**Before recording:** start the app, click **Clear cache** in the sidebar (so runs show real progress, not instant cached results), and close other browser tabs.

| Time | Show | Say |
|---|---|---|
| 0:00 | Terminal: `cd ~/Documents/llm-csv-labeler`, `uv run streamlit run app.py` | "Start the app; it opens in the browser. The sidebar shows the key status, the model and the spend." |
| 0:30 | Upload the election CSV | "Upload any CSV. You see the rows and columns, and the first rows of the file." |
| 0:50 | The app picks "Why do you think that?". Switch to **"How should we improve elections?"** | "The column with the longest text is picked automatically; change it here. If a column has many empty rows, a warning tells you." |
| 1:10 | Type `voter id` in New query | "Short queries are often misread, so the app warns you. Describe the opinion in a full sentence instead." |
| 1:30 | Add "Supports requiring voter ID or photo identification to vote" | "The column name is suggested. Each query becomes a card with a test and a full-run cost estimate." |
| 2:00 | Click **Test (20 rows)** | "Twenty fixed rows: matched and not matched, with confidence. Check that the wording does what you mean." |
| 2:30 | Click **Edit**, change a word, **Save** | "Edit on the card. A finished query becomes Out of date until you run it again." |
| 2:50 | Click **Run** | "The full run shows progress. The box shows X of Y matched, Z not labelled, the notes and the cost." |
| 3:20 | Open the results expander | "Rows needing attention first, then lowest confidence. Near 0.50 means unsure, so check those." |
| 3:40 | Add "Wants to abolish, replace or change the electoral college", click **Run** | "Add as many queries as you like; each one gets its own columns." |
| 4:00 | **Download queries (.json)**, point at **Load queries** | "Save your queries to reuse them on the next file. Loaded queries never run by themselves." |
| 4:15 | **Delete** a card (confirm) | "Delete asks for confirmation." |
| 4:25 | **Download CSV**, open it in Excel | "The download is your original file plus 3 columns per finished query: label, confidence and note." |
| 4:45 | Sidebar **Clear cache** | "Re-running the same query is free thanks to the cache. Clear it after changing settings." |
