# Stress test results

Date: 2026-11-04 · Model: `gpt-4o-mini` · Batch size 50 · Concurrency 10

Data: `sample_data/stress.csv` (5,000 unique rows; 250 matches only at the end; 300 long rows). Each scenario uses a fresh cache except E and F, which reuse A's.

| Scenario | Query | Rows | Est $ | Actual $ | Diff | $ / 1k rows | Time s | Requests (batches) | Notes | Accuracy |
|---|---|---|---|---|---|---|---|---|---|---|
| A. 5,000 rows, matches only in last 250 | Mentions a person getting hit by a car or other vehicle | 5000 | 0.0440 | 0.0440 | +0% | 0.0088 | 40.48 | 100 (100) | none | 4990/5000 (99.8%); found 240/250 at end, 0 false positives before |
| B. Negation query | Does NOT mention any vehicle (car, bus, train, truck, taxi, etc.) | 5000 | 0.0441 | 0.0456 | +4% | 0.0091 | 47.22 | 132 (100) | none | 4725/5000 (94.5%) |
| C. Two-condition query | A child was hurt AND the speaker blames the city | 5000 | 0.0440 | 0.0453 | +3% | 0.0091 | 43.98 | 106 (100) | none | 4917/5000 (98.3%) |
| D. 300 long rows (~1,500 chars) | Mentions a person getting hit by a car or other vehicle | 300 | 0.0135 | 0.0135 | +0% | 0.0450 | 7.59 | 6 (6) | none | 300/300 (100.0%) |
| E. Re-run A (cache) | Mentions a person getting hit by a car or other vehicle | 5000 | 0.0000 | 0.0000 | n/a | 0.0000 | 0.12 | 0 (0) | none | 4990/5000 (99.8%) |
| F. A with one word changed | Mentions someone getting hit by a car or other vehicle | 5000 | 0.0440 | 0.0440 | +0% | 0.0088 | 38.96 | 100 (100) | none | 4988/5000 (99.8%) |

## Findings
- **Cost depends only on row count and text length.** Match position and query difficulty make no real difference: A, B, C and F all cost **$0.0088–0.0091 per 1,000 rows**.
- **Matches at the end of the file are found.** 240 of the 250 matches in the last rows were found, with 0 false positives in the 4,750 rows before them.
- **Speed:** 5,000 rows in about 40 s, which is about 8 s per 1,000 rows.
- **Long rows** (~1,500 chars) cost about 5× more per row ($0.045 per 1,000), in line with their length. The estimate was exact.
- **Cache:** the re-run cost $0.00 and took 0.1 s. A query with one word changed is charged in full, as designed.
- **Estimate gap explained:** the extra cost comes from retry requests. The negation query needed 32 retries (+4%) and the two-condition query needed 6 (+3%). Simple queries needed none.
- **Accuracy:** 99.8% (A), 94.5% (B, negation, the hardest), 98.3% (C), 100% (D).
