# Walkthrough video script (≤ 5 minutes)

Record on Alex's election CSV (`data/elections_sample.csv`: local only, git-ignored, never committed). About $0.03 of API use.

**Before recording:** start the app, open the **gear icon** (top right) and click **Clear cache** (so runs show real progress, not instant cached results), and close other browser tabs.

| Time | Show | Say |
|---|---|---|
| 0:00 | Terminal: `cd ~/Documents/llm-csv-labeler`, `.venv/bin/python -m streamlit run app.py` | "Start the app; it opens in the browser. Top right: the key status and what this session has cost." |
| 0:25 | Upload the election CSV in the top bar | "Upload any CSV. The file, the text column and the new-query box stay at the top while you scroll." |
| 0:40 | The app picks "Why do you think that?". Switch to **"How should we improve elections?"** | "The column with the longest text is picked automatically; change it here. If a column has many empty rows, a warning tells you." |
| 0:55 | Scroll the sidebar; double-click a long answer | "The sidebar lists every answer in that column, to read while you write queries. Double-click any cell to read a long answer in full. **Data preview** shows the whole file when you need it." |
| 1:15 | Type `voter id` in the query box | "Short queries are often misread, so the app warns you. Describe the opinion in a full sentence instead." |
| 1:30 | Add "Supports requiring voter ID or photo identification to vote" | "The column name is suggested. Each query becomes a card with a test and a full-run cost estimate." |
| 1:50 | Click **Test (20 rows)** | "Twenty fixed rows: matched and not matched, with confidence. Check that the wording does what you mean." |
| 2:15 | Click **Edit**, change a word, **Save** | "Edit on the card. A finished query becomes Out of date until you run it again." |
| 2:35 | Click **Run** | "The full run shows progress. The box shows X of Y matched, Z not labelled, the notes and the cost." |
| 3:00 | Open the results expander | "Rows needing attention first, then lowest confidence. Near 0.50 means unsure, so check those." |
| 3:20 | Add "Wants to abolish, replace or change the electoral college", click **Run**, then collapse the first card with its arrow | "Add as many queries as you like; each gets its own columns. Collapse a card to just its name to keep the page tidy." |
| 3:50 | Bottom bar: **Save queries**, point at **Load queries** | "Save your queries to reuse them on the next file. Loaded queries never run by themselves." |
| 4:05 | **Delete** a card (confirm) | "Delete asks for confirmation." |
| 4:15 | **Download CSV**, open it in Excel | "Your original file, with each query's label, confidence and note right next to the answers column." |
| 4:40 | Gear icon → **Clear cache** | "Re-running the same query is free thanks to the cache. Clear it after changing settings." |
