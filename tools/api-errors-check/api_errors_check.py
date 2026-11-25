#!/usr/bin/env python3
"""api-errors-check: deterministic gate for the API ERRORS surface.
Stdlib only, offline, free. Canonical source (read in full 2026-11-20):
Anthropic Claude Platform Docs "Claude API errors"
https://platform.claude.com/docs/en/api/errors (247 lines)
Key facts: predictable HTTP taxonomy - 400 invalid_request_error (also other
unlisted 4xx, and org/workspace spend limit reached; Claude Code workspace
limits are the exception and can return 429), 401 authentication_error
(malformed/revoked/expired key; on Claude Platform on AWS also AWS creds /
SigV4), 402 billing_error, 403 permission_error, 404 not_found_error,
409 conflict_error (resolve then retry), 413 request_too_large,
429 rate_limit_error (rate limit, usage-tier monthly spend cap, or Claude
Code workspace spend limit; a tier spend-cap 429 has NO retry-after header
and keeps failing until access resumes; ramp limits can 429 even under
limits), 500 api_error (retry with exponential backoff, then support with
request ID; timeout_error can ride other codes e.g. 500 at server time
limit), 504 timeout_error, 529 overloaded_error. Official SDK auto-retries
transient failures (connection errors, rate limits, 5xx) with exponential
backoff, twice by default, honoring retry-after; max_retries configures or
disables it. A 401 whose message begins "CORS requests are not allowed for
this Organization" is NOT a key problem: the request carried an Origin
header, the org cannot call the API from a browser, no browser-side change
fixes it, send from your own back end (wording "because of custom retention
settings" = retention arrangements such as ZDR; "because of its settings"
= general case incl. Compliance API). SSE: errors can occur after a 200;
mid-stream errors do not follow these mechanisms (see Error events).
Size limits (first-party): Messages 128 MB, Token Counting 128 MB,
Batch 256 MB, Files 500 MB; over -> 413, returned by Cloudflare before the
request reaches API servers. Error shape: JSON with top-level error object
(always type + message) plus request_id field; values can expand and new
type values can appear under the API versioning policy. SDK raises typed
exceptions (404 -> anthropic.NotFoundError; Go has one *anthropic.Error,
branch on StatusCode): catch typed classes, most specific first, never
string-match messages. Every response carries a request-id header (also
request_id in error bodies); include it when contacting support. On Claude
Platform on AWS there are two IDs: x-amzn-requestid (primary, CloudTrail)
and request-id (secondary, Anthropic support). Python/TS expose _request_id;
other SDKs via raw-response accessors (Ruby via middleware); with_raw_response
reads other headers. Long requests: large max_tokens without streaming risks
idle-connection drops; use streaming or Message Batches (poll); TCP socket
keep-alive helps; the SDK validates non-streaming requests against a
10-minute timeout and sets keep-alive, and can consume a stream into the
final Message. Common validation 400s: prefill unsupported on Claude 4.6+
and Mythos Preview (use structured outputs / system / output_config.format);
thinking blocks must be resent exactly as returned incl. empty thinking and
redacted_thinking (filtering by type breaks it; distinct from prefix check);
extended thinking unsupported on 4.7+ (use adaptive), adaptive unsupported
on 4.5-and-earlier-only-extended models (use enabled + budget_tokens);
thinking cannot be disabled on Fable 5/5.1/5.2, Mythos 5/5.1/5.2, Opus 5.5,
Mythos Preview; Sonnet 5.5 lowest is between_tools (disabled -> 400;
between_tools at xhigh/max effort -> 400; effort cannot change
mid-conversation with between_tools; Haiku 5.5 accepts disabled under the
same two effort limits; Sonnet 5.5 and Haiku 5.5 also reject enabled);
between_tools to any model other than Sonnet 5.5 -> 400; omitting thinking
runs adaptive; display omitted hides content without disabling. Forced tool
use unsupported on Fable 5.2, Mythos 5.2, Opus 5.5, Sonnet 5.5, Fable 5.1,
Mythos 5.1 (any/tool -> 400 incl. token counting; auto/none accepted; use
auto + strict tool use or structured outputs). Computer use: current models
reject unaccepted tool versions (Claude API incl. computer_20251124 + beta
header; computer_20250124 accepted nowhere); same message for any
unsupported Anthropic-defined tool type, naming accepted types after "Did
you mean one of"; current models use computer_toolset_20260801 without beta
header; Bedrock additionally accepts computer_20251124 with
computer-use-2025-11-24 in anthropic_beta body array via InvokeModel.
Prefix check: thinking block bound to a different conversation -> compare
system/tools/prior messages; resending same history fails same way; fix by
beta header thinking-binding-controls-2026-08-01 + prefix_mismatch_behavior
drop_block on retry and every later request (Sonnet 5.5 / Haiku 5.5:
block_binding only with adaptive), or strip the named block and every
thinking/redacted_thinking block after it in that and every later message;
sending block_binding without the beta header -> 400; keep history
append-only to prevent. Outbound web identity federation disabled (AWS):
run aws iam enable-outbound-web-identity-federation once per account.
Refusals are HTTP 200, not errors (see refusal-check). Exit 0 = all pass,
1 = any fail. null/unverified = fail."""
import json, sys
def check(d):
    r = {}
    r["AE-0a_surface_decided"] = d.get("decided") is True
    r["AE-0b_owner_and_source"] = bool(d.get("owner")) and bool(d.get("source"))
    r["AE-0c_errors_distinct_from_refusal_200"] = d.get("errors_distinguished_from_refusal_http200_and_fallback_surfaces_known") is True
    r["AE-1a_full_code_type_map"] = d.get("code_type_map_400_401_402_403_404_409_413_429_500_504_529_known") is True
    r["AE-1b_400_spend_limit_and_cc_exception"] = d.get("bad_request_also_spend_limit_and_unlisted_4xx_claude_code_workspace_limit_returns_429_known") is True
    r["AE-1c_429_variants_no_retry_after_ramp"] = d.get("tier_spend_cap_429_no_retry_after_persists_and_ramp_limits_429_under_limits_known") is True
    r["AE-2a_sdk_auto_retry_defaults"] = d.get("sdk_auto_retries_transient_2x_default_exp_backoff_honors_retry_after_max_retries_configurable_known") is True
    r["AE-2b_retry_only_transient_409_500_529"] = d.get("retry_only_transient_409_resolve_then_retry_500_backoff_then_support_with_request_id_529_transient_known") is True
    r["AE-2c_cors_401_not_a_key_problem"] = d.get("cors_401_message_is_origin_retention_or_settings_not_key_no_browser_fix_route_via_backend_known") is True
    r["AE-3a_error_shape_and_expansion"] = d.get("error_json_top_level_error_type_message_plus_request_id_values_can_expand_new_types_known") is True
    r["AE-3b_request_id_everywhere_aws_dual"] = d.get("request_id_header_every_response_include_for_support_sdk_accessors_aws_dual_id_roles_known") is True
    r["AE-3c_typed_exceptions_not_string_match"] = d.get("branch_on_sdk_typed_exceptions_or_status_most_specific_first_never_string_match_go_single_type_known") is True
    r["AE-4a_size_limits_cloudflare_413"] = d.get("size_limits_messages_tokencount_128mb_batch_256mb_files_500mb_413_from_cloudflare_firstparty_known") is True
    r["AE-4b_long_requests_stream_batch_keepalive"] = d.get("long_request_idle_drop_risk_use_streaming_or_batches_poll_tcp_keepalive_known") is True
    r["AE-4c_sdk_10min_validation_sse_after_200"] = d.get("sdk_validates_nonstreaming_10min_sets_keepalive_can_consume_stream_sse_errors_after_200_separate_known") is True
    r["AE-5a_prefill_and_thinking_verbatim"] = d.get("prefill_unsupported_46plus_use_structured_system_format_thinking_blocks_resent_verbatim_incl_empty_redacted_known") is True
    r["AE-5b_thinking_config_matrix"] = d.get("thinking_matrix_extended_vs_adaptive_by_generation_cannot_disable_models_between_tools_rules_effort_locks_known") is True
    r["AE-5c_forced_tool_computer_prefix"] = d.get("forced_tool_use_unsupported_models_computer_toolset_versions_prefix_drop_block_beta_or_strip_appendonly_known") is True
    r["pass_count"] = sum(1 for v in r.values() if v is True)
    r["fail_count"] = sum(1 for v in r.values() if v is False)
    r["pass"] = r["fail_count"] == 0
    return r
if __name__ == "__main__":
    v = check(json.load(open(sys.argv[1])))
    print(json.dumps(v, indent=2)); sys.exit(0 if v["pass"] else 1)
