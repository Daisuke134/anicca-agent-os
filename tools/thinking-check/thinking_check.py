#!/usr/bin/env python3
"""thinking-check: deterministic gate for the THINKING surface
(how much a model reasons before and between answers - mode, depth,
preservation, display, measurement - is decided, not left to defaults).
Stdlib only, offline.
Canonical sources (read in full 2026-11-18):
- Anthropic Claude Platform Docs "Thinking"
  https://platform.claude.com/docs/en/build-with-claude/thinking
  (636 lines read in full): thinking blocks arrive before text blocks;
  each carries a signature (encrypted full reasoning, pass back
  unchanged); the visible text is a summary, never raw chain of
  thought. display: summarized returns the summary, omitted (default
  on many current models) returns empty thinking fields at the same
  billing - omitted cuts latency, not cost. Thinking tokens are billed
  as output tokens and count toward max_tokens. Modes per model:
  adaptive (model decides whether/how much to think, steered by
  effort), enabled with budget_tokens (manual), disabled, and
  between_tools (Sonnet 5.5 lowest setting); enabled returns 400 on
  4.7+ models, several models cannot disable thinking at all. Manual
  mode supports only tool_choice auto/none; adaptive supports forced
  tool use except on listed models, where an accepted forced call
  starts with the tool call and no thinking block. Tool-use turns must
  return every thinking block (including redacted_thinking) complete
  and unmodified; a tool-use loop is one assistant turn and thinking
  cannot be toggled mid-turn - a mid-turn toggle silently disables
  thinking, so verify thinking blocks are present. Interleaved
  thinking is automatic in adaptive mode; Haiku 4.5 has none.
  Preservation is per-model: keep-all models retain prior thinking as
  billed input and context; last-turn-only models strip it. Changing
  mode, budget or top-level effort invalidates prompt caching.
  Non-default sampling parameters and prefill are restricted on
  thinking models. Streaming delivers thinking_delta then a single
  signature_delta; reassemble with get_final_message().
- Anthropic Claude Platform Docs "Extended thinking"
  https://platform.claude.com/docs/en/build-with-claude/extended-thinking
  (186 lines read in full): manual budget_tokens minimum 1024, must be
  less than max_tokens (exception: interleaved, where the budget spans
  the turn), incompatible with max_tokens:0 cache pre-warming; the
  budget is a target, max_tokens is the hard ceiling. Start near 1024
  for simple tasks, 16k+ for complex ones; above 32k use batch
  processing. Track cost via usage.output_tokens_details.
  thinking_tokens (final message_delta only when streaming). Manual
  mode on Opus 4.6 has no interleaving; migration to adaptive removes
  budget_tokens and controls depth with output_config.effort, and
  adaptive may skip thinking entirely at low effort.
Exit 0=PASS, 1=FAIL.
"""
import json, sys
def check(d):
    f=[]
    dec=d.get("decision") or {}
    if not dec.get("decision_recorded"): f.append("TH-0 the thinking surface is not recorded as a decided surface - whether the model reasons before answering is left to route defaults and habit, not a decision")
    if not dec.get("owner_recorded"): f.append("TH-0 no owner is recorded for thinking correctness (mode, depth, preservation, cost) - a workload that silently stops thinking, or pays for thinking it never uses, has no accountable reader")
    if not dec.get("thinking_surfaces_inventoried"): f.append("TH-0 there is no inventory of the workloads by thinking need (complex reasoning and long agentic work versus simple speed-sensitive calls) - depth cannot be allocated where the surfaces are indistinguishable")
    mode=d.get("mode") or {}
    if not mode.get("mode_chosen_per_model"): f.append("TH-1 the thinking mode is not chosen per model (adaptive / enabled with budget / disabled / between_tools against the per-model configuration table) - a configuration one model accepts returns a 400 on another (enabled on 4.7+ models, disabled on models that cannot turn thinking off)")
    if not mode.get("depth_control_chosen"): f.append("TH-1 the depth control is not chosen deliberately (effort in adaptive mode, budget_tokens in manual mode) - the two are different controls, adaptive is a thinking mode and never an effort value, and an unchosen depth means the route default decides how much reasoning every task gets")
    if not mode.get("thinking_off_decision_explicit"): f.append("TH-1 where thinking is off is not an explicit decision - on default-on models silence means thinking (and its output-token cost) is on, and on models where thinking cannot be disabled the off switch does not exist to be assumed")
    cor=d.get("correctness") or {}
    if not cor.get("budget_rules_respected"): f.append("TH-2 manual budget rules are not respected (budget_tokens at least 1024 and less than max_tokens, the interleaved span-the-turn case the only exception, never combined with max_tokens:0 cache pre-warming) - the budget is a target and max_tokens the hard ceiling, so a budget that leaves no room for the answer truncates the answer")
    if not cor.get("tool_choice_compatibility_handled"): f.append("TH-2 tool-choice compatibility is not handled (manual extended thinking accepts only tool_choice auto or none; forced tool use belongs to adaptive mode, and where it is accepted the response starts with the tool call and carries no thinking block) - forcing a tool in manual mode errors, and expecting reasoning before a forced call misreads the response")
    if not cor.get("sampling_and_prefill_constraints_respected"): f.append("TH-2 sampling and prefill constraints on thinking models are not respected (non-default temperature/top_p/top_k rejected on current models, assistant prefill rejected on 4.6+ models) - a request template carried over from a non-thinking workload fails wholesale once thinking is on")
    pre=d.get("preservation") or {}
    if not pre.get("thinking_blocks_preserved_unmodified"): f.append("TH-3 thinking blocks are not passed back complete and unmodified within tool-use turns (including redacted_thinking blocks; the signature is opaque and never parsed or edited) - dropping or editing a block breaks reasoning continuity and, on preserved-thinking models, can fail the request outright")
    if not pre.get("display_chosen_deliberately"): f.append("TH-3 the display setting is not chosen deliberately (summarized versus omitted versus updates) - omitted returns empty thinking fields at identical billing, so it buys latency and never cost, and no setting returns raw chain of thought, so reasoning must be read from thinking blocks rather than elicited into the answer text")
    if not pre.get("streaming_reassembly_handled"): f.append("TH-3 streaming thinking is not handled (thinking_delta events then a single signature_delta per block, reassembled with the SDK final-message helper rather than hand-concatenated deltas) - a hand-rolled accumulator loses signatures and with them the ability to continue the turn")
    ver=d.get("verification") or {}
    if not ver.get("thinking_tokens_measured"): f.append("TH-4 thinking tokens are not measured (usage.output_tokens_details.thinking_tokens, visible only on the final message_delta when streaming) - thinking is billed as output tokens even when its text is omitted or summarized, so an unmeasured workload cannot price reasoning or notice that billed tokens and visible summary tokens differ")
    if not ver.get("depth_tuned_on_own_tasks"): f.append("TH-4 depth is not tuned on the team's own tasks (start near the 1024 minimum for simple work and at 16k or more for complex work, expect diminishing returns, route budgets above 32k through batch processing) - an untuned budget pays latency and timeout risk for reasoning the task never needed, or starves the tasks that did")
    if not ver.get("thinking_presence_and_quality_checked"): f.append("TH-4 the presence and quality of thinking are not checked (a mid-turn toggle silently disables thinking, so only returned thinking blocks prove it ran; eliciting reasoning into the answer text can be refused as reasoning extraction) - a pipeline can lose its reasoning layer without any error and report the loss as success")
    ops=d.get("operations") or {}
    if not ops.get("config_held_stable_for_cache"): f.append("TH-5 the thinking configuration is not held stable inside cached conversations (switching mode, changing budget_tokens, or changing top-level effort renders into the prompt and invalidates cache breakpoints) - per-request depth changes repay the cache write premium on every change; per-message effort is the cache-preserving route where the model supports it")
    if not ops.get("context_window_accounted_for_thinking"): f.append("TH-5 the context cost of thinking is not accounted per model (current-turn thinking counts toward max_tokens and the window; on keep-all models prior thinking stays in context as billed input, on last-turn-only models it is stripped automatically, with thinking-block clearing as the reclaim lever) - long agentic sessions on keep-all models accumulate reasoning as silent context growth")
    if not ops.get("migration_and_model_switch_recorded"): f.append("TH-5 the migration and model-switch behaviour is not recorded (enabled to adaptive removes budget_tokens and moves depth to effort, adaptive interleaves automatically and may skip thinking at low effort; when switching models, blocks are passed back unstripped and the API drops only what the target cannot read) - a model upgrade silently changes whether, how much, and how continuably the system thinks")
    return f
if __name__=="__main__":
    data=json.load(open(sys.argv[1])); fails=check(data)
    if fails:
        print(f"FAIL ({len(fails)}):")
        [print(" -",x) for x in fails]; sys.exit(1)
    print("PASS")
