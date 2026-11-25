#!/usr/bin/env python3
"""multi-agent-check: deterministic gate for the MULTI-AGENT RESEARCH /
DELEGATION surface (an orchestrator-worker system where a lead agent
plans, decomposes the work and spawns specialized subagents that run in
parallel in their own context windows; delegation only works with
detailed briefs -- objective, output format, tool/source guidance and
clear boundaries -- and with effort scaled to complexity in the prompt;
search starts wide then narrows, extended/interleaved thinking is the
scratchpad, tool calling is parallel; evaluation judges outcomes with a
flexible rubric rather than prescribed paths, starts immediately on
small samples, uses a single-call LLM judge plus human testing; in
production, stateful agents resume from checkpoints instead of
restarting, decision patterns are traced without reading conversation
contents, and subagent outputs go to a filesystem as artifacts with
lightweight references back to the coordinator). Stdlib only, offline.
Canonical source (read in full 2026-11-18, Anthropic Engineering,
"How we built our multi-agent research system",
https://www.anthropic.com/engineering/multi-agent-research-system,
published 2025-06-13, updated 2026-10-09, 227 lines read via browser.open):
- Fit/economics: multi-agent outperformed single-agent by 90.2% on the
  internal research eval (Opus 4 lead + Sonnet 4 subagents); token usage
  alone explains 80% of BrowseComp variance (95% with tool calls + model);
  agents use ~4x chat tokens, multi-agent ~15x -- so the surface only
  pays for high-value tasks with heavy parallelization, information
  beyond one context window, and many complex tools; domains needing
  shared context / many interdependencies are a poor fit today.
- Architecture: orchestrator-worker; subagents compress by exploring in
  parallel in separate context windows with distinct tools, prompts and
  trajectories (separation of concerns, less path dependency).
- Delegation: each subagent needs an objective, an output format,
  guidance on tools and sources, and clear task boundaries; vague short
  instructions cause duplication, gaps and misinterpretation.
- Effort scaling in the prompt: simple fact-finding 1 agent / 3-10 tool
  calls; direct comparisons 2-4 subagents / 10-15 calls each; complex
  research >10 subagents with clearly divided responsibilities.
- Search/thinking/tools: start with short broad queries then narrow;
  lead uses extended thinking to plan (tools, complexity, subagent
  count, roles), subagents use interleaved thinking after tool results;
  examine all available tools first, match tool to intent, prefer
  specialized tools; each tool needs a distinct purpose + clear
  description.
- Parallelism: lead spins up 3-5 subagents in parallel, subagents use
  3+ tools in parallel -- cut research time by up to 90%.
- Evaluation: agents take different valid paths, so judge outcomes and
  reasonable process, not prescribed steps; start immediately with
  ~20 real-usage queries (large effect sizes are visible on small
  samples); a single LLM call with one rubric prompt scoring 0.0-1.0
  plus pass/fail (factual accuracy, citation accuracy, completeness,
  source quality, tool efficiency) was most consistent with humans;
  human evaluation still catches what automation misses (e.g. SEO
  content farms preferred over authoritative sources).
- Production: agents are stateful and errors compound -- durable
  execution, retry logic and regular checkpoints, resume from where the
  error occurred instead of restarting, and let the agent adapt when a
  tool fails; full production tracing of decision patterns and
  interaction structures (without monitoring conversation contents)
  makes non-deterministic failures diagnosable.
- Appendix: subagent output to a filesystem minimizes the 'game of
  telephone' -- specialized agents store work in external systems and
  pass lightweight references back to the coordinator, preserving
  fidelity and cutting token overhead.
Exit 0=PASS, 1=FAIL.
"""
import json, sys
def check(d):
    f=[]
    dec=d.get("decision") or {}
    if not dec.get("decision_recorded"): f.append("MA-0 the multi-agent surface is not recorded as a decided surface - when to run one lead with parallel subagents versus one agent is left to per-task habit")
    if not dec.get("owner_recorded"): f.append("MA-0 no owner is recorded for the multi-agent surface - nobody is named to keep delegation quality, effort budgets and evals honest")
    if not dec.get("canonical_source_recorded"): f.append("MA-0 the canonical source is not recorded (Anthropic multi-agent research system: orchestrator-worker, detailed delegation, effort scaled in the prompt, parallel execution, outcome evaluation, resumable traced production) - every orchestrator invents its own delegation shape")
    arc=d.get("architecture") or {}
    if not arc.get("orchestrator_worker_pattern"): f.append("MA-1 work is not run as orchestrator-worker (a lead that plans and decomposes, specialized subagents that execute) - coordination is ad hoc chat between agents")
    if not arc.get("fit_checked_before_spawning"): f.append("MA-1 fit is not checked before spawning (heavy parallelization, information beyond one context window, task value high enough for roughly 15x chat tokens; shared-context / high-dependency work excluded) - multi-agent is spent on tasks a single agent, or no agent, should do")
    if not arc.get("separate_contexts_distinct_roles"): f.append("MA-1 subagents do not run in separate context windows with distinct tools, prompts and exploration trajectories - there is no compression or separation of concerns, only copies of the same search")
    dlg=d.get("delegation") or {}
    if not dlg.get("detailed_briefs_objective_format_tools_boundaries"): f.append("MA-2 subagent briefs do not always carry an objective, an output format, guidance on tools and sources, and clear task boundaries - vague short instructions are the measured cause of duplicated work, gaps and misinterpretation")
    if not dlg.get("effort_scaling_rules_in_prompt"): f.append("MA-2 effort is not scaled to complexity by explicit rules (simple: 1 agent / 3-10 tool calls; comparison: 2-4 subagents / 10-15 calls each; complex: >10 subagents with divided responsibilities) - simple queries over-spawn and complex ones under-spawn")
    if not dlg.get("parallel_spawning_and_tool_calls"): f.append("MA-2 execution is not parallel by default (lead spawns 3-5 subagents in parallel, subagents call 3+ tools in parallel) - serial delegation gives back the up-to-90% time saving the architecture exists for")
    srch=d.get("search_thinking") or {}
    if not srch.get("start_wide_then_narrow"): f.append("MA-3 search strategy is not start-wide-then-narrow (short broad queries first, evaluate what exists, then progressively focus) - agents default to long specific queries that return few results")
    if not srch.get("thinking_as_scratchpad"): f.append("MA-3 thinking is not used as the controllable scratchpad (lead plans tools, complexity, subagent count and roles before spawning; subagents think interleaved after tool results to judge quality and gaps) - delegation is improvised instead of planned")
    if not srch.get("tool_selection_heuristics"): f.append("MA-3 tool selection has no explicit heuristics (examine all available tools first, match tool to intent, prefer specialized over generic, every tool has a distinct purpose and a clear description) - a bad or wrong tool choice dooms the subagent before it starts")
    ev=d.get("evaluation") or {}
    if not ev.get("start_small_immediately"): f.append("MA-4 evaluation does not start immediately on a small set of real-usage cases (about 20) - teams delay evals waiting for hundreds of cases while large early effect sizes go unmeasured")
    if not ev.get("llm_judge_rubric_single_call"): f.append("MA-4 outputs are not graded by a single-call LLM judge against one rubric (factual accuracy, citation accuracy, completeness, source quality, tool efficiency; 0.0-1.0 scores plus pass/fail) judging outcomes and reasonable process rather than prescribed steps - multi-agent paths differ validly, so step-checking alone misjudges them")
    if not ev.get("human_evaluation_kept"): f.append("MA-4 human evaluation is not kept alongside automation - the failures automation misses (hallucinations on unusual queries, subtle source-selection bias such as SEO farms over authoritative sources) stay invisible")
    prod=d.get("production") or {}
    if not prod.get("resume_from_checkpoint_not_restart"): f.append("MA-5 stateful runs cannot resume from where an error occurred (durable execution, retries and regular checkpoints, and the agent told when a tool fails so it can adapt) - minor failures become catastrophic restarts because errors compound across long runs")
    if not prod.get("decision_pattern_tracing"): f.append("MA-5 there is no full tracing of agent decision patterns and interaction structures (without reading conversation contents) - non-deterministic failures cannot be diagnosed, only re-rolled")
    if not prod.get("filesystem_artifact_handoff"): f.append("MA-5 subagent outputs do not go to a filesystem / external store with lightweight references back to the coordinator - everything is copied through the lead's conversation, losing fidelity and burning tokens (the game of telephone)")
    return f
if __name__=="__main__":
    data=json.load(open(sys.argv[1])); fails=check(data)
    if fails:
        print(f"FAIL ({len(fails)}):")
        [print(" -",x) for x in fails]; sys.exit(1)
    print("PASS")
