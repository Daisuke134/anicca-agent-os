# repetition-schedule-check

Offline Python standard-library checker. Run:

```sh
python3 repetition_schedule_check.py fixtures/good.json
python3 -m unittest discover -s . -p 'test_*.py'
```

Exit 0 means every gate passed; exit 1 means a gate or input failed. Each gate
prints its own PASS/FAIL. `check(document)` retains the failure-list API.

HL-0..HL-4 retain the existing ownership, decision features, recall threshold,
item/learner separation, and top-factor checks. SR3-0..SR3-2 implement
`files/paper-loop-duolingo3-eval3-gates-spec-2026-11-24.md`:

| Gate | Required comparison fields |
| --- | --- |
| SR3-0 | `evidence_type`: `real_learners`, `simulated_learners`, or `operational_logs`; `reported_population` must match it. |
| SR3-1 | Nonempty `protocol`; at least three distinct `baselines`, each with `name`, boolean `classical`, and matching `protocol`; at least one classical baseline. |
| SR3-2 | Boolean `claims_confusion_robustness` and `llm_every_decision`. Robustness claims require separate `semantic_confusion.confusable` and `.non_confusable` results, each with positive integer `sample_size` and numeric `success_rate` in [0,1]. LLM use every decision requires `inference_cost.amount_per_decision` (nonnegative finite number), `currency`, and `measurement_basis`. |

`comparison` is a top-level object; `fixtures/good.json` demonstrates the complete
schema. Evidence fields validate the document's records, not the underlying
experiment or whether a method is actually classical. No empirical performance
threshold is inferred from the paper.

Fixtures: `good.json` is a synthetic conforming example; `bad.json` is a control
with four intentional failing gates; `anicca.json` is an explicitly assumed
calendar-only scenario, not a production audit. Its missing comparison evidence
fails closed. All fixture rates and costs are invented test data.
