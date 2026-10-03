# Failure records

Keep real model failures with their submitted artifacts, raw transcripts and
run metadata. None have been measured in this release. The records below are
deliberately injected **tooling regression controls**, exercised by
[test_project.py](../tests/test_project.py); they are not agent evaluation results.

| Control | Observed rejection | Evidence | Resolution |
| --- | --- | --- | --- |
| `polish-scope`: change 84.0 to 94.0 | Protected value check fails | `test_protected_value_negative_control_fails` | Restore the actual source value; rerun scoring. |
| Change a prepared input or skill context | Scoring refuses mismatched fingerprints | `test_changed_prepared_input_and_context_are_rejected` | Prepare a new run; do not relabel old artifacts. |
| Reuse a session ID in both conditions | Pair comparison is refused | `test_comparison_requires_attribution_and_distinct_sessions` | Run genuinely independent sessions with actual identifiers. |
| Change settings or compare maintainer candidates | Comparison is refused | `test_comparison_rejects_changed_settings_and_maintainer_scores` | Match recorded conditions and use actual model artifacts. |
| Cite a review excerpt absent from its artifact line | Human evidence validation fails | `test_human_review_requires_real_line_excerpt` | Cite the real location and review the full output. |
| Treat missing TeX as complete verification | Default runner refuses; explicit portable mode records partial | `test_example_missing_engine_and_portable_evidence` | Install/use an existing engine and retain real logs. |

For each real future failure, record case/trial, condition, model/settings,
artifact and transcript location, failing criterion, source discrepancy,
suspected cause, proposed fix, rerun evidence and remaining uncertainty. Preserve
unsuccessful trials as well as successes. See the [protocol](../docs/evaluation.md).
