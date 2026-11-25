#!/usr/bin/env python3
"""rollout-check: deterministic gate for the PROGRESSIVE ROLLOUT /
SAFE DEPLOYMENT surface (every LLM change is a release: eval-gated in CI,
shadowed, canaried with a sticky automatic verdict, reversible in one
config step). Stdlib only, offline, free.
Canonical source (read in full 2026-11-18, LLMOps.si, "LLM Deployment:
CI/CD, staging and one-step rollback",
https://www.llmops.si/articles/llm-deployment-ci-cd-staging-rollback/):
- An LLM change (new prompt, model swap, retrieval tweak) is a deploy:
  tested in CI, rolled out progressively, reversible in one step. Skipping
  that turns a one-line prompt edit into a production incident.
- Controls: CI with an eval gate (a change cannot merge on a regression),
  a staging environment that mirrors production, progressive rollout,
  one-step config-driven rollback (not a code redeploy), an evaluated
  provider/model fallback, and a recorded change log.
- Shadow first, then canary: shadow sends a copy of live requests to the
  candidate, serves the stable answer, stores both; compare offline with
  judge + literal checks plus latency and tokens, and read the
  disagreements by hand. Shadow a sample for days, never anything with
  side effects, and treat shadow copies as production data.
- Canary assignment is sticky: hash a stable user id (salted per rollout),
  never random per request. The verdict compares canary vs stable over
  the SAME window on error rate, p95 latency, eval pass rate and cost per
  request, with a minimum traffic floor before any verdict.
- Fallback chains: every model in the chain passes the same eval set,
  fallback events are logged and alerted, a circuit breaker skips a down
  provider, and non-retryable errors (400) are never retried elsewhere.
- Release checklist before 100%: eval passed in CI with no critical case
  regressed, token/cost compared, shadow reviewed, canary covered the
  daily traffic shape with a promote verdict, prior version still
  deployable, change + owner + eval result in the change log.
Exit 0=PASS, 1=FAIL.
"""
import json, sys
def check(d):
    f=[]
    dec=d.get("decision") or {}
    if not dec.get("decision_recorded"): f.append("RO-0 the rollout / safe-deployment surface is not recorded as a decided surface - how a model or prompt change reaches users is decided ad hoc per change and big-bang release is the default")
    if not dec.get("owner_recorded"): f.append("RO-0 no single owner is recorded for releases and rollback - when a shipped change regresses, nobody is named to pull it back")
    if not dec.get("canonical_source_recorded"): f.append("RO-0 the canonical source is not recorded (LLMOps.si: every LLM change is a release, eval-gated, shadowed, canaried, reversible in one step) - every release invents its own route to users")
    pre=d.get("pre_release") or {}
    if not pre.get("ci_eval_gate_blocks_regression"): f.append("RO-1 there is no eval gate in CI that blocks a merge on regression (with no critical case regressed) - quality is a hope checked after users, not a merge condition")
    if not pre.get("staging_mirrors_production"): f.append("RO-1 there is no staging environment that mirrors production (same retrieval, same config) - changes are validated in production, on real users")
    if not pre.get("cost_token_compared_before_release"): f.append("RO-1 token count and cost per request are not compared with the current version before release - a slightly better change that costs multiples more ships unnoticed")
    sh=d.get("shadow") or {}
    if not sh.get("shadow_before_user_exposure_for_risky"): f.append("RO-2 risky changes (new model, rewritten prompt, different retriever) are not run in shadow mode first - the first real-traffic test of the candidate is served to users")
    if not sh.get("shadow_disagreements_reviewed"): f.append("RO-2 shadow outputs are not compared offline (judge + literal checks, latency, tokens) with a hand-read sample of the disagreements - the rows where candidate and stable differ, which carry the signal, are never looked at")
    if not sh.get("shadow_safeguards_sampled_no_side_effects"): f.append("RO-2 shadow safeguards are not fixed (sampled not everything, days not weeks, write tools stubbed out, shadow copies under the same redaction / access / retention rules as production traces) - shadowing can double spend, cause side effects, or leak data")
    can=d.get("canary") or {}
    if not can.get("sticky_assignment_by_stable_id"): f.append("RO-3 canary assignment is not sticky by stable user id (hash, salted per rollout) - the same person bounces between two behaviours within one conversation and neither slice is interpretable")
    if not can.get("staged_ladder_not_big_bang"): f.append("RO-3 rollout is not a staged ladder (small slice first, then widened step by step to 100%) - a change ships to all traffic at once and there is no small blast radius to learn from")
    if not can.get("minimum_sample_and_daily_shape"): f.append("RO-3 there is no minimum canary traffic floor and no requirement that the canary run long enough to cover the daily traffic shape - verdicts are read off a handful of requests at one time of day")
    ver=d.get("verdict_rollback") or {}
    if not ver.get("automatic_verdict_same_window"): f.append("RO-4 there is no automatic canary verdict comparing canary vs stable over the same window on error rate, p95 latency, eval pass rate and cost per request - a classic service canary would promote a change that fails on quality and cost, the two numbers only an LLM deploy needs")
    if not ver.get("one_step_config_rollback"): f.append("RO-4 rollback is not one step driven by config (point back at the previous known-good prompt + model) - a bad release means a frantic code redeploy instead of flipping one value")
    if not ver.get("prior_version_kept_deployable"): f.append("RO-4 the previous version is not kept deployable as a rollback target - there is nothing verified to roll back to")
    res=d.get("resilience_record") or {}
    if not res.get("evaluated_fallback_chain"): f.append("RO-5 the provider / model fallback chain is not itself evaluated (every model in the chain passes the same eval set, with its own prompt variant if needed) - an outage fails over to a model nobody ever tested")
    if not res.get("fallback_events_logged_alerted_breaker"): f.append("RO-5 fallback events are not logged and alerted with a circuit breaker (and non-retryable errors are retried elsewhere, hiding bugs) - running on the secondary for six hours goes unnoticed as an incident")
    if not res.get("changelog_with_owner_and_eval_result"): f.append("RO-5 the change, its owner and its eval result are not recorded in a change log - after the fact nobody can reconstruct what shipped, why, or on what evidence")
    return f
if __name__=="__main__":
    data=json.load(open(sys.argv[1])); fails=check(data)
    if fails:
        print(f"FAIL ({len(fails)}):")
        [print(" -",x) for x in fails]; sys.exit(1)
    print("PASS")
