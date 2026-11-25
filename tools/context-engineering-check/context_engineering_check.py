#!/usr/bin/env python3
"""context-engineering-check: deterministic gate for the CONTEXT ENGINEERING
surface (smallest high-signal context, right-altitude prompts, minimal tools,
canonical examples, just-in-time retrieval, compaction, structured notes,
sub-agent distillation, attention-budget measurement). Stdlib only, offline.
Canonical source (read in full 2026-11-18, Anthropic, "Effective context
engineering for AI agents", 2025-09-29, updated 2026-10-18,
https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents):
- Context is a finite resource with diminishing returns: context rot means
  recall degrades as tokens grow; every token draws on an attention budget
  (transformer n^2 pairwise attention, patterns trained mostly on shorter
  sequences). Guiding principle: find the smallest possible set of
  high-signal tokens that maximize the likelihood of the desired outcome.
- System prompts at the right altitude: neither brittle hardcoded logic nor
  vague high-level guidance; organized into distinct sections; start from a
  minimal prompt tested with the best model, add instructions/examples only
  from observed failure modes. Minimal does not mean short.
- Tools: self-contained, robust, clear, minimal overlap, token-efficient
  returns. Bloated tool sets with ambiguous choice points are a top failure
  mode - if a human cannot say which tool applies, an agent cannot either.
- Examples: curate a diverse canonical set; do not stuff a laundry list of
  edge cases / every rule into the prompt. Examples are pictures worth a
  thousand words.
- Just-in-time: keep lightweight identifiers (paths, queries, links) and
  load data at runtime with tools instead of pre-processing everything up
  front; metadata (names, folders, timestamps) is itself a signal;
  progressive disclosure assembles understanding layer by layer. Hybrid:
  some data up front for speed plus autonomous exploration; boundary is
  task-dependent. Do the simplest thing that works.
- Long-horizon: compaction (summarize near the limit, restart with the
  summary; tune for recall first, then precision; tool-result clearing is
  the safest light-touch form), structured note-taking (notes persisted
  outside the window, pulled back later), sub-agent architectures (each
  sub-agent explores deeply but returns a condensed 1,000-2,000 token
  summary; detailed context stays isolated, lead synthesizes).
Exit 0=PASS, 1=FAIL.
"""
import json, sys
def check(d):
    f=[]
    dec=d.get("decision") or {}
    if not dec.get("decision_recorded"): f.append("CX-0 the context-engineering surface is not recorded as a decided surface - what enters the model's context at each step is left to accumulation, not curation")
    if not dec.get("owner_recorded"): f.append("CX-0 no context-engineering owner is recorded - nobody is named to keep the attention budget, compaction and pruning honest")
    if not dec.get("canonical_source_recorded"): f.append("CX-0 the canonical source is not recorded (Anthropic Effective Context Engineering: smallest high-signal set, right altitude, minimal tools, just-in-time, compaction / notes / sub-agents) - every surface stuffs its own context")
    ana=d.get("anatomy") or {}
    if not ana.get("system_prompt_right_altitude_tested_minimal"): f.append("CX-1 the system prompt is not held at the right altitude and tested from a minimal version (neither brittle hardcoded logic nor vague guidance; sections distinct; additions only from observed failure modes) - the prompt grew by accretion and was never cut back against failures")
    if not ana.get("tools_minimal_nonoverlapping_token_efficient"): f.append("CX-1 the tool set is not audited as minimal, non-overlapping and token-efficient (self-contained, clear intended use, descriptive inputs) - bloated or ambiguous tools create decision points a human could not resolve either")
    if not ana.get("examples_canonical_diverse_not_laundry_list"): f.append("CX-1 examples are not a curated diverse canonical set - the prompt carries a laundry list of edge cases and rules instead of the few examples that portray the expected behaviour")
    jit=d.get("just_in_time") or {}
    if not jit.get("identifiers_kept_data_loaded_at_runtime"): f.append("CX-2 context is not just-in-time (lightweight identifiers - paths, stored queries, links - kept and loaded at runtime with tools) - everything is pre-processed into the window up front, paying rot for data that may never be used")
    if not jit.get("hybrid_boundary_decided_per_task"): f.append("CX-2 the hybrid boundary is not decided per task (what is loaded up front for speed vs explored autonomously at runtime) - the level of autonomy is an accident of the first implementation")
    if not jit.get("progressive_disclosure_metadata_used"): f.append("CX-2 progressive disclosure and reference metadata are not used as signals (file names, folder hierarchy, timestamps guide what to open next; understanding is assembled layer by layer) - the agent either drowns in exhaustive context or wanders without signals")
    lh=d.get("long_horizon") or {}
    if not lh.get("compaction_tuned_recall_then_precision"): f.append("CX-3 there is no tuned compaction (summarize near the limit and restart from the summary; prompt tuned on real traces for recall first, then precision; critical decisions and unresolved items preserved) - long tasks either overflow or lose subtle context whose importance appears later")
    if not lh.get("structured_notes_outside_context_pulled_back"): f.append("CX-3 there is no structured note-taking (notes persisted outside the context window and pulled back at later steps) - progress, tallies and dependencies live only in the window and are lost across resets and dozens of tool calls")
    if not lh.get("subagents_return_distilled_summaries"): f.append("CX-3 sub-agents do not return only condensed distilled summaries (about 1,000-2,000 tokens) with detailed search context isolated inside them - the lead context is flooded with raw exploration and loses the synthesis role")
    bud=d.get("budget_measurement") or {}
    if not bud.get("attention_budget_rot_measured_on_own_traces"): f.append("CX-4 the attention budget is not measured on own traces (recall / task success as context grows; context rot is a gradient, not a cliff) - 'more context' is added on faith while precision silently degrades")
    if not bud.get("tool_result_clearing_and_pruning_applied"): f.append("CX-4 tool-result clearing and pruning are not applied (raw results deep in history are cleared once used; stale and redundant content is removed) - the safest light-touch compaction is left unused and pollution accumulates")
    if not bud.get("smallest_high_signal_set_compared"): f.append("CX-4 candidate context configurations are not compared against the smallest high-signal set (same tasks, success / recall / cost / latency) - there is no evidence the current set earns its tokens")
    dis=d.get("discipline") or {}
    if not dis.get("context_configuration_versioned_as_unit"): f.append("CX-5 the whole context configuration (system prompt, tools, examples, retrieval policy, compaction and notes policy) is not versioned as one unit - a behaviour change cannot be attributed to the context change that caused it")
    if not dis.get("context_changes_evaluated_before_promotion"): f.append("CX-5 context changes are not evaluated on a fixed set before promotion and linked to their results - a larger or reordered context ships on intuition and regressions are found by users")
    if not dis.get("simplest_thing_autonomy_boundary_recorded"): f.append("CX-5 the simplicity / autonomy boundary is not recorded (do the simplest thing that works; grant more autonomy only as evaluations prove it) - engineering effort and agent freedom grow without the evidence the source requires")
    return f
if __name__=="__main__":
    data=json.load(open(sys.argv[1])); fails=check(data)
    if fails:
        print(f"FAIL ({len(fails)}):")
        [print(" -",x) for x in fails]; sys.exit(1)
    print("PASS")
