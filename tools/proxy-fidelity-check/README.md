# proxy-fidelity-check

Python standard library only. Canonical specification:
`files/paper-loop-usersim3-behaviorsim3-gates-spec-2026-11-23.md`, UP-0..3,
DG-0..3, FA-0..2. Checks evidence records; it does not measure simulator fidelity.

Run `python3 proxy_fidelity_check.py fixtures/conforming.json`.
Exit 0: all gates pass; 1: evidence/claim gate failure; 2: unreadable or invalid
JSON, non-object root, nonfinite JSON numbers, or incorrect CLI arguments.
Each gate prints PASS/FAIL, followed by aggregate counts.

`fixtures/conforming.json` is the complete input template. Numeric fields must
be finite JSON numbers (booleans and numeric strings are rejected). Rates use
0..1. A missing or malformed evidence section fails its gates without crashing.
All text evidence fields require nonblank strings. Boolean declarations must
be actual JSON booleans.

| Gates | Required fields |
|---|---|
| UP-0..2 | `proxy`: fidelity metric/score independent of agent success, premature disclosure rate, successful-episode violation rate, signed interaction change and unit, explicit rejection of preserved-reward harmlessness |
| UP-3 | `simulators.results`: at least two uniquely named simulators with score and nonnegative cost; `score_range` must equal max-minus-min; cost/fidelity selection reason |
| DG-0..1 | `distribution`: nonnegative backward KL, forward KL, JS; six named facets each with nonnegative capture/miss/hallucinate measurements |
| DG-2 | `simulators.ensemble_used`; when true, comparison rows and complementarity evidence |
| DG-3 | `grounding`: source type (`real-data-profile`, `handwritten-directive`, `ungrounded`), description, ceiling and amplification checks, anti-leakage control |
| FA-0..2 | Signed easy/medium/hard calibration errors and metric; JP/EN subgroup quality and metric; conversation artifact inspection |

Compared simulators need not be deployed as an ensemble. DG-2 passes an explicit
false declaration without complementarity evidence. Fixtures are illustrative;
`anicca-assumed` means no gate evidence was supplied, not a production finding.
