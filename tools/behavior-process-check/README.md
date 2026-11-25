# behavior-process-check

Python standard library only. Canonical specification:
`files/paper-loop-usersim3-behaviorsim3-gates-spec-2026-11-23.md`, BS-0..3.
Checks evidence records; it does not itself measure human behavior.

Run `python3 behavior_process_check.py fixtures/conforming.json`.
Exit 0: all gates pass; 1: evidence/claim gate failure; 2: unreadable or invalid
JSON, non-object root, nonfinite JSON numbers, or incorrect CLI arguments.
Each gate prints PASS/FAIL, followed by aggregate counts.

`fixtures/conforming.json` is the complete input template. Numeric fields must
be finite JSON numbers, never booleans or numeric strings. Evidence strings must
be nonblank and declarations must be actual booleans. Malformed evidence
sections fail their gates without crashing.

| Gate | Required fields |
|---|---|
| BS-0 | `tasks`: separate `measurement`, `individual_prediction`, `population_simulation` objects, each with metric name and numeric value |
| BS-1 | `population`: nonnegative effect-size MAE, desirability inflation inspection and individual-variation compression inspection |
| BS-2 | `process`: separate reasoning-to-conclusion and conclusion-to-action fidelity in [0,1]; `extraction_method: "explicit-tag"`, nonblank tag, `tag_machine_checked: true`, `free_text_extraction_mismatch_as_model_trait: false` |
| BS-3 | `rule_misapplication`: directional bias probe and result, `assumes_single_upstream_cause: false` |

Fixtures are illustrative. `anicca-assumed` means no gate evidence was supplied,
not a production finding. Negative signed metrics are allowed where meaningful;
MAE is nonnegative and fidelity is a rate.
