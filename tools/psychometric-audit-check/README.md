# psychometric-audit-check

Python standard library only; offline deterministic document checks for PA-0..PA-5 in `files/paper-loop-synthetic3-mrt3-gates-spec-2026-11-23.md`.

Run `python3 psychometric_audit_check.py fixtures/conforming.json` from this directory. Prints one PASS/FAIL per gate and a RESULT with counts. Exit 0 means all gates pass, 1 means evidence is missing or a gate fails, 2 means bad CLI, unreadable input, invalid JSON, or a non-object root. Wrongly typed nested fields fail the relevant gate. Numeric measurements must be finite JSON numbers, not booleans.

The conforming fixture is the schema example. All values and references in fixtures are illustrative, not Anicca measurements. The Anicca-assumed fixture deliberately omits unavailable evidence. This checker validates supplied evidence descriptions, not their external authenticity or the scientific validity of a model.

| Gate | Object and required fields |
| --- | --- |
| PA-0 | `baseline`: name, non_llm=true, strongest_comparator=true, synthetic_score, baseline_score, higher_is_better boolean. A worse synthetic score requires conclusion=`below-baseline` and used_as_evidence=false. |
| PA-1 | `human_anchor`: kind=`same-people` or `other-people`, numeric score, nonempty reference. |
| PA-2 | `joint_structure`: nonempty item_correlations, latent_structure, reliability descriptions; nonnegative within_person_sd_ratio; marginals_only_validity_claim=false. |
| PA-3 | `negative_controls`: human_null_established=true, reference, positive integer paths_tested, integer synthetic_significant_paths in [0, paths_tested]. |
| PA-4 | `held_out`: training_data=`synthetic`, test_data=`held-out-human`, metric, finite value (negative R² is accepted), split_reference. |
| PA-5 | `segment_gap`: nonnegative synthetic_to_real_ratio, boolean decision_reversal, nonempty comparison description. |

No literature score is a hard-coded acceptance threshold. A documented below-baseline result passes when it is honestly withheld as evidence. Negative controls finding false signals and decision reversals are likewise acceptable to report. The audit requires all six records even when the document does not make a mediation claim; absence is reported as missing audit evidence.

Run `python3 -m unittest discover -s . -p 'test_*.py'` for boundary and fixture checks.
