# decision-fidelity-check

Deterministic DF-0..DF-7 reporting checker for section 2 of
`files/paper-loop-decision-fidelity-gates-spec-2026-11-19.md`. Python standard
library only; no network, API, installation or credentials.

```sh
python3 tools/decision-fidelity-check/decision_fidelity_check.py tools/decision-fidelity-check/fixtures/compliant.json
python3 -B -m unittest discover -s tools/decision-fidelity-check -p 'test_*.py'
```

The standalone copy also runs from `~/workspace/tools/decision-fidelity-check/`.
Exit 0 = all gates PASS; 1 = gate failure; 2 = invalid JSON/input or usage,
following the previous checkers. JSON output includes per-gate PASS/FAIL,
passed/failed/total counts and failed gate IDs. Unknown metadata is ignored.
Duplicate keys and NaN/Infinity constants are rejected. Required values reject
missing/null/empty/wrong types; numbers exclude booleans and nonfinite values.

`fixtures/compliant.json` is the complete input schema and contains synthetic
illustrative evidence, not Anicca measurements. Rates are fractions [0,1].
Metrics contain a nonempty `metric` and finite `value`. Contrasts contain an
`effect_size_metric`, finite `effect_size`, and either `test` (method and p_value
in [0,1]) or `interval` (ordered lower/upper and confidence strictly in (0,1)).
Outcome reports require at least two distinct outcome groups, each with a metric.

| Gate | Required record |
|---|---|
| DF-0 | Allowed ground_truth_type and boolean decision_claimed; assigned-goal roleplay cannot support a decision claim. |
| DF-1 | outcome_conditioned groups and contrast, regardless of marginal values. |
| DF-2 | Separate real/simulation resistance, deliberation, disengagement rates; repair_claimed=true requires a complete post_repair_outcome_conditioned report. |
| DF-3 | Boolean teacher_forced and same_perceiver; if both false, uncontrolled=true. Missing settings fail rather than imply false. |
| DF-4 | persona_has_unknown_targets=true requires real/fabricated pairs, twin_construction, paired_contrast and distinct domain contrasts. Without a numeric human_low_knowledge_baseline, conditional_on_twin_adequacy=true is required. |
| DF-5 | claimed=true requires separate_from_task_success=true, lexical and judge metrics, human_human/proxy_proxy controls and judge_sensitivity. Sensitivity is performed=true with two distinct judges and result, or performed=false with a note. |
| DF-6 | Separate R1/R2 metrics, cross_level_improvement_inferred=false, profile_informativeness_evidence, positive integer coverage.n and separate variance_stability/bias_assessment descriptions. |
| DF-7 | claimed=true requires type=direct_fidelity or transferable_structure, reference_questions, explicit complementary cold_start/target_has_human_data booleans, and level=individual or distribution. |

Conditional declarations (`knowledge_leakage.persona_has_unknown_targets`,
`human_likeness.claimed`, `calibration.claimed`, `behavior.repair_claimed`) must
be explicit booleans. False makes only that conditional requirement inapplicable
(reported PASS); missing declarations fail. A true trigger never exempts absent
evidence. Producers must accurately set these flags; the checker does not infer
claims from prose or independently verify evidence.

The spec prescribes reporting completeness, not universal effect-size acceptance
thresholds. A fully reported poor contrast may pass this reporting gate; PASS
is not proof of fidelity, human-likeness, efficacy or improved revenue. The Chen
control records good marginal bias and a persistent bad contrast in design
metadata while deliberately omitting a complete outcome-conditioned report and
post-repair remeasurement. It fails exactly DF-1 and DF-2. The documented Anicca
fixture leaves unverified facts absent, based on the two cited local specs, and
fails rather than inventing measurements or conditional exemptions.
