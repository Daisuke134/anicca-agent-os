# onboarding-adaptation-check

Implements section 3 of the 2026-11-18 paper-loop JITAI2/onboarding2 spec.
Python standard library only. Run:

```sh
python3 ~/workspace/tools/onboarding-adaptation-check/onboarding_adaptation_check.py ~/workspace/tools/onboarding-adaptation-check/fixtures/compliant.json
```

Exit 0 = all gates PASS; 1 = one or more gates FAIL; 2 = invalid JSON/input or usage.
Output includes each gate, passed/failed/total counts and failed gate IDs.
Missing, null, empty or wrongly typed required fields fail. Conditional gates require explicit boolean declarations; absence never implies false. Unknown metadata fields are ignored. Duplicate JSON keys and nonfinite JSON constants are rejected.

The compliant fixture documents the input schema. Rates and confidence are fractions in [0,1]; counts are nonnegative integers; periods and methods are nonempty descriptions. Evidence records are declarations, not independently verified scientific findings. These checkers validate records, not runtime behavior or efficacy. Fixture evidence is synthetic except for the explicitly document-backed Anicca snapshot. That snapshot leaves unknown fields missing rather than manufacturing passing exemptions.

Gates OG-0..OG-5. Routing uses low/middle/high tier definitions and allowed goal-source lists. Both low=self-only and high=algorithm-only fail OG-2 independently. User sources must agree with their tier assignment. Explicit default-unchanged is an allowed source. No algorithm or no adaptation requires used=false; no evaluated effects requires effects_present=false and effects=[].
