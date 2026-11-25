#!/usr/bin/env python3
"""context-editing-check: deterministic gate for the Context Editing surface
(how stale tool results and old thinking blocks are selectively cleared
server-side as a conversation grows - trigger, keep, cache cost, preserved
state - is decided, not left to whatever each request happens to include).
Stdlib only, offline.
Canonical source (read in full 2026-11-19):
- Anthropic Claude Platform Docs "Context editing"
  https://platform.claude.com/docs/en/build-with-claude/context-editing
  (314 lines read in full): context is a finite resource with diminishing
  returns; irrelevant content degrades focus, so editing is active curation,
  not only cost control. Two server-side strategies, independently
  configurable, applied before the prompt reaches Claude:
  clear_tool_uses_20250919 clears the oldest tool results chronologically
  past a trigger, replacing each with placeholder text (defaults: trigger
  100,000 input tokens - trigger may be input_tokens or tool_uses; keep 3
  tool use/result pairs; clear_at_least unset; exclude_tools unset;
  clear_tool_inputs false, so only results clear and the calls stay
  visible). clear_thinking_20251015 manages thinking blocks of earlier
  turns: keep defaults to {thinking_turns, 1} when the strategy is present
  (on EVERY model, including models whose no-strategy default keeps all);
  keep counts the turn in progress plus turns without thinking blocks, a
  tool_result-only user message continues the turn in progress, any other
  user message starts a new turn, so keep=1 at a new-turn boundary clears
  every earlier turn's thinking; "all" keeps everything. Cache interaction
  differs by strategy: tool-result clearing invalidates cached prefixes, so
  clear_at_least exists to clear enough to make the invalidation worthwhile
  (cache write costs are paid, then the new prefix is reused); kept thinking
  preserves the cache, cleared thinking invalidates it at the clearing
  point. Editing is server-side only: the client keeps the full unmodified
  history and never syncs to the edited version; on preserved-thinking
  models server-side management never invalidates thinking blocks, while
  client-side edits to earlier turns can invalidate thinking in every later
  turn. Applied edits are observable in the response context_management
  field (and in the final message_delta when streaming), and the token
  counting endpoint previews the effect (input_tokens after editing vs
  original_input_tokens before). Combined with the memory tool, Claude gets
  an automatic warning as the threshold approaches so it can write
  essentials to memory files before results are cleared - the cleared
  content stays reachable on demand instead of occupying the window.
  Client-side SDK compaction is a different mechanism (TypeScript / Ruby
  SDK tool_runner, compaction_control): the SDK totals
  input + cache_creation + cache_read + output tokens against a threshold
  (default 100,000), injects a summary request as a user turn, replaces the
  whole history with the <summary>-wrapped structured summary (task
  overview, current state, discoveries, next steps, context to preserve)
  and continues; with heavy server-side tools the SDK total miscounts
  because cache_read_input_tokens accumulates across the server tool's
  internal calls, so compaction can fire early (workarounds: token counting
  endpoint, avoid compaction on server-tool-heavy work); a compaction that
  fires while a tool use is pending drops that tool block and Claude
  reissues the call if still needed. Fit: good for long-running agent work
  over many files / sources, research accumulation, multi-step tasks with
  measurable progress and artifacts persisted outside the conversation;
  less ideal for precise recall of early details, server-tool-heavy
  workflows, and exact state across many variables. Availability: Beta on
  the Messages API, a beta header is required, all models supported.
Exit 0=PASS, 1=FAIL.
"""
import json, sys
def check(d):
    f=[]
    dec=d.get("decision") or {}
    if not dec.get("decision_recorded"): f.append("CE-0 the Context Editing surface is not recorded as a decided surface - whether old tool results and thinking blocks are cleared server-side, summarized client-side, or left to grow until the window fills, is left to each call site and habit, not a decision")
    if not dec.get("owner_recorded"): f.append("CE-0 no owner is recorded for context editing correctness (triggers, keep counts, cache cost, lost-context incidents) - a turn that silently lost the one tool result it still needed has no accountable reader")
    if not dec.get("surfaces_inventoried"): f.append("CE-0 there is no inventory of the context-management surfaces (which conversations use server-side clearing, which use client-side compaction, which use neither) - the cache and recall consequences cannot be required where the surfaces are indistinguishable")
    tc=d.get("tool_clearing") or {}
    if not tc.get("strategy_decided"): f.append("CE-1 tool result clearing is not decided (clear_tool_uses_20250919 clears the oldest tool results first once the trigger is passed and replaces each with placeholder text; only results clear by default) - long tool-heavy sessions carry every stale file dump and search result to the window limit, degrading focus long before they fail")
    if not tc.get("trigger_and_keep_decided"): f.append("CE-1 the trigger and keep are not decided (trigger defaults to 100,000 input tokens and may instead count tool_uses; keep defaults to the 3 most recent tool use/result pairs, oldest removed first) - clearing fires at an inherited default nobody chose for this workload's result sizes, or keeps so little that the current task's working set is cleared mid-flight")
    if not tc.get("clear_at_least_and_cache_decided"): f.append("CE-1 the cache cost of clearing is not decided (tool result clearing invalidates cached prompt prefixes and pays cache write costs on the new prefix; clear_at_least guarantees a minimum cleared amount so the invalidation is worthwhile, and if that amount cannot be cleared the strategy is not applied) - small frequent clears repeatedly break the cache for savings smaller than the rewrite they cause")
    th=d.get("thinking_clearing") or {}
    if not th.get("strategy_decided"): f.append("CE-2 thinking block clearing is not decided (clear_thinking_20251015 controls how many earlier turns keep their thinking blocks - more kept preserves reasoning continuity, more cleared frees window space) - thinking accumulates as an unmanaged tax on every long reasoning session, or continuity is lost by an edit nobody configured")
    if not th.get("keep_semantics_understood"): f.append("CE-2 the keep semantics are not understood (with the strategy present, keep defaults to the last 1 thinking turn on every model - including models whose per-model default without the strategy keeps all; keep counts the turn in progress and turns without thinking blocks, a tool_result-only user message continues the current turn while any other user message starts a new one, so keep=1 at a new-turn boundary clears all earlier thinking) - adding the strategy to 'just configure it later' silently switches a keep-all model to keep-1")
    if not th.get("cache_tradeoff_decided"): f.append("CE-2 the thinking cache tradeoff is not decided (thinking blocks that are kept preserve the prompt cache and its input-token savings; cleared thinking invalidates the cache at the clearing point) - a keep value is chosen for window space alone and the cache bill it creates is attributed to the model instead of the edit")
    sf=d.get("safety") or {}
    if not sf.get("exclusions_decided"): f.append("CE-3 exclusions are not decided (exclude_tools names tools whose uses and results are never cleared; clear_tool_inputs defaults to false so the tool calls themselves stay visible when only results clear) - a result that must survive (an approval record, a baseline measurement) is cleared by the same rule as disposable search dumps, or call parameters vanish that the model still needs to interpret what it did")
    if not sf.get("memory_pairing_decided"): f.append("CE-3 the memory-tool pairing is not decided (with the memory tool enabled, Claude is warned automatically as the clearing threshold approaches and can write essential results and context to persistent memory files before they are cleared, then read them back on demand) - clearing deletes the only copy of intermediate findings, and the long workflow restarts its research instead of looking it up")
    if not sf.get("server_side_state_understood"): f.append("CE-3 the server-side state shape is not understood (editing is applied before the prompt reaches Claude; the client keeps the full unmodified history and does not sync to the edited version; on preserved-thinking models server-side management never invalidates thinking blocks, whereas client-side edits to earlier turns can invalidate the thinking of every later assistant turn) - a client 'helpfully' rewrites history to match what it thinks the server did and breaks every later turn's thinking, or a cleared result is hunted for in a local history that was never edited")
    ob=d.get("observability") or {}
    if not ob.get("response_read"): f.append("CE-4 applied edits are not read from the response (the context_management field reports which strategies fired and the content / input-token statistics cleared; in streaming the edits arrive in the final message_delta event) - clearing is assumed from configuration alone, and a strategy that never fired, or fired far earlier than intended, is discovered from a quality complaint instead of the response")
    if not ob.get("token_count_preview_decided"): f.append("CE-4 the token counting preview is not used (the token counting endpoint accepts context management and returns input_tokens after editing alongside original_input_tokens before any clearing) - trigger and keep values are tuned blind against live traffic instead of previewed against real conversation shapes")
    if not ob.get("client_compaction_boundary_decided"): f.append("CE-4 the client-side compaction boundary is not decided (SDK compaction in the TypeScript / Ruby tool_runner is summary replacement, not clearing: it totals input + cache-creation + cache-read + output tokens against its threshold (default 100,000), injects a summary request, and swaps the whole history for the structured summary; its total miscounts on server-tool-heavy work because cache_read accumulates across the server tool's internal calls, and a compaction fired while a tool use is pending drops that block for reissue) - the two mechanisms are conflated, compaction fires early on exactly the search-heavy surfaces that can least afford a summary swap, or a dropped pending call is read as a completed step")
    ft=d.get("fit") or {}
    if not ft.get("fit_decided"): f.append("CE-5 the fit is not decided per workload (clearing / compaction fit long-running agent work over many files and sources, research accumulation, and multi-step tasks whose artifacts persist outside the conversation; they fit poorly where precise recall of early details, heavy server-side tool use, or exact state across many variables is the work) - a recall-critical surface is put on aggressive clearing because a file-processing surface benefited from it")
    if not ft.get("beta_status_recorded"): f.append("CE-5 the availability shape is not recorded (context editing is Beta on the Messages API, requires the beta header, and is supported on all models) - a surface is designed as if the feature were GA, or a missing beta header is debugged as a model failure")
    if not ft.get("threshold_tuning_loop"): f.append("CE-5 there is no tuning loop (triggers, keep counts and clear_at_least are revisited from the context_management statistics and task outcomes as workloads change) - the first values chosen become permanent by neglect while the conversations they govern change shape")
    return f
if __name__=="__main__":
    data=json.load(open(sys.argv[1])); fails=check(data)
    if fails:
        print(f"FAIL ({len(fails)}):")
        [print(" -",x) for x in fails]; sys.exit(1)
    print("PASS"); sys.exit(0)
