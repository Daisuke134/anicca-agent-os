#!/usr/bin/env python3
"""cost-efficiency-check: deterministic gate for the LLM COST EFFICIENCY
surface (cost per successful task, quality-gated). Stdlib only, offline, free.
Canonical source (read in full 2026-11-18, CodeAustral, "Cutting LLM Costs
Without Hurting Quality: A Field Guide",
https://www.codeaustral.com/blog/ai-cost-optimization-llm-apps):
- Treat each request as a measurable task, not the monthly bill. Log input,
  cached-input and output tokens separately, model, route, retries,
  escalations, latency and a task-specific quality result.
- cost_per_successful_task = sum of EVERY call cost in the trace (retries and
  escalations included, each at its own rate) / tasks passing a PREWRITTEN
  quality gate. The denominator is the discipline: cheap-but-rejected is not
  cheap, and success must be defined before candidates are compared.
- CRAFT: Classify work by job/risk/shape; Record the whole trace; Assign a
  quality contract (must-pass, latency ceiling, disqualifying errors); Fit
  the least disruptive intervention to the measured concentration (stable
  prefix -> caching, redundant context -> trimming, non-interactive ->
  deferred/batch, mixed difficulty -> deterministic routing first); Test on
  the same task definition and a versioned sample, then keep or roll back.
- Rate cards live in config with an effective date; never copy a price from
  an old article. Report quality and latency BESIDE cost, never beneath it.
- A router/cascade is itself a cost line: count its calls, watch misroutes.
Exit 0=PASS, 1=FAIL.
"""
import json, sys
def check(d):
    f=[]
    dec=d.get("decision") or {}
    if not dec.get("decision_recorded"): f.append("CE-0 the cost-efficiency surface is not recorded as a decided surface - spend is reviewed as a monthly total, not managed per task")
    if not dec.get("owner_recorded"): f.append("CE-0 no single owner is recorded for unit cost - when cost per successful task rises, nobody is named to act")
    if not dec.get("canonical_source_recorded"): f.append("CE-0 the canonical source is not recorded (CodeAustral: cost per successful task, quality-gated, CRAFT) - every cost cut invents its own metric")
    mea=d.get("measurement") or {}
    if not mea.get("tasks_classified_by_job_risk_shape"): f.append("CE-1 work is not classified by job, risk and context shape - a short classification and a high-consequence synthesis are budgeted as if they were the same work")
    if not mea.get("whole_trace_recorded"): f.append("CE-1 the whole task trace is not recorded (task, prompt version, model/route, fresh vs cached vs output tokens, retries, escalations, latency, task outcome) - a gateway total cannot say which task caused the spend or whether a second call repaired the first")
    if not mea.get("cost_per_successful_task_computed"): f.append("CE-1 cost per successful task is not computed from every call in the trace divided by tasks passing the gate - cost per call hides repairs, retries and rejected work")
    con=d.get("contract") or {}
    if not con.get("quality_contract_per_task"): f.append("CE-2 there is no per-task quality contract (must-pass conditions, latency ceiling, disqualifying errors, success defined before any comparison) - a cheaper system can be made to look better by quietly accepting weaker outputs")
    if not con.get("current_rate_card_in_config"): f.append("CE-2 the current rate card is not kept in config with an effective date (fresh, cached and output rates separate) - calculations run on stale or copied article prices and mix old and new billing rules")
    if not con.get("quality_latency_reported_beside_cost"): f.append("CE-2 quality and latency are not reported beside the cost number - a cheaper but unusable or slower path can be selected on price alone")
    fit=d.get("intervention_fit") or {}
    if not fit.get("least_disruptive_single_change_first"): f.append("CE-3 interventions are not fitted least-disruptive-first, one change at a time, dominant task first - combined routing, compression and provider changes cannot be attributed when the result moves")
    if not fit.get("routing_deterministic_first_cheapest_passing"): f.append("CE-3 routing is not deterministic-first to the cheapest model that passes the task gate - frontier models do routine work by default, or a model router spends a call where a rule would do")
    if not fit.get("caching_context_batching_fitted"): f.append("CE-3 caching, context trimming and deferred/batch processing are not fitted to the measured concentration (stable repeated prefix, redundant context, non-interactive work) - the free levers are unused while the expensive pattern repeats")
    tst=d.get("test_decision") or {}
    if not tst.get("baseline_candidate_same_task_same_sample"): f.append("CE-4 baseline and candidate are not compared on the same task definition and a versioned evaluation sample - normal variation and traffic-mix shifts are read as savings")
    if not tst.get("decision_recorded_with_rollback_trigger"): f.append("CE-4 the keep/roll-back decision and its rollback trigger (quality breach, latency or escalation ceiling, billing mismatch) are not recorded before exposure - a breached candidate stays live and the lesson is erased by the next change")
    if not tst.get("router_cascade_cost_counted"): f.append("CE-4 router and cascade costs are not counted as their own lines (router calls, escalation rate, misroutes) - a cheap first pass that escalates often is more expensive than never switching, and the ledger cannot see it")
    grd=d.get("guardrails_evolution") or {}
    if not grd.get("budgets_caps_alerts_no_autoreload"): f.append("CE-5 there are no per-task/per-user budgets, step limits and spend alerts, and no bar on silent auto-reload/top-up - spend can grow unbounded between monthly reviews")
    if not grd.get("non_token_costs_scoped_consistently"): f.append("CE-5 non-token operating costs (queueing, storage, observability, evaluation, human review) are not scoped consistently between baseline and candidate - token savings can hide a larger total cost")
    if not grd.get("worksheet_revisited_on_change"): f.append("CE-5 the cost worksheet and intervention ledger are not revisited when the task, traffic mix or provider billing changes - optimisations rot silently as prices and workloads move")
    return f
if __name__=="__main__":
    data=json.load(open(sys.argv[1])); fails=check(data)
    if fails:
        print(f"FAIL ({len(fails)}):")
        [print(" -",x) for x in fails]; sys.exit(1)
    print("PASS")
