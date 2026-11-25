#!/usr/bin/env python3
"""tool-use-check: deterministic gate for the AGENT TOOL DESIGN surface
(choosing few high-impact tools instead of API wrappers, consolidation,
distinct purpose, namespacing, meaningful context with natural identifiers,
response_format concise/detailed, pagination/filtering/truncation with
sensible defaults, helpful truncation and error guidance, prompt-engineered
descriptions with unambiguous parameters, real-world verifiable eval tasks,
call/token/error/runtime metrics, transcript analysis with agent collaboration,
held-out sets, local prototyping, pruning and consistency on change).
Stdlib only, offline.
Canonical source (read in full 2026-11-18, Anthropic, "Writing effective
tools for AI agents - with agents", 2025-09-11,
https://www.anthropic.com/research/writing-tools-for-agents):
- Tools are contracts between deterministic systems and non-deterministic
  agents; design them for agents, not like ordinary APIs for developers.
- More tools do not mean better outcomes: do not merely wrap existing API
  endpoints. Build a few thoughtful tools for specific high-impact workflows
  (search_contacts, not list_contacts); consolidate chained multi-step work
  into one call (schedule_event, not list_users+list_events+create_event);
  every tool needs a clear, distinct purpose; overlapping tools distract.
- Namespace by service and resource (asana_search, asana_projects_search);
  prefix vs suffix choice itself moves eval results, so choose by evaluation.
- Return only high-signal context: prioritize contextual relevance over
  flexibility, resolve cryptic UUIDs to meaningful names / simple IDs, and
  expose a response_format enum (concise vs detailed) so agents control
  verbosity; pick response structure (XML/JSON/Markdown) by evaluation.
- Token efficiency: pagination, range selection, filtering and/or truncation
  with sensible defaults (Claude Code caps responses at 25,000 tokens).
  Truncation must steer agents to targeted strategies; error responses must
  state specific, actionable fixes, not opaque codes or tracebacks.
- Prompt-engineer descriptions like onboarding a new hire: make implicit
  context explicit, name parameters unambiguously (user_id, not user),
  enforce inputs/outputs with strict data models. Small refinements moved
  SWE-bench Verified to state of the art for Claude Sonnet 3.5.
- Evaluate: prototype locally first; generate many eval tasks grounded in
  real-world use with realistic data and verifiable outcomes (avoid strict
  verifiers that reject correct answers on formatting); run programmatically;
  collect accuracy plus runtime, tool-call count, token consumption and tool
  errors; read reasoning/feedback AND raw transcripts (omissions matter);
  let agents analyze concatenated transcripts and refactor tools; keep
  held-out test sets so improvements do not overfit the training evals.
Exit 0=PASS, 1=FAIL.
"""
import json, sys
def check(d):
    f=[]
    dec=d.get("decision") or {}
    if not dec.get("decision_recorded"): f.append("TU-0 the tool-design surface is not recorded as a decided surface - which agent-facing tools exist, and under what design rules, is left to habit")
    if not dec.get("owner_recorded"): f.append("TU-0 no tool-design owner is recorded - nobody is named to keep tool selection, descriptions and eval results honest")
    if not dec.get("canonical_source_recorded"): f.append("TU-0 the canonical source is not recorded (Anthropic Writing effective tools for agents: few high-impact tools, consolidation, namespacing, meaningful context, token efficiency, prompt-engineered descriptions, evaluation with transcripts and held-out sets) - every tool author invents their own interface")
    sel=d.get("selection") or {}
    if not sel.get("few_high_impact_tools_not_api_wrappers"): f.append("TU-1 tools merely wrap existing API endpoints or a long tool list is kept without selecting a few high-impact workflows - agents drown in low-affordance surface area and burn context reading irrelevant returns (list_contacts instead of search_contacts)")
    if not sel.get("consolidated_multi_step_workflows"): f.append("TU-1 frequently chained multi-step work is not consolidated into single tools (schedule_event instead of list_users + list_events + create_event) - intermediate outputs consume the agent context the tool was meant to save")
    if not sel.get("distinct_purpose_no_overlap"): f.append("TU-1 tools do not each have a clear, distinct purpose, or overlapping tools remain - if a human cannot say definitively which tool to use, the agent cannot either, and efficient strategies are crowded out")
    ctx=d.get("context") or {}
    if not ctx.get("namespaced_by_service_and_resource"): f.append("TU-2 tools are not namespaced by service and resource (asana_search, asana_projects_search) - with dozens of servers and hundreds of tools, vague boundaries make agents pick the wrong tool")
    if not ctx.get("meaningful_context_natural_identifiers"): f.append("TU-2 tool returns are not limited to high-signal context with meaningful names instead of cryptic UUIDs and low-level technical fields - retrieval precision drops and hallucinations rise on identifiers agents cannot interpret")
    if not ctx.get("response_format_concise_detailed"): f.append("TU-2 tools expose no response_format control (concise vs detailed) and response structure is not chosen by evaluation - agents cannot control verbosity, so every call pays the detailed price")
    tok=d.get("token_efficiency") or {}
    if not tok.get("pagination_range_filtering_truncation_defaults"): f.append("TU-3 responses that can consume large context have no pagination, range selection, filtering or truncation with sensible defaults - a single broad call can spend the context the rest of the task needed")
    if not tok.get("truncation_and_errors_guide_action"): f.append("TU-3 truncation does not steer agents toward targeted, token-efficient strategies and error responses are opaque codes or tracebacks instead of specific, actionable fixes - agents repeat the same failing call")
    if not tok.get("descriptions_prompt_engineered_unambiguous_params"): f.append("TU-3 tool descriptions are not prompt-engineered like onboarding a new hire (implicit context made explicit, parameters named unambiguously - user_id not user, strict input/output models) - the cheapest performance lever in the whole system is left unpulled")
    ev=d.get("evaluation") or {}
    if not ev.get("eval_tasks_real_world_verifiable"): f.append("TU-4 there are no evaluation tasks grounded in real-world use with realistic data and verifiable outcomes (or verifiers are so strict they reject correct answers on formatting) - tool quality is asserted, never measured")
    if not ev.get("metrics_collected_calls_tokens_errors_runtime"): f.append("TU-4 evaluation collects no metrics beyond accuracy (runtime, tool-call count, token consumption, tool errors) - redundant calls and invalid-parameter errors that reveal consolidation and description fixes stay invisible")
    if not ev.get("transcripts_read_and_agents_collaborate_to_improve"): f.append("TU-4 evaluation reasoning, feedback and raw transcripts are not read (including what agents omit) and agents do not help analyze transcripts and refactor tools - the failure modes only transcripts show never become fixes")
    evo=d.get("evolution") or {}
    if not evo.get("held_out_sets_prevent_overfitting"): f.append("TU-5 no held-out test sets are kept - tool 'improvements' overfit the training evaluations and regress on real work")
    if not evo.get("prototype_tested_locally_before_eval"): f.append("TU-5 tools are not prototyped and tested locally by hand before evaluation - rough edges that one hands-on pass would catch are shipped to every agent")
    if not evo.get("tools_pruned_and_descriptions_kept_consistent_on_change"): f.append("TU-5 the tool set is not pruned as needs change and descriptions/implementations are not kept self-consistent across changes - stale, overlapping tools accumulate and descriptions drift from behavior")
    return f
if __name__=="__main__":
    data=json.load(open(sys.argv[1])); fails=check(data)
    if fails:
        print(f"FAIL ({len(fails)}):")
        [print(" -",x) for x in fails]; sys.exit(1)
    print("PASS")
