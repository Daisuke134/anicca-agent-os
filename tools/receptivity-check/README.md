# receptivity-check

Implements section 3 of the 2026-11-18 paper-loop JITAI2/onboarding2 spec.
Python standard library only. Run:

```sh
python3 ~/workspace/tools/receptivity-check/receptivity_check.py ~/workspace/tools/receptivity-check/fixtures/compliant.json
```

Exit 0 = all gates PASS; 1 = one or more gates FAIL; 2 = invalid JSON/input or usage.
Output includes each gate, passed/failed/total counts and failed gate IDs.
Missing, null, empty or wrongly typed required fields fail. Conditional gates require explicit boolean declarations; absence never implies false. Unknown metadata fields are ignored. Duplicate JSON keys and nonfinite JSON constants are rejected.

The compliant fixture documents the input schema. Rates and confidence are fractions in [0,1]; counts are nonnegative integers; periods and methods are nonempty descriptions. Evidence records are declarations, not independently verified scientific findings. These checkers validate records, not runtime behavior or efficacy. Fixture evidence is synthetic except for the explicitly document-backed Anicca snapshot. That snapshot leaves unknown fields missing rather than manufacturing passing exemptions.

Gate set replaced: legacy RP-0..RP-7 (2026-11-14) is superseded here by TR-0..TR-5 and CG-0..CG-1. The three fixtures also use the replacement schema.
