# provenance-stability-check

Standard-library-only, deterministic reporting checker for PS-0–PS-5 in
`files/paper-loop-synthetic2-mrt2-gates-spec-2026-11-20.md`.

```sh
python3 provenance_stability_check.py fixtures/compliant.json
python3 -B -m unittest discover -s . -p 'test_*.py'
```

The CLI prints JSON with `result`, six ordered `gates`, `passed`, `failed`,
`total`, and `failed_gates`. Exit 0 means all six pass; any failed gate or
invalid input exits 1. Invalid input includes unreadable files, malformed JSON,
duplicate keys, non-object roots, and NaN/Infinity. Missing required fields fail;
only explicit boolean declarations enable conditional exemptions.

## Input contract

Use `fixtures/compliant.json` as a complete example. Unrecognized metadata is
ignored; it cannot substitute for the fields below.

| Gate | Required evidence |
| --- | --- |
| PS-0 | Nonempty `claims`, each with `type` (`stance`, `attribute`, `ranking`) and nonblank `population`. |
| PS-1 | `stability_audit.neutral_present=true`; `revisions` contains exactly one aggregate for each `type`: `neutral_paraphrase`, `substantive_addition`, `multimodal`. Each has finite `directional_shift` and `transition_rate` in [0,1]. |
| PS-2 | `mechanism.name` and a nonempty `mechanism.settings` object with non-null settings. |
| PS-3 | Each attribute declares boolean `enriched`. Enriched attributes require nonblank `source`, `audit` (`supported`, `partially_supported`, `unsupported`, `unflagged`), boolean `fabrication` and `stereotyping`. `unflagged` fails. `diversity_as_validity=false` is mandatory. |
| PS-4 | `provenance_claimed_as_realism=false`; boolean `realism_claim`. If true, a separate nonblank `human_calibration_reference`. |
| PS-5 | `predictive_claim=false`, or true with `human_studies`: positive integer `study_count` and `participant_count`, nonempty `correlations` (unique `metric`, finite `value` in [-1,1]), `minimum_correlation` equal to the smallest listed value, and boolean `fitted_not_forecast`. |

This checks reporting structure, not scientific truth or source accessibility.
`unsupported` and positive fabrication/stereotyping flags are allowed when
explicitly reported: the spec requires auditable classification, not universal
support. Both values of `fitted_not_forecast` pass when disclosed. No minimum
correlation, maximum stance shift, or effectiveness threshold is invented.
Bounds on rates/correlations are mathematical domains, not efficacy thresholds.
The minimum must describe the listed correlations; an average alone is insufficient.

## Exactly three fixtures

- `compliant.json`: illustrative complete design, all six gates PASS. All numbers
  and references are synthetic examples, not observed Anicca results.
- `anicca-current.json`: documented-state snapshot based on specification sections
  4, 6 and 7; absent evidence is left absent, all six FAIL. This is not a live audit
  or a claim that every undocumented capability is absent in production.
- `control.json`: otherwise complete design that leaves an enriched claim
  unflagged and conflates diversity/provenance with validity/realism; PS-3/PS-4 FAIL.

Tests also mutate inputs in memory and temporary files; these are not additional
fixtures. No installation, network access, or API is used.
