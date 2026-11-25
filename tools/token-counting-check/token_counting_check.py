#!/usr/bin/env python3
"""token-counting-check: deterministic gate for the TOKEN COUNTING surface
(counting input tokens before sending - method, coverage, preflight use,
accuracy, operations - is decided, not estimated from characters).
Stdlib only, offline.
Canonical source (read in full 2026-11-19):
- Anthropic Claude Platform Docs "Token counting"
  https://platform.claude.com/docs/en/build-with-claude/token-counting
  (101 lines read in full): the count_tokens endpoint accepts the same
  structured inputs as message creation (system, tools, images, PDFs)
  and returns total input tokens only. It returns invalid_request_error
  for server tools (every server tool except the advisor tool), the MCP
  connector, and image/document blocks with a url or file source; send
  images and PDFs as base64 to count them, and for server-tool / MCP
  requests read tokens from the Messages API response usage object. All
  active models support counting. An oversized_image:error block is
  rejected at count time exactly as creation would reject it. Fable 5.2/
  5.1/5, Mythos 5.2/5.1/5 and Opus 4.7 share a newer tokenizer counting
  roughly 30 percent higher than pre-4.7 models; the endpoint counts
  under the tokenizer of the model passed, so measure a migration by
  counting the same request under both models. Counting is free, rate
  limited per usage tier (Start 5,000 / Build 10,000 / Scale 20,000 RPM).
  Stated uses: proactively manage rate limits and costs, make smart
  model routing decisions, optimize prompts to a specific length, keep
  prompts within the context window, check counts before sending to stay
  within the usage tier, and cache repeated prefixes.
Secondary (flagged, not in the official page as fetched): the count is
an estimate and actual input tokens may differ by a small amount, so
hold headroom below hard limits; output cannot be counted before it
exists - max_tokens is its ceiling, so the window check is
input + max_tokens <= window; billed prompt length is
input_tokens + cache_creation_input_tokens + cache_read_input_tokens,
never input_tokens alone, and long-context tier thresholds count cache
tokens too; tiktoken and characters-per-token rules are other
tokenizers' arithmetic and undercount Claude, steeply on code and
non-English text.
Exit 0=PASS, 1=FAIL.
"""
import json, sys
def check(d):
    f=[]
    dec=d.get("decision") or {}
    if not dec.get("decision_recorded"): f.append("TC-0 the token-counting surface is not recorded as a decided surface - prompt size before sending is left to character estimates and habit, not a decision")
    if not dec.get("owner_recorded"): f.append("TC-0 no owner is recorded for counting correctness (method, coverage, headroom, reconciliation) - a workload that overflows its window or silently crosses a pricing tier has no accountable reader")
    if not dec.get("counting_surfaces_inventoried"): f.append("TC-0 there is no inventory of the surfaces that need preflight counting (large prompts, RAG assembly, tool-heavy agents, migrations) - counting cannot be required where the surfaces are indistinguishable")
    m=d.get("method") or {}
    if not m.get("official_endpoint_used_per_target_model"): f.append("TC-1 counting does not use the provider's own count endpoint under the target model's tokenizer - the same text counts roughly 30 percent higher on the Opus 4.7 / Fable / Mythos tokenizer generation, so a count taken under another model or another provider's tokenizer is a different number wearing the same label")
    if not m.get("assembled_request_counted_not_pieces"): f.append("TC-1 the assembled request is not what gets counted (system, messages, tool definitions, tool results and media together) - counting pieces and adding them misses the formatting and boundary tokens the endpoint includes, and everything counts toward the window together")
    if not m.get("foreign_estimates_not_used_as_truth"): f.append("TC-1 foreign estimates (tiktoken, characters divided by four, word counts) are still used as if they were counts - they are another tokenizer's arithmetic and undercount Claude, steeply on code, JSON and non-English text")
    cov=d.get("coverage") or {}
    if not cov.get("all_input_kinds_covered"): f.append("TC-2 not every input kind is covered by counting (system prompts, tool schemas, tool results, images, PDFs, thinking configuration) - tool schemas alone tax every agent step, and an uncounted kind is an unbudgeted kind")
    if not cov.get("unsupported_inputs_fallback_to_usage"): f.append("TC-2 inputs the endpoint rejects have no fallback (server tools other than the advisor tool, the MCP connector, and url/file-sourced media return invalid_request_error; their tokens come from the Messages response usage object) - treating a rejected count as zero tokens hides exactly the largest requests")
    if not cov.get("media_counted_as_base64"): f.append("TC-2 images and PDFs are not sent as base64 for counting (url and file sources are rejected at count time, and an oversized_image:error block fails counting exactly as it would fail creation) - media-heavy prompts are the ones most likely to overflow uncounted")
    pre=d.get("preflight") or {}
    if not pre.get("counted_before_send_for_costly_requests"): f.append("TC-3 costly or large requests are not counted before they are sent - counting is free and creates no message, so learning a prompt's size only from its bill pays full price for information that was free beforehand")
    if not pre.get("window_check_includes_output_ceiling"): f.append("TC-3 the context-window check ignores the output ceiling (the window holds input plus generation, so the check is counted input + max_tokens <= window, with truncated stop reasons watched) - a prompt that fits alone can still truncate its own answer silently")
    if not pre.get("routing_and_tier_decisions_use_counts"): f.append("TC-3 routing, rate-limit and pricing-tier decisions do not use counts (stay within the usage tier, catch long-context thresholds before they reprice the whole request, route oversized work before it is sent) - deciding these from character length reprices or rejects requests that a free count would have caught")
    ver=d.get("verification") or {}
    if not ver.get("estimate_headroom_held"): f.append("TC-4 no headroom is held under hard limits (the count is an estimate and actual input tokens may differ by a small amount) - aiming exactly at a window or tier boundary means ordinary estimation error alone crosses it")
    if not ver.get("count_vs_usage_reconciled"): f.append("TC-4 counted tokens are never reconciled against the usage actually billed (count logged beside response usage, differences investigated) - an unreconciled estimate drifts with every prompt and model change and nobody notices")
    if not ver.get("usage_retained_post_hoc"): f.append("TC-4 post-hoc usage is not retained (the response usage object is the ground truth every count is checked against) - without it there is nothing to reconcile and no historical output sizes to budget from")
    ops=d.get("operations") or {}
    if not ops.get("counting_limits_and_cost_discipline"): f.append("TC-5 counting's own limits and cost discipline are not recorded (counting is free with its own per-tier RPM - Start 5,000 / Build 10,000 / Scale 20,000 - separate from message creation) - an unrecorded free quota gets treated either as unusable or as infinite, and any paid counting substitute violates the prepaid rule")
    if not ops.get("cache_accounting_correct"): f.append("TC-5 cache accounting is wrong (billed prompt length is input_tokens + cache_creation_input_tokens + cache_read_input_tokens, and tier thresholds count cache tokens too; caching does not get a prompt under a threshold, only a shorter prompt does) - charting input_tokens alone can show a small prompt for a request billed at the long tier")
    if not ops.get("recount_triggers_recorded"): f.append("TC-5 recount triggers are not recorded (prompt, tool set, media or model changes - above all a tokenizer-generation migration, where the same request must be counted under both the current and the target model) - budgets measured on the old tokenizer survive silently into the new one at roughly 30 percent under")
    return f
if __name__=="__main__":
    data=json.load(open(sys.argv[1])); fails=check(data)
    if fails:
        print(f"FAIL ({len(fails)}):")
        [print(" -",x) for x in fails]; sys.exit(1)
    print("PASS"); sys.exit(0)
