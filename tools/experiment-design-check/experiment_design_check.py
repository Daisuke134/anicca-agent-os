#!/usr/bin/env python3
"""experiment-design-check: deterministic gate for the EXPERIMENT DESIGN
surface (online controlled experiments / A-B tests for product and paywall
changes). Stdlib only, offline, free.
Canonical sources (read 2026-11-17):
- GrowthBook, "How to design an A/B test" (full read)
  https://www.growthbook.io/insights/how-to-design-an-ab-test
  Design backward from a decision; causal hypothesis naming population,
  change, outcome and mechanism; one primary metric defined with numerator,
  denominator, window; guardrails with thresholds; MDE/sample/allocation/
  duration planned before launch; exposure distinct from assignment;
  integrity checks planned, SRM first; decision rule for positive /
  negative / inconclusive / mixed written before results; A/A + QA before
  launch; check SRM and instrumentation before reading effects; report
  effect with interval and practical significance; record the learning.
- Kohavi et al., Trustworthy Online Controlled Experiments (via GrowthBook
  Kohavi session, full read of summary):
  https://www.growthbook.io/blog/lessons-learned-from-ronny-kohavi-and-luke-sonnet-running-trustworthy-experiments
  SRM is the number-one trust check (50.2/49.8 at scale can be p~1/500,000;
  ~6% of mature Microsoft experiments had SRM). Peeking inflates a 5%
  false-positive rate to ~17% when checked daily for two extra weeks;
  plan fixed horizon or a sequential/alpha-spending method in advance.
  Twyman's law: an effect that looks too good is usually a bug.
- Anthropic, "Demystifying evals for AI agents": A/B tests are one layer
  of the Swiss-cheese picture, distinct from automated evals and
  production monitoring - they do not replace either.
Exit 0=PASS, 1=FAIL.
"""
import json, sys
def check(d):
    f=[]
    dec=d.get("decision") or {}
    if not dec.get("decision_recorded"): f.append("EX-0 the experiment surface is not recorded as a decided surface - changes ship as releases and are later narrated as tests")
    if not dec.get("owner_recorded"): f.append("EX-0 no single owner is recorded for experiment design - nobody is responsible when a test is read wrong")
    if not dec.get("canonical_source_recorded"): f.append("EX-0 the canonical source is not recorded (GrowthBook design steps / Kohavi trustworthy experiments) - every loop invents its own definition of a valid test")
    des=d.get("design") or {}
    if not des.get("hypothesis_causal_recorded"): f.append("EX-1 no causal hypothesis is recorded before launch (population, change, outcome, mechanism) - a result cannot teach anything because nothing was predicted")
    if not des.get("eligible_population_defined"): f.append("EX-1 the eligible population and exclusions are not defined before assignment - post-treatment filtering can bias the comparison")
    if not des.get("single_primary_metric_defined"): f.append("EX-1 there is not exactly one pre-registered primary metric with numerator, denominator and window - any metric that moved can be declared the win")
    pow_=d.get("power") or {}
    if not pow_.get("mde_and_sample_planned"): f.append("EX-2 minimum detectable effect, baseline and sample/power are not planned before launch - at small traffic the test cannot detect an economically meaningful effect and a null result means nothing")
    if not pow_.get("randomization_unit_and_stable_bucketing"): f.append("EX-2 the randomization unit and stable bucketing are not defined - the same user can see both variants and analysis units can mismatch assignment units")
    if not pow_.get("duration_fixed_or_sequential_method"): f.append("EX-2 neither a fixed duration/horizon nor a named sequential method is fixed before launch - the run length is decided by how the results look")
    integ=d.get("integrity") or {}
    if not integ.get("srm_check_planned_first"): f.append("EX-3 no sample-ratio-mismatch check is planned as the first read - a broken split (Kohavi: ~6% of mature experiments) is read as a treatment effect")
    if not integ.get("exposure_defined_and_logged"): f.append("EX-3 exposure is not defined and logged separately from assignment (experiment, variant, unit, timestamp, version) - assigned-but-never-exposed users dilute or bias the read")
    if not integ.get("aa_or_qa_before_launch"): f.append("EX-3 no A/A test or assignment/exposure QA is done before launch - instrumentation bugs are discovered inside the real test, if at all")
    cond=d.get("conduct") or {}
    if not cond.get("no_peeking_rule_or_sequential"): f.append("EX-4 there is no peeking rule and no sequential/alpha-spending plan - daily checking inflates false positives (5% toward ~17% in Kohavi's example)")
    if not cond.get("guardrails_with_thresholds"): f.append("EX-4 guardrail metrics with pre-set thresholds (errors, refunds, cancellations, revenue) are not defined - a primary win can ship while harming the business")
    if not cond.get("single_change_or_exclusion"): f.append("EX-4 concurrent changes are not isolated (one change at a time, or mutual exclusion / factorial by design) - effects cannot be attributed to the change that shipped")
    rul=d.get("ruling") or {}
    if not rul.get("decision_rule_preregistered"): f.append("EX-5 the decision rule for positive / negative / inconclusive / mixed outcomes is not written before results - the ship call is negotiated after seeing the numbers")
    if not rul.get("effect_reported_with_uncertainty"): f.append("EX-5 effects are not reported with uncertainty and practical significance - a tiny significant effect, or a large noisy one, is reported as a plain win or loss")
    if not rul.get("learning_recorded"): f.append("EX-5 the outcome and learning are not recorded in a durable ledger - the same test is re-run or re-argued because the last result was never written down")
    return f
if __name__=="__main__":
    data=json.load(open(sys.argv[1])); fails=check(data)
    if fails:
        print(f"FAIL ({len(fails)}):")
        [print(" -",x) for x in fails]; sys.exit(1)
    print("PASS")
