# Real-data test: Alex's election survey (`data/elections_sample.csv`)

The data stays local in `data/` (git-ignored). This report contains **counts only, no answer text**.

## File
- 1,567 rows; columns: a blank-named id, "How should we improve elections?" and "Why do you think that?".
- Read correctly: multi-line cells, `NA` kept as text, encoding OK.
- **Bug found and fixed:** the blank first header was written back as `Unnamed: 0`. `csv_io` now restores the original headers on download (`test_blank_header_survives_upload_and_download`). The round trip keeps all 1,567 rows, their order and the identical text.
- The app auto-picks "Why do you think that?" (the longest text). The main answers are in "How should we improve elections?", so Alex picks it from the dropdown.
- Empty rows: 39 in column 1, 131 in column 2. Both are flagged by the empty-rows warning and noted `empty`.

## Accuracy
Hand-checked reference: 57–66 rows per query, labelled by Tariq. A fixed random sample, plus 12 known abusive rows for the insult query; ambiguous rows weren't scored. **This is provisional until Alex's own 20 labelled rows arrive.**

| Query (column) | Accuracy | Time (1,567 rows) | Cost |
|---|---|---|---|
| Supports requiring voter ID or photo identification to vote (Q1) | **100%** (57/57) | 22 s | $0.013 |
| Wants to abolish, replace or change the electoral college (Q1) | **100%** (60/60) | 20 s | $0.013 |
| Mentions foreign interference or hacking of elections (Q1) | **100%** (59/59) | 19 s | $0.013 |
| Mentions stopping illegal immigrants or non-citizens from voting (Q1) | 86.7% | 20 s | $0.013 |
| ↳ reworded: "**Explicitly** mentions illegal immigrants, non-citizens or citizenship in connection with voting" | **96.7%** (1 of 2 errors at confidence 0.56) | 19 s | $0.013 |
| Contains insults, swearing or offensive language (Q2) | 89.4%; **all 13 real insults found** | 20 s | $0.016 |
| ↳ reworded: "Contains insults, name-calling or swear words" | 90.9% | 19 s | $0.016 |

### What the errors were
- **Non-citizen query, original wording:** plain "Voter ID" answers were counted as stopping non-citizens (the model inferred the purpose). Adding "explicitly" fixed almost all of them.
- **Insult query:** every error is a **false positive**: a strong anti-immigrant or anti-government opinion without an actual insult or swear word. "Insult/offensive" is subjective, so Alex should define what counts, e.g. "swear words or name-calling of a person or group". No real insult was missed.

## Abusive text
**No row was refused, blocked or failed** across 5 queries × 1,567 rows of real, often abusive answers. The only notes were `empty` and `trimmed`, so every answer with text got a label.

## Performance
About 20 s and about $0.013 per query for 1,567 rows (≈ 13 s and $0.008 per 1,000).

## Lessons for query writing (added to the README)
- Use **"explicitly mentions…"** when you mean words actually in the answer, not an implied purpose.
- Avoid subjective words ("offensive"). Say what counts ("swear words or name-calling").
