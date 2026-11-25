# eval-claim-check

Run `python3 eval_claim_check.py fixtures/conforming.json`.
Python standard library only; offline. Exit 0 means six gates pass, 1 means a
gate fails, 2 means invalid JSON/input file/usage. `check(document)` returns one
failure per gate; CLI prints each gate and a RESULT summary. Missing fields fail
closed; string booleans and nonfinite numbers cannot satisfy numeric fields.

Schema (full example: `fixtures/conforming.json`):

- EC-0: nonempty `scores`, each with unique string `id`, finite `value`, nonempty
  `formality_tier` and `scope`, ISO dates `valid_from` <= `expires_on`.
  No numeric tier threshold is imposed by the source spec.
- EC-1: `aggregation.multiple_signals` explicitly declares applicability.
  For multiple signals, `signals` maps model names to equal-length lists of at
  least two finite values, on a comparable higher-is-better scale declared via
  `higher_is_better_normalized: true`. `mean_ranks` and `weakest_link_ranks` must
  match recomputed competition ranks (1,1,3 for ties). When rankings differ,
  `rank_disagreement_disclosed` must be true. Normalization itself is not audited.
- EC-2: `as_of` is an explicit ISO date, never the machine clock. Each score has
  `reevaluated_on` <= `valid_from`, not in the future, and boolean
  `used_for_current_claim`. Current use requires as_of inside the inclusive
  validity window. Expired historical records may be retained without current
  use. Changing reevaluated_on alone cannot renew an expired window.
- RA-0: `audit.statistical_result` is positive/negative/inconclusive;
  `.regime.iid_assumption` is met/violated/unknown, `.benchmark_size` is a positive
  integer, `.power_at_benchmark_size` and `.reference_set_source` are descriptions.
- RA-1: `audit.provenance` explicitly records provenance (including honest unknown
  status), `.statistical_detection_separate_from_provenance` is true and
  `.negative_detection_substitutes_for_provenance` is false.
- RA-2: `audit.distribution_shift` is boolean, with a nonempty
  `.suspect_validation_distribution_comparison`. Shift requires
  `.false_positive_risk_disclosed: true`.

Conforming/control are synthetic documents. The Anicca-assumed fixture represents
missing evidence, not verified production behavior. This audits document structure
and internal consistency; it does not verify asserted provenance, detector power,
or methodological validity. Canonical spec:
`files/paper-loop-duolingo3-eval3-gates-spec-2026-11-24.md`.
