#!/usr/bin/env python3
"""advisor-check: deterministic gate for the Advisor surface
(how a faster, lower-cost executor model consults a higher-intelligence
advisor model mid-generation - valid executor/advisor pairing, when the
consult happens, how its result blocks round-trip through history and
paused turns, and how its separate sub-inference cost is capped and
read - is decided, not left to habit).
Stdlib only, offline.
Canonical source (read in full 2026-11-19):
- Anthropic Claude Platform Docs "Advisor tool"
  https://platform.claude.com/docs/en/agents-and-tools/tool-use/advisor-tool
  (457 lines read in full): a faster, lower-cost executor consults a
  higher-intelligence advisor mid-generation; the advisor reads the full
  transcript (system prompt, tool definitions, prior turns and tool
  results, and the executor's text so far) under its own Anthropic
  system prompt, runs without tools and without context management, its
  thinking blocks are dropped, and only the advice text reaches the
  executor - all inside a single /v1/messages request. Fit: long-horizon
  agentic work (coding agents, computer use, multistep research) where
  most turns are mechanical but an excellent plan is crucial; close to
  advisor-solo quality with bulk generation at executor rates, and the
  benefit shrinks as executor capability approaches the advisor's. Weak
  fit: single-turn Q&A, pure pass-through model pickers, workloads where
  every turn needs the advisor's full capability. Definition:
  type "advisor_20260301", name "advisor", model required (billed at
  the advisor model's rates), beta header advisor-tool-2026-03-01.
  The advisor must be Sonnet 4.6 or more capable and at least as capable
  as the executor (equal-capability models may advise each other); an
  invalid pair returns 400 invalid_request_error. Result variants:
  advisor_result (plaintext, e.g. Opus 4.8) and advisor_redacted_result
  (encrypted_content, e.g. newest Opus - the executor reads it
  server-side, the client cannot); both carry stop_reason only when
  max_tokens is set on the tool. Round-trip result blocks verbatim;
  switching advisor models mid-conversation means branching on
  content.type. Dropping the tool or changing model / max_uses /
  max_tokens / caching is an edit to tools: it invalidates thinking
  blocks in history (prefix check can 400; fix is
  thinking.block_binding.prefix_mismatch_behavior "drop_block" on that
  and every later request, beta thinking-binding-controls-2026-08-01);
  dropping the tool is allowed only with no call pending and the beta
  header still sent. pause_turn: a pending advisor call ends the
  response with stop_reason "pause_turn" and a server_tool_use block
  with no result; resume by resending the assistant message unchanged
  with the same tool and header - omitting the tool is a 400; if the
  executor also called a client tool, the response ends "tool_use" and
  the pending call runs at the start of the next request. Timing: an
  early first call after a few exploratory reads, and for difficult
  tasks a final call after writes and test outputs; call the advisor
  before planner-like tools. Nudge: a turn-2 reminder raised Haiku 4.5
  pass rates about 7 points in Anthropic's internal eval, had no
  measurable effect on Sonnet, and slightly lowered Opus - never nudge
  Opus; measure the baseline first-call turn first (a turn-2 nudge when
  baseline first call was turn 7+ correlated with a 3-4 point drop);
  74 percent (Sonnet) to 98 percent (Haiku 4.5) of nudged attempts call
  immediately; skip the nudge when the system prompt already carries
  restraint language. Forcing via tool_choice {"type":"tool","name":
  "advisor"} cannot combine with manual enabled thinking (400);
  Fable / Mythos / Opus 5.5 / Sonnet 5.5 executors reject tool_choice
  types tool and any - use the nudge there. Cost: advisor calls are a
  separate sub-inference; top-level usage is executor-only, advisor
  tokens live in usage.iterations[] as type "advisor_message" at advisor
  rates (summed executor input_tokens exceeds any single prompt because
  later iterations re-send the conversation); token counting returns the
  executor's first iteration only. Typical advisor output is 400-700
  text tokens (1,400-1,800 with thinking). Top-level max_tokens and any
  task budget bound the executor only. Tool max_tokens (minimum 1024)
  is the hard cap: 2048 is the recommended start (about 7x less mean
  output, near-zero truncation, no detectable quality loss in testing);
  1024 cuts about 10x but truncates about 10 percent of calls; a hit
  appends "[Advisor output truncated at max_tokens=...]" and sets
  stop_reason "max_tokens" on the result. max_uses caps calls per turn
  and a turn spans requests (pause_turn resumes and tool_result-only
  continuations count earlier calls); past the cap, calls return
  advisor_tool_result_error max_uses_exceeded and the executor
  continues - the request itself never fails on an advisor error.
  Error codes: max_uses_exceeded, too_many_requests (advisor limits
  share the advisor model's direct-call bucket; an executor rate limit
  instead fails the whole request with HTTP 429), overloaded,
  prompt_too_long, execution_time_exceeded, model_not_found,
  unavailable. Conversation budgets are client-side: count calls, and
  at the cap remove the tool (history blocks stay). Advisor-side
  caching ({"type":"ephemeral","ttl":"5m"|"1h"}) breaks even at roughly
  three calls per conversation - enable only at 3+, set once and never
  toggle mid-conversation. Streaming: the advisor does not stream; the
  executor stream pauses (pings about every 30s) and the result arrives
  fully formed in one content_block_start with no deltas, then a
  message_delta carries updated usage.iterations. Composition: batches
  supported (iterations per item); context editing clear_tool_uses is
  not fully compatible with advisor blocks; Priority Tier applies per
  model independently. Managed Agents: advisor is configured as
  "advisor": {"type":"enabled","model":...} in the agent's multiagent
  block - no max_uses / max_tokens / caching options, advice arrives as
  thread events, not advisor_tool_result blocks. Beta on the Claude API,
  Claude Platform on AWS, and Claude Models on Google Cloud (managed).
Exit 0=PASS, 1=FAIL.
"""
import json, sys
def check(d):
    f=[]
    dec=d.get("decision") or {}
    if not dec.get("decision_recorded"): f.append("AD-0 the Advisor surface is not recorded as a decided surface - which executor consults which stronger model mid-generation, and when, is left to each run and habit, not a decision")
    if not dec.get("owner_recorded"): f.append("AD-0 no owner is recorded for advisor correctness (pairing, call timing, cost of the sub-inference) - an executor that never asks, or asks on every turn at advisor rates, has no accountable reader")
    if not dec.get("pairs_inventoried"): f.append("AD-0 there is no inventory of executor/advisor pairs in use (which workloads run a cheap executor with a stronger advisor available, and which run a single model throughout) - the surface cannot be required where its own deployment is uncounted")
    en=d.get("enablement") or {}
    if not en.get("valid_pair_checked"): f.append("AD-1 the executor/advisor pair is not checked against the compatibility rule (the advisor must be Claude Sonnet 4.6 or more capable and at least as capable as the executor; equal-capability models may advise each other; an invalid pair returns 400 invalid_request_error naming the combination) - a request is built on a pair the API refuses")
    if not en.get("tool_definition_fixed"): f.append("AD-1 the tool definition shape is not fixed (type advisor_20260301, name advisor, model required and billed at the advisor model's rates, beta header advisor-tool-2026-03-01 sent - including on later requests that only carry advisor_tool_result blocks in history) - the consult is wired in a shape the API does not recognise")
    if not en.get("fit_decided"): f.append("AD-1 the fit is not decided (long-horizon agentic work where most turns are mechanical but the plan is crucial, with the benefit shrinking as executor capability approaches the advisor's; a weaker fit for single-turn Q&A, pass-through model pickers, and workloads where every turn genuinely needs the advisor's full capability - evaluated on this workload, not the headline) - advisor cost is paid where it buys nothing, or withheld where a plan was the whole bottleneck")
    ti=d.get("timing") or {}
    if not ti.get("call_timing_prompted"): f.append("AD-2 call timing is not prompted (an early first call after a few exploratory reads are in the transcript, a final call on difficult tasks after file writes and test outputs, and the advisor called before planner-like tools so its plan funnels into them; without steering, executors under-call, particularly on coding tasks) - the consult lands after the approach is already committed, or never")
    if not ti.get("nudge_calibrated"): f.append("AD-2 the under-calling nudge is not calibrated (a turn-2 reminder raised Haiku 4.5 pass rates about 7 points, had no measurable effect on Sonnet, and slightly lowered Opus - never nudge Opus; measure the baseline first-call turn before adding it, because a turn-2 nudge when the baseline first call was turn 7 or later correlated with a 3-4 point drop, and 74 to 98 percent of nudged attempts call immediately; skip it entirely when the system prompt already carries restraint language) - a generic reminder pushes trivial tasks into a consult and displaces better-timed later calls")
    if not ti.get("forcing_rules_known"): f.append("AD-2 the forcing rules are not known (tool_choice {type: tool, name: advisor} forces a consult but cannot combine with manual enabled thinking - the API returns 400; adaptive thinking supports it; Fable, Mythos, Opus 5.5 and Sonnet 5.5 executors reject tool_choice types tool and any, so the nudge is the only lever there) - a forced consult is configured in a combination the API refuses")
    ct=d.get("continuation") or {}
    if not ct.get("history_roundtripped"): f.append("AD-3 advisor result blocks are not round-tripped verbatim (the full assistant content including advisor_tool_result blocks goes back unchanged; the executor's prompt always contains the plaintext advice, but the client may hold either advisor_result text or advisor_redacted_result encrypted_content, and switching advisor models mid-conversation means branching on content.type) - rewriting or dropping a block loses the advice or breaks the request")
    if not ct.get("tool_edits_handled"): f.append("AD-3 tool edits are not handled (dropping the advisor tool, or changing its model, max_uses, max_tokens or caching, is an edit to tools that invalidates thinking blocks already in history - the prefix check can return 400; the fix is thinking.block_binding.prefix_mismatch_behavior drop_block on that request and every later one, with the thinking-binding-controls-2026-08-01 beta header; dropping the tool itself is allowed only when no call is pending and the advisor beta header is still sent) - a routine budget cap or model swap takes down the conversation it was meant to cheapen")
    if not ct.get("paused_turn_resumed"): f.append("AD-3 a paused turn is not resumed correctly (a pending advisor call ends the response with stop_reason pause_turn and a server_tool_use block with no result; resume by resending that assistant message unchanged with the same advisor tool and beta header and no added user message or tool_result - omitting the tool returns 400; if the executor also called a client tool, the response ends tool_use and the pending advisor call runs at the start of the next request after the tool_result blocks) - a dangling consult is abandoned, duplicated, or answered with a block the API rejects")
    co=d.get("cost") or {}
    if not co.get("usage_read_from_iterations"): f.append("AD-4 advisor cost is not read from usage.iterations (top-level usage is executor-only; advisor tokens appear as iterations of type advisor_message billed at the advisor model's rates, and summed executor input_tokens exceeds any single prompt because later iterations re-send the conversation; token counting returns only the executor's first iteration) - the sub-inference is invisible in the totals and the surface is judged free, or executor spend is misread as advisor spend")
    if not co.get("output_capped"): f.append("AD-4 advisor output is not capped on the tool definition (the top-level max_tokens and any task budget bound the executor only; the tool's max_tokens - minimum 1024 - is the hard ceiling, the server also tells the advisor its remaining budget, 2048 is the tested starting point at roughly 7x less mean output with near-zero truncation while 1024 truncates about 10 percent of calls, and a hit is detectable via stop_reason max_tokens on the result and the appended truncation marker) - the largest cost driver of the surface runs unbounded at advisor rates")
    if not co.get("call_budgets_set"): f.append("AD-4 call budgets are not set (max_uses caps advisor calls per turn and a turn spans requests - pause_turn resumes and tool_result-only continuations count earlier calls against the same cap, past which calls return max_uses_exceeded and the executor continues; conversation-level budgets are counted client-side and enforced by removing the tool; advisor-side caching breaks even at roughly three calls per conversation, is enabled only at 3+, and is set once and never toggled mid-conversation) - a long loop consults without limit, or caching is paid for on conversations too short to recoup the write")
    cs=d.get("constraints") or {}
    if not cs.get("errors_read"): f.append("AD-5 advisor errors are not read correctly (an advisor failure never fails the request - the executor receives advisor_tool_result_error and continues; codes are max_uses_exceeded, too_many_requests, overloaded, prompt_too_long, execution_time_exceeded, model_not_found and unavailable; advisor rate limits draw from the same per-model bucket as direct advisor calls, while an executor rate limit fails the whole request with HTTP 429) - a rate-limited or over-cap consult is debugged as a model failure, or retried as if the request had failed")
    if not cs.get("streaming_and_composition_known"): f.append("AD-5 the streaming and composition facts are not known (the advisor sub-inference does not stream - the executor stream pauses with pings about every 30 seconds and the result arrives fully formed in a single content_block_start with no deltas, followed by a message_delta carrying updated usage.iterations; batches are supported with iterations per item; context editing clear_tool_uses is not fully compatible with advisor blocks; Priority Tier applies to each model independently) - a normal advisor pause is misread as a hung stream, or the blocks are combined with a feature that mangles them")
    if not cs.get("platform_variants_known"): f.append("AD-5 the platform variants are not known (beta on the Claude API, Claude Platform on AWS and Claude Models on Google Cloud managed; on Claude Managed Agents the advisor is not a tool definition at all but advisor {type: enabled, model} in the agent's multiagent block, taking no max_uses, max_tokens or caching options, with advice delivered as thread events rather than advisor_tool_result blocks) - the Messages API shape is configured on a surface that takes a different one, and its limits are assumed where they do not exist")
    return f
if __name__=="__main__":
    data=json.load(open(sys.argv[1])); fails=check(data)
    if fails:
        print(f"FAIL ({len(fails)}):")
        [print(" -",x) for x in fails]; sys.exit(1)
    print("PASS"); sys.exit(0)
