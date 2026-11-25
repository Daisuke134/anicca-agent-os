# mrt-moderator-check

Python standard library only; offline deterministic document checks for MV-0..MV-5 in `files/paper-loop-synthetic3-mrt3-gates-spec-2026-11-23.md`.

Run `python3 mrt_moderator_check.py fixtures/conforming.json` from this directory. Prints one PASS/FAIL per gate and a RESULT with counts. Exit 0 means all gates pass, 1 means evidence is missing or a gate fails, 2 means bad CLI, unreadable input, invalid JSON, or a non-object root. Wrongly typed nested fields fail the relevant gate. Numeric measurements must be finite JSON numbers, not booleans.

The conforming fixture is the schema example. All fixture measurements and references are illustrative. The Anicca-assumed fixture marks unavailable evidence rather than claiming a measured production failure. This checks the supplied document; it cannot authenticate the study or establish causal validity itself.

| Gate | Object and required fields |
| --- | --- |
| MV-0 | `declaration`: nonempty unique moderators, stratification_factors, and strata string lists. before_analysis=true, or false with claim_kind=`exploratory`. `strata` enumerates every device × phase combination intended by the analysis. |
| MV-1 | `consistency`: stratum_effects must cover exactly the declared strata; values positive/negative/null. A single common non-null sign supports conclusion=`consistent`; all other combinations require conclusion=`inconsistent` and general_moderator_claim=false. |
| MV-2 | `surface_personalization`: factor, tested_independently=true, result positive/negative/null, matching reported_result, personalization_alone_is_evidence=false. |
| MV-3 | `policy_value`: claimed=false explicitly, or claimed=true with policy_assignment_randomized=true, control=`random-allocation`, comparison_reference, forecasting_only=false. |
| MV-4 | `outcomes`: unique declared_proximal list, results object covering exactly that list; each outcome has finite effect and positive/negative/null result; generalized_to_other_outcomes=false. |
| MV-5 | `power`: boolean adequate and controlled, nonempty assessment, claim_kind=`efficacy` or `feasibility`. Inadequate power or no control forbids efficacy. |

Null and heterogeneous moderator effects are acceptable when honestly reported. A forecasting-only model cannot support a policy-value claim. Stratum labels and comparison references are supplied evidence; the checker does not reconstruct trial data or compute statistical significance.

Run `python3 -m unittest discover -s . -p 'test_*.py'` for boundary and fixture checks.
