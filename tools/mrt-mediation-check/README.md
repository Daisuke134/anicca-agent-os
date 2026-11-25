# mrt-mediation-check

Standard-library-only, deterministic reporting checker for MM-0–MM-5 in
`files/paper-loop-synthetic2-mrt2-gates-spec-2026-11-20.md`.

```sh
python3 mrt_mediation_check.py fixtures/compliant.json
python3 -B -m unittest discover -s . -p 'test_*.py'
```

The CLI prints JSON with `result`, six ordered `gates`, `passed`, `failed`,
`total`, and `failed_gates`. Exit 0 means all gates pass; all other outcomes
exit 1, including invalid input (with an `error` and all six gates FAIL).
Missing/null fields, wrong types, duplicate JSON keys and nonfinite JSON
constants never silently exempt a gate. Conditional exemptions are printed as
PASS, and require the explicit declarations below.

## Input contract

`fixtures/compliant.json` is the full adaptive factorial mediation example.

| Gate | Required evidence |
| --- | --- |
| MM-0 | `design.treatment_type`: `binary`, `categorical`, or `factorial`; `design.outcomes.proximal_types`: nonempty text list; boolean `design.outcomes.distal_present`. |
| MM-1 | Booleans `distal_claim` and `mediation_claim`. Distal claims require `distal_present=true` and nonempty `distal_effects` using `direct`, `indirect`, `total`. With `mediation_claim=false`, distal effects must be exactly `["total"]` and `estimator.numeric_mediation_claim=false`. With mediation true, require `mediator.definition`, `measurement_time`, `nearest_after_treatment=true`, named `estimands.direct/indirect/total`, and nonempty `identification_assumptions`. |
| MM-2 | `estimator.robustness`: `multiply_robust`, `doubly_robust`, `none`; booleans `cross_fitting` and `numeric_mediation_claim`. Numerical mediation requires a mediation declaration and robustness other than `none`. |
| MM-3 | Factorial: `factorial.factors` maps at least two names to at least two unique string levels each. `arms` enumerates the entire Cartesian product exactly once, each arm mapping factor names to levels. Nonempty `interaction_contrasts`, `preregistered=true`, and `selection_basis` text list containing the exact item `interaction`. Binary/categorical: explicitly set `factorial.not_applicable=true`. |
| MM-4 | `randomization.fixed` boolean. If false, require nonblank `algorithm_version`, `clipping.lower/upper` within [0,1] with lower < upper, `actual_probability_logged=true`, `fixed_probability_assumed=false`. |
| MM-5 | `proximal_outcomes.engagement` and `target_behavior`: separate nonempty text lists of recorded outcomes; `cross_outcome_inference=false`; `feasibility_as_efficacy=false`. |

Interpretation choices: an explicit non-mediation declaration permits total-only
distal reporting as stated by MM-1. If mediation is claimed, its declarations
are checked even without a distal claim. Adaptive designs require recorded
probabilities and must not declare a fixed-probability analysis assumption.
The checker validates the logging declaration, not the logs themselves. Factor
levels make "all arms" mechanically verifiable. No effect-size/significance
threshold or optimal clipping range is invented. The range [0,1] is the
mathematical domain of probabilities, not an efficacy threshold.

## Exactly three fixtures

- `compliant.json`: illustrative adaptive factorial design with mediation, six PASS;
  references and settings are examples, not Anicca measurements.
- `anicca-current.json`: evidence-limited snapshot sourced to specification sections
  4, 6 and 7; all six FAIL. Unknown fields stay absent. This is a documentation
  audit, not a fresh production measurement.
- `control.json`: main-effects-only arm selection, adaptive probabilities missing
  from logs while assuming fixed probabilities, and outcome/feasibility conflation;
  MM-3/MM-4/MM-5 FAIL.

Tests exercise missing evidence, malformed types, conditional exemptions, arm
coverage, robustness and adaptive logging. They create no extra stored fixtures.
No installation, network access, or API is used.
