#!/usr/bin/env python3
"""model-release-check: deterministic gate for the MODEL RELEASE /
CHECKPOINT SELECTION surface (deciding whether a post-trained candidate
replaces the prior / base model in production). Stdlib only, offline, free.
Canonical source (read 2026-11-17/18):
- Anthropic, "Demystifying evals for AI agents" (2026-01-09)
  https://www.anthropic.com/research/demystifying-evals-for-ai-agents
  Capability evals and regression evals are different suites: capability
  evals start at a low pass rate and give a slope to climb; regression
  evals should pass at nearly 100% and catch backsliding. When a
  capability suite saturates, its tasks graduate into the regression
  suite. Because outputs vary between runs, run multiple trials:
  pass@k (at least one success in k) vs pass^k (all k succeed) - for
  consistency-critical behaviour pass^k is the number that matters.
  A task at 0% across many trials (pass@100 = 0) most often signals a
  broken task, spec or grader, not an incapable model. Read transcripts
  and outcomes before trusting any total score; a better total can hide
  a regression in the case that matters most. Negative capability -
  what the system must NOT do - is part of the eval surface.
Exit 0=PASS, 1=FAIL.
"""
import json, sys
def check(d):
    f=[]
    dec=d.get("decision") or {}
    if not dec.get("decision_recorded"): f.append("MR-0 the model-release / checkpoint-selection surface is not recorded as a decided surface - candidates are promoted by impression and no release can be compared to another")
    if not dec.get("owner_recorded"): f.append("MR-0 no single owner is recorded for model release - when a promoted model regresses in production, nobody owns the promotion decision")
    if not dec.get("canonical_source_recorded"): f.append("MR-0 the canonical source is not recorded (Anthropic demystifying evals) - every release invents its own promotion rule")
    sep=d.get("separation") or {}
    if not sep.get("capability_and_regression_suites_separate"): f.append("MR-1 capability and regression evals are not run as separate suites - a score drop cannot be told apart from harder cases being added, and backsliding hides inside capability gains")
    if not sep.get("regression_suite_near_100_bar"): f.append("MR-1 the regression suite has no near-100% pass bar - solved behaviour is allowed to break silently as long as the total looks acceptable")
    if not sep.get("capability_suite_starts_low_with_slope"): f.append("MR-1 the capability suite does not start low with a climbable slope - a saturated or trivial suite measures nothing and gives post-training no hill to climb")
    tri=d.get("trials") or {}
    if not tri.get("multiple_trials_per_task"): f.append("MR-2 tasks are run once per candidate - model outputs vary between runs, so a single trial cannot distinguish a real difference from noise")
    if not tri.get("pass_at_k_and_pass_caret_k_reported"): f.append("MR-2 pass@k and pass^k are not both reported - for consistency-critical behaviour only pass^k (all k trials succeed) shows whether the behaviour can be relied on")
    if not tri.get("zero_pass_investigated_as_broken_task"): f.append("MR-2 a task at 0% across many trials is read as model incapability without first investigating the task, spec and grader - Anthropic: 0% pass@100 most often signals a broken task, not an incapable model")
    cmp_=d.get("comparison") or {}
    if not cmp_.get("same_conditions_all_candidates"): f.append("MR-3 candidates are not compared under identical conditions (same dataset version, same graders, same trial count) - a better score may come from a moved bar, not a better model")
    if not cmp_.get("negative_capability_checked"): f.append("MR-3 negative capability is not evaluated (what the model must NOT do: prohibited interventions, unsafe or off-policy behaviour) - a candidate can win on positives while failing the cases that must never happen")
    if not cmp_.get("cost_latency_tokens_compared"): f.append("MR-3 cost, latency and token use are not compared alongside quality - a marginally better candidate that costs multiples more destroys gross profit at scale")
    rel=d.get("release_decision") or {}
    if not rel.get("preregistered_promotion_thresholds"): f.append("MR-4 promotion thresholds are not written before the run - the bar moves to fit the result the team wanted, and every release becomes a negotiation")
    if not rel.get("regressions_read_before_total"): f.append("MR-4 the total score is read before (or instead of) the regression failures - a better total can hide a regression in exactly the case the product can least afford")
    if not rel.get("prior_fallback_plan"): f.append("MR-4 there is no recorded fallback (the prior / base model keeps serving until a candidate clears the gate, and a promoted model can be rolled back) - a bad promotion has no way back")
    evo=d.get("evolution") or {}
    if not evo.get("saturated_tasks_graduate_to_regression"): f.append("MR-5 saturated capability tasks do not graduate into the regression suite - solved behaviour leaves the measured surface and can break unnoticed in the next release")
    if not evo.get("new_failures_become_cases"): f.append("MR-5 new failures found in production or transcript review do not become eval cases before the next release - the same failure can ship twice")
    if not evo.get("release_log_with_versions_and_scores"): f.append("MR-5 there is no release log tying model version, dataset version, grader version, trial count and scores together - no past promotion can be reproduced or audited")
    return f
if __name__=="__main__":
    data=json.load(open(sys.argv[1])); fails=check(data)
    if fails:
        print(f"FAIL ({len(fails)}):")
        [print(" -",x) for x in fails]; sys.exit(1)
    print("PASS")
