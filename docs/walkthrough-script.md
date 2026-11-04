# Walkthrough video script (≤ 5 minutes)

Record with `sample_data/sample.csv` and `sample_data/sample_queries.json`. About $0.01 of API use.

| Time | Show | Say |
|---|---|---|
| 0:00 | Terminal: `source venv/bin/activate`, `streamlit run app.py` | "Start the app; it opens in the browser. The sidebar shows the key status, the model and the spend." |
| 0:30 | Upload `sample.csv` | "Upload any CSV. You see the rows and columns. The text column is picked automatically; change it here." |
| 0:50 | Choose the `housing_open` column, then back | "If many rows are empty in a column, a warning tells you and names a better one." |
| 1:10 | Type `accident` in New query | "Short queries are often misread, so the app warns you. Write a full sentence instead." |
| 1:30 | Add "Mentions a person getting hit by a car or other vehicle, or almost getting hit (near misses count)" | "The column name is suggested. Each query becomes a card with a test and a full-run cost estimate." |
| 2:00 | Click **Test (20 rows)** | "Twenty fixed rows: matched and not matched, with confidence. Check that the wording does what you mean." |
| 2:30 | Click **Edit**, change a word, **Save** | "Edit on the card. A finished query becomes Out of date until you run it again." |
| 2:50 | Click **Run** | "The full run shows progress. The box shows X of Y matched, Z not labelled, the notes and the cost." |
| 3:20 | Open the results expander | "Rows needing attention first, then lowest confidence. Near 0.50 means unsure, so check those." |
| 3:40 | Load `sample_queries.json`, run one more query | "Save queries to reuse on the next file. Loaded queries never run by themselves." |
| 4:10 | **Delete** a card (confirm) | "Delete asks for confirmation." |
| 4:25 | **Download CSV**, open it in Excel | "The download is your original file plus 3 columns per finished query: label, confidence and note." |
| 4:45 | Sidebar **Clear cache** | "Re-running the same query is free thanks to the cache. Clear it after changing settings." |
