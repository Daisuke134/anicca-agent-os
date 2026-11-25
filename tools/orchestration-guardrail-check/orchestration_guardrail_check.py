#!/usr/bin/env python3
"""orchestration-guardrail-check: deterministic gate for the AGENT ORCHESTRATION & GUARDRAILS
surface (single-agent first, tools classified, instructions from existing docs, manager vs
decentralized handoffs, run-loop exit conditions, layered guardrails, tool risk ratings,
output validation, execution mode, failure thresholds, high-risk oversight, failure-driven
layering). Stdlib only, offline.
Canonical source (read in full 2026-11-18, OpenAI, "A Practical Guide to Building Agents",
https://openai.com/business/guides-and-resources/a-practical-guide-to-building-ai-agents):
- Start with a single agent, maximize it first; split only for complex logic (many
  conditionals) or tool overload (similar/overlapping tools, not raw count).
- Tools are data / action / orchestration, standardized, documented, tested, reusable.
- Instructions from existing operating procedures/docs, broken into clear actions,
  with edge cases captured as conditional branches.
- Multi-agent: manager pattern (central agent calls specialists as tools, keeps control
  and synthesis) vs decentralized pattern (peers hand off execution one-way, transferring
  latest state; optional handoff back). Runs are loops until an exit condition (final-output
  tool, response without tool calls, error, max turns).
- Guardrails are layered defense, never one filter: relevance classifier, safety
  classifier (jailbreak / prompt injection), PII filter, moderation, tool safeguards,
  rules-based protections (blocklists, length limits, regex), output validation.
  Tool safeguards rate each tool low/medium/high by read-only vs write, reversibility,
  permissions, financial impact, and trigger checks or escalation.
- Execution is optimistic by default in the SDK (guardrails run concurrently, tripwire
  raises) - the mode is a decision, not an accident. Guardrails couple with auth,
  access controls and standard security, never replace them.
- Build heuristic: focus on data privacy and content safety first, add guardrails from
  real edge cases and failures, optimize for security AND user experience.
- Human intervention: exceeding failure thresholds (retries/actions) and high-risk
  actions (sensitive, irreversible, high stakes - cancel orders, large refunds, payments)
  trigger oversight / graceful transfer of control.
Exit 0=PASS, 1=FAIL.
"""
import json, sys
def check(d):
    f=[]
    dec=d.get("decision") or {}
    if not dec.get("decision_recorded"): f.append("OG-0 the orchestration-and-guardrails surface is not recorded as a decided surface - how agents are coordinated and fenced is left to habit, not decision")
    if not dec.get("owner_recorded"): f.append("OG-0 no orchestration-and-guardrails owner is recorded - nobody is named to keep patterns, risk ratings and thresholds honest")
    if not dec.get("canonical_source_recorded"): f.append("OG-0 the canonical source is not recorded (OpenAI Practical Guide: single-agent first, manager vs decentralized, layered guardrails, tool risk ratings, failure thresholds and high-risk oversight) - every workflow invents its own coordination and fencing")
    fd=d.get("foundations") or {}
    if not fd.get("single_agent_maximized_before_splitting"): f.append("OG-1 a single agent was not maximized first (split only on complex logic or tool overload - similarity/overlap, not raw count) - multi-agent complexity and overhead were bought before the simple form was proven insufficient")
    if not fd.get("tools_classified_and_standardized"): f.append("OG-1 tools are not classified as data / action / orchestration with standardized, documented, tested, reusable definitions - redundant definitions and unclear ownership multiply")
    if not fd.get("instructions_from_docs_clear_actions_edge_cases"): f.append("OG-1 instructions are not built from existing operating procedures into clear actions with edge cases as conditional branches - ambiguity is left for the model to resolve at runtime")
    orc=d.get("orchestration") or {}
    if not orc.get("pattern_chosen_manager_vs_decentralized"): f.append("OG-2 the orchestration pattern is not chosen and recorded per workflow (manager: central control and synthesis via tool calls vs decentralized: peers hand off execution) - who holds control and who talks to the user is an accident")
    if not orc.get("handoffs_transfer_state_with_return_path"): f.append("OG-2 handoffs do not transfer the latest state in a one-way handoff with an optional recorded return path - the receiving agent restarts from fragments or control is lost")
    if not orc.get("run_loop_exit_conditions_defined"): f.append("OG-2 run loops have no defined exit conditions (final-output tool, response without tool calls, error, maximum turns) - agents can loop, stall or stop for reasons nobody specified")
    gl=d.get("guardrail_layers") or {}
    if not gl.get("input_guardrails_layered"): f.append("OG-3 input guardrails are not layered (relevance classifier, safety classifier for jailbreaks/injection, PII filter, moderation, rules-based blocklists/limits/regex together) - a single filter is treated as sufficient protection")
    if not gl.get("tool_safeguards_risk_rated"): f.append("OG-3 tools carry no risk rating (low/medium/high from read-only vs write, reversibility, required permissions, financial impact) with automated actions triggered by the rating - a read and an irreversible payment are fenced identically")
    if not gl.get("output_validation_applied"): f.append("OG-3 output is not validated (brand values, content checks, PII vetting of model output) - what the agent says is shipped unchecked")
    ex=d.get("execution_and_intervention") or {}
    if not ex.get("guardrail_execution_mode_decided"): f.append("OG-4 the guardrail execution mode is not decided per risk (blocking checks before execution vs optimistic concurrent checks with a tripwire) - latency and safety trade-offs are accidental")
    if not ex.get("failure_thresholds_escalate"): f.append("OG-4 no failure thresholds escalate (limits on retries or actions; exceeding them gracefully transfers control) - a failing agent retries or stalls without bound")
    if not ex.get("high_risk_actions_trigger_oversight"): f.append("OG-4 high-risk actions do not trigger oversight (sensitive, irreversible or high-stakes actions - cancellations, large refunds, payments - are not fenced until reliability is proven) - the costliest actions have the least friction")
    ev=d.get("evolution") or {}
    if not ev.get("guardrails_added_from_real_failures"): f.append("OG-5 guardrails are not added from real-world edge cases and failures (privacy and content safety first, then layer as vulnerabilities are uncovered) - the fence reflects imagined risks while lived failures stay unfenced")
    if not ev.get("guardrails_tuned_for_security_and_ux"): f.append("OG-5 guardrails are not tuned for both security and user experience as the agent evolves - over-blocking and under-blocking are never measured or corrected")
    if not ev.get("guardrails_coupled_with_auth_and_access_controls"): f.append("OG-5 guardrails are treated as a substitute for authentication, authorization, strict access controls and standard security - prompt-level fencing carries weight it cannot hold")
    return f
if __name__=="__main__":
    data=json.load(open(sys.argv[1])); fails=check(data)
    if fails:
        print(f"FAIL ({len(fails)}):")
        [print(" -",x) for x in fails]; sys.exit(1)
    print("PASS")
