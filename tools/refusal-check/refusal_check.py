#!/usr/bin/env python3
"""refusal-check: deterministic gate for the REFUSALS AND FALLBACK surface.
Stdlib only, offline, free. Canonical source (read in full 2026-11-20):
Anthropic Claude Platform Docs "Refusals and fallback"
https://platform.claude.com/docs/en/build-with-claude/refusals-and-fallback
Key facts: a refusal is an HTTP 200 with stop_reason "refusal" (not an error);
stop_details is always present on a refusal, null for every other stop reason,
and its category/explanation can be null (display explanation, never parse it).
Categories: cyber / bio / frontier_llm / reasoning_extraction / general_harms.
Pre-output refusals are billed only for bio, frontier_llm, reasoning_extraction;
mid-stream refusals bill input + streamed output; partial output is discarded.
reasoning_extraction has NO recommended fallback: change the prompt, keep
reasoning in thinking blocks (display summarized). Three retry routes:
server-side fallbacks ("default" or up to 3 distinct permitted models, beta
server-side-fallback-2026-07-01; only a classifier decline triggers it, never
429/529/5xx), SDK middleware (BetaRefusalFallbackMiddleware + shared
BetaFallbackState, client.beta.messages), or a manual retry redeeming fallback
credit on every self-built retry (body unchanged for redemption). Haiku 5.5 has
no server-side fallback and no fallback credit. Retry a DIFFERENT model (same
model usually refuses again), stay on the fallback model for later turns
(sticky routing ~1h, org-scoped, best-effort). Echo the fallback block exactly
in place; drop thinking/redacted_thinking/connector_text and client tool_use
before the final fallback block. Fallback must be configured on EVERY request
path (retries, error recovery, background workers) and subagent calls need
their own fallbacks; budget retries per request, not per turn/session.
Instrument refusals as their own signal (one event per refusal + one per
fallback-served response, alert on the gap) because error-rate monitoring
never sees an HTTP 200. Batches: result succeeded + stop_reason refusal, no
fallback credit token, server-side fallback unavailable (per-item error);
collect refused items and resubmit on a fallback model.
Exit 0 = all pass, 1 = any fail. null/unverified counts as fail."""
import json, sys
def check(d):
    r = {}
    r["RF-0a_surface_decided"] = d.get("decided") is True
    r["RF-0b_owner_and_source"] = bool(d.get("owner")) and bool(d.get("source"))
    r["RF-0c_every_path_and_subagents"] = d.get("fallback_on_every_request_path") is True and d.get("subagent_calls_have_own_fallback") is True
    r["RF-1a_branch_on_stop_reason"] = d.get("branch_on_stop_reason_refusal") is True and d.get("not_branch_on_content_or_inner_fields") is True
    r["RF-1b_stop_details_handling"] = d.get("stop_details_null_rules_handled") is True and d.get("explanation_displayed_not_parsed") is True
    r["RF-1c_partial_output_discarded"] = d.get("partial_output_treated_incomplete_discarded") is True
    r["RF-2a_approach_chosen_per_situation"] = d.get("fallback_mechanism_on_primary_path") is True and d.get("approach_matched_to_platform") is True
    r["RF-2b_server_side_config"] = d.get("fallbacks_param_and_beta_header") is True
    r["RF-2c_haiku_exception"] = d.get("haiku55_no_server_no_credit_handled") is True
    r["RF-3a_different_permitted_model"] = d.get("retry_targets_different_model") is True and d.get("fallback_list_distinct_permitted_max3") is True
    r["RF-3b_reasoning_extraction_reprompt"] = d.get("reasoning_extraction_reprompt_not_retry") is True and d.get("between_tools_adjusted_on_retry") is True
    r["RF-3c_stay_on_fallback"] = d.get("stay_on_fallback_for_later_turns") is True
    r["RF-4a_echo_fallback_block_exactly"] = d.get("fallback_block_echoed_exactly_in_place") is True and d.get("pre_boundary_blocks_dropped_per_table") is True
    r["RF-4b_streaming_nonstreaming"] = d.get("streaming_vs_nonstreaming_difference_handled") is True
    r["RF-4c_fallback_credit_redeemed"] = d.get("fallback_credit_redeemed_on_manual_retries") is True
    r["RF-5a_refusals_instrumented"] = d.get("refusal_and_fallback_events_emitted") is True and d.get("alert_on_refusal_fallback_gap") is True
    r["RF-5b_billing_iterations_read"] = d.get("billed_categories_understood") is True and d.get("usage_iterations_read_per_attempt") is True
    r["RF-5c_batches_separate"] = d.get("batch_refusals_resubmitted_separately") is True
    r["pass_count"] = sum(1 for v in r.values() if v is True)
    r["fail_count"] = sum(1 for v in r.values() if v is False)
    r["pass"] = r["fail_count"] == 0
    return r
if __name__ == "__main__":
    v = check(json.load(open(sys.argv[1])))
    print(json.dumps(v, indent=2)); sys.exit(0 if v["pass"] else 1)
