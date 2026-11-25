# streak-representation-check

Run `python3 streak_representation_check.py fixtures/conforming.json`.
Python standard library only; offline. Exit 0 means all five gates pass, 1 means
at least one gate fails, 2 means unreadable/invalid JSON or CLI usage.
`check(document)` returns one failure message per failed gate. CLI prints every
gate and a `RESULT` summary. Missing fields fail closed; booleans must be JSON booleans.

Schema (complete example: `fixtures/conforming.json`):

- ST-0: `actual_behavior.measure` and `.observation_window` are nonempty strings;
  `representation.conditions` contains intact/broken/no-log, and
  `.separate_from_actual_behavior` is true.
- ST-1: `continuation_rates` has finite fractions in [0,1] for each condition;
  `comparison_protocol` describes the common comparison. `display_harm_recorded`
  must be true when broken <= no-log, including equality;
  `benefit_claim_based_only_on_intact_gap` must be false.
- ST-2: `attribution.groups` is a nonempty list of self/external/system;
  `.self_external_pooled` is false and `.analysis_by_attribution` describes the
  separate analysis. Only observed attribution groups need be included.
- ST-3: `repair.available` is boolean; `.may_remain_below_intact` is true and
  `.equivalent_to_intact_claim` is false, including when repair is unavailable.
- ST-4: `consideration.offered` is boolean. If true, `.types` lists the forms of
  consideration and `.included_in_mechanism_inventory` is true.

Fixtures: conforming is synthetic, control breaks ST-1/2/3, Anicca-assumed has
no verified evidence and fails all gates. None is a measurement of Anicca users.
These are document completeness/consistency gates, not causal proof or a paper
replication. Spec: `files/paper-loop-duolingo3-eval3-gates-spec-2026-11-24.md`.
