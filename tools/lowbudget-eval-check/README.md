# lowbudget-eval-check

Python standard library only. Deterministic reporting audit for LB-0–LB-5 and
CT-0–CT-4, section 2 of
`files/paper-loop-duolingo2-eval2-gates-spec-2026-11-21.md`.

```sh
python3 -B lowbudget_eval_check.py fixtures/compliant.json
python3 -B -m unittest discover -s . -p 'test_*.py' -v
```

JSON output includes `checker`, `result`, ordered `gates`, `passed`, `failed`,
`total`, `failed_gates`. Exit 0 means all gates PASS; exit 1 means failed gates
or invalid input. Input errors include `error` and fail all gates. Missing
fields fail affected gates; explicit conditional exemptions are PASS. Numbers
must be finite, booleans must be booleans, text must be nonblank. Duplicate
JSON keys and NaN/Infinity are rejected.

## Input contract

See `fixtures/compliant.json` for the complete schema.

| Gate | Fields and rule |
| --- | --- |
| LB-0 | Positive integer `k`, `m`; boolean `extrapolation` must equal `k>m`. |
| LB-1 | For `k>m`, `estimator.type`, `prior_family`, `component_selection` must be named; `naive_y_over_m_transform_only=false`. Types `naive`, `y/m`, `direct`, `combinatorial` do not qualify for extrapolation. Hierarchical/Beta-mixture or another documented estimator can qualify. For `k<=m`, exempt. |
| LB-2 | `interval.type`: `delta_method_ci`, `credible_interval`, or `confidence_interval`; ordered numeric `bounds=[lower,upper]`, numeric `full_data_reference`, boolean `contains_reference` matching inclusive containment. |
| LB-3 | `improvability.used=false` exempts; otherwise true, `fitted_prior_dependence_disclosed=true` and nonblank `dependence_description`. |
| LB-4 | For `k<=m`, `estimator.direct_or_combinatorial_prioritized=true` and `unconditional_mixture_superiority_claim=false`. For `k>m`, exempt. |
| LB-5 | `metrics_fit.reports_pass_power_and_auc=false` exempts; otherwise true, `same_fit=true` and identical nonblank `pass_power_fit_id`/`auc_fit_id`. |
| CT-0 | `contamination.claim_types`: nonempty unique list of `absolute_inflation`, `ranking_reorder`; `claims_separated=true`. Both claims are permitted when explicitly separated. |
| CT-1 | Boolean `contamination.discusses_ranking`. True requires numeric `paraphrase_rank_correlation` in [-1,1]. A `ranking_reorder` claim also requires `discusses_ranking=true`. |
| CT-2 | `contamination.decomposition.uniform` and `differential`: numeric decomposition results. A ranking-reorder claim additionally requires `differential_evidence=true` and nonblank `evidence_description`. |
| CT-3 | `contamination.calibration.known_dose`, `known_dose_result`, `negative_control_result`: numeric calibration records. |
| CT-4 | Numeric `contamination.paraphrase_gap`; `clean_baseline` with a named `reference`, numeric `gap`, and `used_as_reference=true`. |

Interpretations: the gate requires recording whether the interval contains the
full-data reference, not that containment must be true. The single-component
hierarchical case can name `fixed single component` as component selection;
BIC is an example, not mandatory. LB-4 records prioritization, without banning
an explicitly justified alternative estimator. LB-5 rejects mixed fit IDs.
Both known-dose and negative-control calibration results are recorded for CT-3.
No correlation cutoff, minimum contamination effect, prior-family preference,
or significance threshold is invented. CT-2 evidence and CT-4 baseline usage
are declarations, not statistical recomputations. This audits supplied state;
it does not fit models or independently verify the evidence.

## Fixtures

- `compliant`: synthetic extrapolation and separated contamination claims;
  numbers illustrate the schema and are not Anicca results.
- `anicca-current`: documentation-only snapshot sourced to the spec/delegation;
  unknown Anicca measurement fields are intentionally absent.
- `control`: naive extrapolation, undisclosed prior dependence, mixed fit IDs,
  conflated claims, and missing ranking, differential, calibration and baseline
  evidence.

Actual CLI reports and unittest output are in `run-results-2026-11-21.json`.
Tests cover each gate, missing evidence, malformed inputs, k=m and k<m,
interval boundaries, conditional exemptions, and ranking claim consistency.
No network, paid API, third-party package, or model call is used.
