# trace-validity-check

Python standard library only. Deterministic reporting audit for BT-0–BT-4 and
HB-0–HB-2, section 2 of
`files/paper-loop-duolingo2-eval2-gates-spec-2026-11-21.md`.

```sh
python3 -B trace_validity_check.py fixtures/compliant.json
python3 -B -m unittest discover -s . -p 'test_*.py' -v
```

The CLI prints JSON (`checker`, `result`, ordered `gates`, `passed`, `failed`,
`total`, `failed_gates`). Exit 0 means every gate passes; exit 1 means failed
gates or input errors. Input errors include `error` and fail all gates.
Missing evidence fails the affected gate. Conditional exemptions are PASS
only with explicit declarations. Booleans must be JSON booleans; numbers must
be finite and cannot be booleans. Duplicate keys and NaN/Infinity are rejected.

## Input contract

`fixtures/compliant.json` supplies a complete example. All fields below are
required unless the gate explicitly allows an exemption.

| Gate | Fields and rule |
| --- | --- |
| BT-0 | `predictor.source_type`: `behavioural_trace`, `self_report`, `mixed`; boolean `retention_or_effect_claim`. Self-report alone plus a retention/effect claim fails. |
| BT-1 | `validation.unit="user"`, `method="cv"` or `"holdout"`, `grouped_by_learner=true`. |
| BT-2 | `calibration.metric`: `ece`, `mce`, `brier_score`, `log_loss`, `calibration_slope`, `calibration_intercept`; numeric `value`. ECE must be in [0,1]. AUC/correlation alone cannot substitute for calibration. |
| BT-3 | `sensitivity.proximity_contamination` names the excluded proximity condition; `excluded_and_recomputed=true`; `metric` and numeric `value` record the recalculation. |
| BT-4 | `common_metric_comparison.performed=false` exempts. Otherwise true, shared `metric`, `left` and `right` each with distinct `tradition` names and ordered numeric `ci=[lower,upper]`; `ci_order` must match `left_below_right`, `right_below_left`, or `overlap`. Touching intervals overlap. |
| HB-0 | `mechanisms` declares booleans for `streak`, `freeze_or_emergency_reserve`, `social`, `push`, `reward`. False records absence and passes. |
| HB-1 | `outcome.claimed_type` and `measured_type` each `retention` or `autonomous_habit`. Claiming autonomous habit from retention measurements fails. |
| HB-2 | A retention claim exempts. Autonomous habit requires `no_reminder_measurement.reminders_absent=true`, a named `continuation_metric`, numeric `value`, and a nonblank `observation_period`. |

Text must be nonblank. CI ordering is checked, but non-overlap or behavioural
superiority is not required. No AUC/ECE quality cutoff, minimum study duration,
or success-rate threshold is imposed by the paper. The supported calibration
metric names are an input vocabulary, not an assertion that those metrics are
interchangeable. This tool checks declarations, not underlying datasets or the
truth of claimed measurements. Autonomous habit is interpreted per the spec;
HB-2 specifically requires measurement without reminders.

## Fixtures

- `compliant`: synthetic evidence demonstrating all gates; not production data.
- `anicca-current`: documentation-only snapshot of the spec and delegation.
  They supply no Anicca evidence for these gates, so unknown fields remain absent.
- `control`: self-report effect claim, random split, no exclusion/recalculation,
  retention represented as habit, and reminders still present.

`run-results-2026-11-21.json` contains actual fixture CLI reports, exit codes,
and unittest output. Tests cover invalid input, gate failures, conditional
exemptions, calibration alternatives, and CI boundary/order checks. No network,
API, third-party package, or model call is used.
