#!/usr/bin/env python3
"""production-eval-check: deterministic gate for the PRODUCTION EVAL
surface (CI evals vs online production monitoring, and the loop that
connects them). Stdlib only, offline, free.
Canonical source (read in full 2026-11-17, Hamel Husain & Shreya Shankar,
"AI Evals FAQ", Production & Deployment + sampling sections,
https://hamel.dev/blog/posts/evals-faq/):
- CI evals protect against known regressions before deployment; online
  monitoring finds failures in production traffic and estimates how
  often they occur. The two are different systems with different data.
- CI: test datasets are small (often 100+ examples) and purpose-built
  (core features, regression tests for past bugs, known edge cases);
  because CI runs frequently, cost per test matters - favour assertions
  / deterministic checks over LLM-as-judge evaluators.
- Online: sample live traces and run evaluators asynchronously; with no
  reference outputs on production data, rely more on reference-free
  evaluators (LLM-as-judge); track confidence intervals for production
  metrics - if the lower bound crosses your threshold, investigate.
- Connect the two: when production monitoring reveals new failure
  patterns (via error analysis), add representative examples to the CI
  dataset so the new issue can never regress silently.
- Sampling: mix methods (random / clustering / extremes / classifier /
  feedback); keep some random traces in every batch so failures your
  current signals do not describe can still surface.
- Frequency is a judgement over cost, saturation and business value:
  a saturated eval gives no new information (retire it, run it less,
  or first make it harder); cheap checks can run on every trace/change,
  expensive judges on a nightly sample.
- Guardrails != evaluators: guardrails are inline, fast, deterministic
  checks in the request path for clear-cut high-impact failures; they
  are versioned, every trigger is logged, rates are monitored, and a
  false positive is treated as a production bug. Evaluators run after
  the response (async/batch), measure nuanced quality, and do not block
  the original answer; a slow LLM judge is almost never a sync guardrail.
Exit 0=PASS, 1=FAIL.
"""
import json, sys
def check(d):
    f=[]
    dec=d.get("decision") or {}
    if not dec.get("decision_recorded"): f.append("PE-0 the CI-vs-production eval split is not recorded as a decided surface - evals are run ad hoc and nobody can say what protects production")
    if not dec.get("owner_recorded"): f.append("PE-0 no single owner is recorded for the production eval surface - when a production metric moves, nobody is responsible for investigating it")
    if not dec.get("canonical_source_recorded"): f.append("PE-0 the canonical source is not recorded (Hamel/Shankar: CI guards known regressions, online monitoring finds new failures, the two are connected) - every team invents its own deployment safety")
    ci=d.get("ci") or {}
    if not ci.get("curated_dataset_exists"): f.append("PE-1 no small purpose-built CI dataset is recorded (core features + regression tests for past bugs + known edge cases, often 100+ examples) - CI either tests nothing or tests an uncurated pile whose cost and signal are unknown")
    if not ci.get("deterministic_first"): f.append("PE-1 CI does not favour deterministic assertions over LLM-as-judge evaluators - frequent CI runs become slow, costly and flaky, so the gate gets skipped")
    if not ci.get("blocks_on_regression"): f.append("PE-1 the eval is not wired as a blocking CI / release gate - a regression can ship while the eval report sits unread (a report is not a gate)")
    on=d.get("online") or {}
    if not on.get("async_sampling_exists"): f.append("PE-2 production traces are not sampled and evaluated asynchronously - failures that only occur on real traffic are invisible until users report them")
    if not on.get("reference_free_evaluators"): f.append("PE-2 production evaluation does not use reference-free evaluators (e.g. LLM-as-judge) - production data has no reference outputs, so supervised-only checks cannot run there")
    if not on.get("confidence_intervals_tracked"): f.append("PE-2 production metrics are not tracked with confidence intervals and a recorded rule (lower bound crossing the threshold triggers investigation) - small samples get read as real movements, and real movements get read as noise")
    lp=d.get("loop") or {}
    if not lp.get("prod_failures_feed_ci"): f.append("PE-3 new failure patterns found in production are not added as representative examples to the CI dataset - the same failure can regress again after it is fixed once")
    if not lp.get("sampling_includes_random"): f.append("PE-3 the production sampling mix keeps no random traces in every batch - targeted-only sampling only finds failures the current signals already describe")
    if not lp.get("frequency_by_cost_saturation_value"): f.append("PE-3 run frequency is not decided by cost, saturation and business value - expensive saturated evals burn budget while cheap high-value checks run too rarely")
    gr=d.get("guardrails") or {}
    if not gr.get("inline_fast_deterministic"): f.append("PE-4 there are no inline, fast, deterministic guardrails for clear-cut high-impact failures (PII, malformed output, disallowed content) - objective failures reach users because only after-the-fact evaluators exist")
    if not gr.get("versioned_logged_monitored"): f.append("PE-4 guardrail rules are not versioned with every trigger logged and rates monitored (false positives treated as production bugs) - an over-firing guardrail silently degrades the product")
    if not gr.get("evaluators_async_nonblocking"): f.append("PE-4 evaluators are not kept asynchronous / non-blocking (or the separation is unrecorded) - a slow judge in the request path, or evaluators that block answers, trade user latency for measurement")
    ops=d.get("operations") or {}
    if not ops.get("tiered_cost_execution"): f.append("PE-5 execution is not tiered by cost (cheap checks on every trace, expensive judges on a sampled / nightly batch) - the team either pays judge prices on all traffic or samples so little that production is unmeasured")
    if not ops.get("alert_thresholds_recorded"): f.append("PE-5 no alert / investigation thresholds are recorded for production eval metrics - a dropping pass rate is discovered from user complaints instead of from the monitoring itself")
    if not ops.get("saturation_retire_or_harden"): f.append("PE-5 saturated evals (passing everything, giving no new information) are not retired, run less often, or made harder - the suite reports green while measuring nothing")
    return f
if __name__=="__main__":
    data=json.load(open(sys.argv[1])); fails=check(data)
    if fails:
        print(f"FAIL ({len(fails)}):")
        [print(" -",x) for x in fails]; sys.exit(1)
    print("PASS")
