#!/usr/bin/env python3
"""tool-choice-check: deterministic gate for the TOOL CHOICE surface
(how strongly each request compels or forbids tool calls - auto / any /
tool / none, forced-use support per model, the thinking trade-off of
forcing, parallel execution and result formatting, and the system-prompt
token add-on that differs by choice type - is decided per surface, not
left to defaults nobody chose).
Stdlib only, offline.
Canonical sources (read in full 2026-11-19):
- Anthropic Claude Platform Docs "Tool use with Claude" (overview)
  https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview
  and "Define tools" #forcing-tool-use
  https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools
  : with default tool_choice {"type": "auto"} Claude decides each turn
  whether to call a tool or answer directly (calls when the request maps
  to a described capability and the answer is not already in context;
  answers directly for stable knowledge, creative and conversational
  turns). The boundary is steerable by system prompt, from light ("Use
  the tools to investigate before responding") to strong ("Always call
  a tool first"). Four options: auto (default when tools are provided),
  any (must use one of the provided tools), tool (must use that tool),
  none (no tools; default when no tools are provided). With any/tool
  the response starts with a tool call: no natural-language preamble,
  and forcing SKIPS thinking on every model that accepts it (response
  starts with tool_use, no thinking block); to think before calling,
  use auto plus a prompt instruction. Forced use is NOT universally
  supported: manual extended thinking (thinking {type: "enabled"})
  rejects any/tool with an error (adaptive thinking does not block it,
  but a forced call still skips thinking); Claude Fable 5.2, Mythos
  5.2, Opus 5.5, Sonnet 5.5, Fable 5.1 and Mythos 5.1 return 400 for
  any/tool - use auto with strict tool use for schema-valid inputs, or
  structured outputs for a fixed JSON shape; none is supported.
  Pricing: a special tool-use system prompt is added per request -
  current-generation models add 286 tokens for auto/none and 406 for
  any/tool (older generations differ: e.g. Opus 4.7 675/804, 4.6
  497/589, 4.1 313/315), on top of the tools parameter, tool_use and
  tool_result block tokens; no tools + none adds 0.
- Anthropic Claude Platform Docs "Parallel tool use"
  https://platform.claude.com/docs/en/agents-and-tools/tool-use/parallel-tool-use
  : by default Claude may call several tools in one response
  (stop_reason tool_use, several tool_use blocks). Execution order is
  the application's choice: concurrent for independent read-only calls,
  sequential for side effects / shared state / ordering; computer use
  and browser use batches MUST run sequentially, stopping at first
  failure. Return ONE tool_result per tool_use block, ALL together in
  the single next user message, matched by tool_use_id, before any
  text; a call not run still gets a tool_result with is_error: true.
  Splitting results into separate user messages is the most common
  failure - it teaches Claude to avoid parallel calls. Disable with
  disable_parallel_tool_use: true INSIDE the tool_choice object (not
  top-level): with auto it means at most one call (plain-text answers
  still allowed); with any/tool it means exactly one call. Guard
  against dependent calls batched together ("Only batch tool calls
  that are independent of each other"); a parallel call that fails for
  a missing prerequisite returns is_error and Claude reissues it.
Separation: this surface is NOT tool DESIGN (gated 2026-11-18,
tool-use-check: which tools exist and how they are described) - here
only the per-request compulsion dial and parallel semantics are gated.
Exit 0=PASS, 1=FAIL.
"""
import json, sys
def check(d):
    f=[]
    dec=d.get("decision") or {}
    if not dec.get("decision_recorded"): f.append("TC-0 the tool choice surface is not recorded as a decided surface - how strongly each request compels or forbids tool calls is left to an unchosen default at every call site")
    if not dec.get("owner_recorded"): f.append("TC-0 no owner is recorded for the tool choice surface (which surfaces may force, forbid or parallelize calls) - a wrongly forced or wrongly forbidden call has no accountable reader")
    if not dec.get("canonical_source_recorded"): f.append("TC-0 the canonical source is not recorded (Anthropic tool_choice: auto/any/tool/none, forcing support varies by model and thinking mode, forcing skips thinking, parallel results return together in one user message) - every surface invents its own compulsion rules")
    modes=d.get("modes") or {}
    if not modes.get("choice_decided_per_surface"): f.append("TC-1 the tool_choice mode is not decided per surface (auto where judgment is wanted, any/tool where a call is mandatory, none where tools must not fire) - one global habit serves surfaces with opposite needs")
    if not modes.get("defaults_understood"): f.append("TC-1 the defaults are not recorded (auto when tools are provided, none when no tools are provided, and no tools + none adds 0 system-prompt tokens) - a surface that never sets tool_choice does not know which mode it is actually running")
    if not modes.get("prompt_steering_used_before_forcing"): f.append("TC-1 prompt steering is not used as the first dial (light to strong system-prompt instructions move the auto boundary while preserving thinking and preamble) - surfaces jump straight to forcing and pay its costs for behavior a sentence would have produced")
    force=d.get("forcing") or {}
    if not force.get("support_checked_per_model_and_thinking"): f.append("TC-2 forced use (any/tool) is not checked for support per model and thinking mode before use (manual extended thinking rejects it with an error; Fable 5.2 / Mythos 5.2 / Opus 5.5 / Sonnet 5.5 / Fable 5.1 / Mythos 5.1 return 400) - a model swap turns a working forced call into a hard failure")
    if not force.get("thinking_and_preamble_tradeoff_accepted"): f.append("TC-2 the forcing trade-off is not explicitly accepted where forcing is used (the response starts with the tool call: no thinking block, no natural-language preamble, even if asked) - surfaces that need reasoning before the call, or an explanation alongside it, silently lose both")
    if not force.get("unsupported_fallback_defined"): f.append("TC-2 no fallback is defined for models/settings where forcing is unsupported (auto + strict tool use for schema-valid inputs, or structured outputs for a fixed JSON shape; none remains supported) - the first unsupported model leaves the surface with an error and no designed alternative")
    par=d.get("parallel") or {}
    if not par.get("execution_strategy_decided"): f.append("TC-3 the execution strategy for parallel calls is not decided per tool class (concurrent for independent read-only calls; sequential for side effects, shared state or ordering; computer/browser batches sequential, stopping at first failure) - parallel-by-accident runs dependent mutations at the same time")
    if not par.get("all_results_single_user_message"): f.append("TC-3 tool results are not all returned together in the single next user message (one tool_result per tool_use block, matched by tool_use_id, before any text; a call not run still returns is_error: true) - split or missing results are the most common way parallelism breaks")
    if not par.get("disable_flag_used_correctly"): f.append("TC-3 disable_parallel_tool_use is not set correctly where single-call behavior is required (inside the tool_choice object, never top-level; with auto it caps at one call while plain-text answers remain possible, with any/tool it means exactly one call) - a misplaced flag is silently ignored and the surface believes it is serial while it is not")
    meas=d.get("measurement") or {}
    if not meas.get("choice_effect_measured"): f.append("TC-4 the effect of the chosen mode is not measured (whether calls happen when expected, whether parallel calls actually occur, error rate by mode) - 'we set any' is asserted while behavior is indistinguishable from auto")
    if not meas.get("history_formatting_preserves_parallelism"): f.append("TC-4 conversation-history formatting is not audited for the parallelism trap (a separate user message per tool result in history teaches Claude to avoid parallel calls) - the surface un-trains the behavior it depends on, one transcript at a time")
    if not meas.get("dependent_calls_guarded"): f.append("TC-4 dependent calls appearing in one batch are not guarded (prompt rule to batch only independent calls, sequential stop-on-failure, or is_error + reissue for a missing prerequisite) - a batch that assumes an order the API never promised fails intermittently and looks like model flakiness")
    cost=d.get("cost") or {}
    if not cost.get("system_prompt_addon_counted"): f.append("TC-5 the tool-use system-prompt add-on is not counted (current generation: 286 tokens for auto/none, 406 for any/tool, per request, on top of tools/tool_use/tool_result tokens) - every tooled request is underpriced by a fixed tax nobody booked")
    if not cost.get("choice_type_cost_difference_counted"): f.append("TC-5 the cost difference between choice types is not counted (forcing costs more system-prompt tokens than auto on every generation in the table) - the compulsion dial is also a price dial, and surfaces turn it without seeing the price")
    if not cost.get("reverified_on_model_change"): f.append("TC-5 add-on tokens and forcing support are not re-verified when the model changes (the add-on differs by generation - 286/406 current, 675/804 on Opus 4.7, 313/315 on 4.1 - and any/tool support itself changes) - a model swap silently changes both what the surface costs and whether it runs at all")
    return f
if __name__=="__main__":
    data=json.load(open(sys.argv[1])); fails=check(data)
    if fails:
        print(f"FAIL ({len(fails)}):")
        [print(" -",x) for x in fails]; sys.exit(1)
    print("PASS"); sys.exit(0)
