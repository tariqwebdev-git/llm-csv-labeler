# Acceptance checklist (plan section 8)

✅ means done, with the evidence named. ⏳ means it needs Alex: his data, his hand-labelled rows, or his machine.
Tests run with `pytest` and cost nothing. Live checks used the real API.

## Functional
| Item | Status | Evidence |
|---|---|---|
| CSV with 1,000 rows uploads and previews correctly | ✅ | Alex's real file (1,567 rows, blank header kept on download); `merged_all.csv` (1,030 rows) and `stress.csv` (5,000) in the app; `test_upload_shows_preview_and_picks_text_column` |
| Excel-exported CSV (Windows-1252, semicolons) uploads correctly | ✅ | `test_excel_export_cp1252_semicolons` |
| Commas, quotes and line breaks inside cells survive upload and download | ✅ | `test_quotes_commas_and_line_breaks_round_trip` |
| Text column can be chosen and changed | ✅ | `test_empty_rows_warning_names_better_column` (changes column) |
| Query can be created, tested, run, edited, re-run and deleted | ✅ | `test_add_two_queries_as_cards`, `test_test_run_uses_20_rows`, `test_full_run_counts_box_and_download`, `test_edit_marks_out_of_date`, `test_delete_needs_confirmation` |
| Test run uses 20 rows and shows matched / unmatched previews | ✅ | `test_test_run_uses_20_rows`; manual browser check |
| Full run labels every row with 1, 0 or blank plus a note | ✅ | `test_labels_every_row_with_confidence`, `test_empty_and_trimmed_notes`; `sample.csv` download |
| Confidence column is filled and between 0.50 and 1.00 | ✅ | `test_parses_lines_and_confidence`; live runs (0 labels without confidence) |
| Results preview sorts by lowest confidence first | ✅ | `ui/result_tables.full_preview` (attention → low confidence → empty last) |
| Estimated cost before every run; actual cost after | ✅ | `test_card_shows_test_and_full_estimates`; result box shows actual cost |
| Re-running an unchanged query uses the cache and costs $0.00 | ✅ | `test_duplicates_sent_once_and_rerun_uses_cache`; live: 220 rows, $0.00 |
| Queries save to JSON and load on a different CSV | ✅ | `test_round_trip_loads_as_not_run`, `test_load_queries_json_adds_not_run_cards` |
| Download has the same rows, order and original columns, plus new columns | ✅ | `test_full_run_counts_box_and_download`, `test_adds_three_columns_without_changing_original`; new columns sit right after the text column (`test_download_puts_new_columns_after_text_column`, live check 2026-11-09) |
| Downloaded CSV opens correctly in Excel | ✅ | UTF-8 with BOM (`test_output_has_bom_for_excel`); ⏳ confirm on Alex's Mac |

## Accuracy
| Item | Status | Evidence |
|---|---|---|
| On 20 hand-labelled rows per query (from Alex), labels agree on at least [X] of 20 | ⏳ | Needs Alex's rows and his choice of X. **His real election file, checked by Tariq (57–66 rows/query): 100% / 100% / 100% / 96.7% / 90.9%** (`docs/milestone-2/real-data-test.md`). Synthetic: hit 97.2%, buses 95.5%, no-vehicle 97.0%, insults 100% (`scripts/run_eval.py`); stress test 100% of 5,000 |
| Same query run twice gives the same labels | ✅ | A re-run returns the cached labels (identical by design, `test_duplicates_sent_once_and_rerun_uses_cache`). Uncached repeats use temperature 0; the stress test scored 100% on 3 separate fresh runs |
| Abusive rows are labelled, or flagged as refused, never guessed | ✅ | Alex's real file: 0 refused / blocked / failed across 5 queries × 1,567 rows; synthetic: all 18 abusive rows labelled; refusal path covered by `test_always_refused_row_is_blank_with_note` |

## Failure handling
| Item | Status | Evidence |
|---|---|---|
| Missing API key shows a clear message and blocks Run | ✅ | `test_run_disabled_without_key`, `test_missing_key_raises_before_any_call` |
| Wrong API key shows a clear message, no crash | ✅ | `test_rejected_key_stops_run` (and the key isn't echoed) |
| Rate limit during a run retries and finishes | ✅ | `test_rate_limit_is_retried_then_labelled`; `test_rate_limit_forever_marks_row_failed` |
| A forced refusal (mocked) leaves the row blank with note `refused` | ✅ | `test_always_refused_row_is_blank_with_note` |
| Empty rows are skipped with note `empty` | ✅ | `test_empty_rows_are_not_sent`, `test_empty_and_trimmed_notes` |
| Closing the browser tab mid-run does not corrupt the cache | ✅ | `test_hard_kill_mid_run_leaves_cache_usable` (hard kill, then `integrity_check = ok`) |

## Performance and cost
| Item | Status | Evidence |
|---|---|---|
| 1,000 rows finish in under 2 minutes per query | ✅ | ~15 s per 1,000 rows (5,000 rows in 70 s) |
| Actual cost for 1,000 rows is a few cents per query | ✅ | ~$0.009 per 1,000 rows (`gpt-6-luna`) |

## Handover
| Item | Status | Evidence |
|---|---|---|
| Alex installs and runs the app from the README on his machine | ⏳ | `INSTALL-MAC.md`: step-by-step guide for a non-technical user (uv installs Python 3.12 and the pinned packages), with an "If something goes wrong" table. The same uv commands were tested on a clean copy (Windows): install, 67 tests pass, and the app starts. Needs Alex |
| Alex can change the model, batch size and test size in `config.py` | ✅ | Settings table in the README; every setting is commented in `config.py` |

## Alex's UI changes (2026-11-09, `feature/ui-rework`)
| Item | Status | Evidence |
|---|---|---|
| Long answers readable everywhere (wrap + click for full text) | ✅ | `ui/answer_table.py` in the sidebar, preview, test and results tables; browser check |
| Whole card collapses to its name | ✅ | `test_card_collapses_to_its_name`; browser check |
| Save / Load / Download small and fixed at the bottom | ✅ | Browser check at 1600 / 1100 / 760 px while scrolling |
| Upload, session info and Create Query fixed at the top; preview collapsed | ✅ | `test_upload_shows_preview_and_picks_text_column`; browser check |
| Single-line query box, hint as placeholder | ✅ | `test_query_box_is_one_line_with_hint_as_placeholder` |
| No big headers | ✅ | `test_no_big_headers` |
| Sidebar lists non-empty answers of the chosen column | ✅ | `test_sidebar_lists_answers_of_chosen_column` |
| App stops with a clear message on old Python | ✅ | `test_old_python_stops_with_message`, `tests/test_python_version_check.py` |
| Update to a new version without reinstalling | ✅ | README + INSTALL-MAC; ⏳ confirm on Alex's Mac (`ditto` is macOS-only) |
| Walkthrough video (≤ 5 min) | ✅ | Recorded and sent by Tariq (2026-11-09) |

## Model lifetime
Default model `gpt-6-luna` (current, not deprecated as of 2026-11-05). The previous default `gpt-4o-mini` shuts down 2027-01-14. To change model: `config.py` (`MODEL`, `REASONING_EFFORT`, the 3 prices), then `python scripts/run_eval.py --model <name>`.

## Milestone 2: four additional features (v1.1.0, 2026-11-13)
| Item | Status | Evidence |
|---|---|---|
| Claude as an option alongside OpenAI; OpenAI unchanged | ✅ | `tests/test_anthropic_client.py`, `test_openai_runs_are_unchanged` (same prompt and cache keys); live check with Alex's key: 20/20 |
| Claude confidence without logprobs | ✅ | Stated score + vote check (`tests/test_confidence_check.py`); live eval: wrong labels get the lowest scores (`docs/claude-confidence-method.md`) |
| Clicking a query highlights its rows in the sidebar (filter switchable) | ✅ | `test_sidebar_highlights_a_querys_rows_without_filter_by_default`, `test_sidebar_filter_buttons_when_enabled`; browser `check_part2` |
| Separate workspace per text column; save, load and download still work | ✅ | `tests/test_workspace_actions.py`, `test_switching_column_keeps_each_columns_queries`; browser download order across columns |
| Keyword queries: whole words, case ignored, OR, `*` word starts, punctuation, escaping | ✅ | `tests/test_keyword_matcher.py`; browser check = regex count |
| White answer cells in the sidebar; match count on cards, also collapsed | ✅ | `tests/test_answer_table.py`, `test_card_header_shows_match_count_also_collapsed`; pixel check (255,255,255) |

## Open items for Alex
1. Optional: 20 hand-labelled rows per query and an accuracy target X. We do not ask him for these unless needed.
2. Installed (2026-11-06); first run hit the conda issue, fix sent by message, waiting for his confirmation. He then deletes the "highlighter-dev" key.
3. Decide on v2 ideas: an "invert" option for "does not" queries, labelling several columns combined, a hosted version.
