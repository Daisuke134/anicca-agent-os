#!/usr/bin/env python3
"""fallback-credit-check: deterministic gate for the FALLBACK CREDIT surface
(how a manual retry after a refusal redeems the refusal's credit token so
the retry does not pay the prompt-cache write twice - opt-in header, the
two stop_details fields, retry body shapes, permitted targets, the
5-minute window, matching fields, usage verification, the rejection
ladder - is decided, not improvised per retry).
Stdlib only, offline, free.
Canonical sources (read in full 2026-11-20):
Anthropic Claude Platform Docs "Fallback credit"
https://platform.claude.com/docs/en/build-with-claude/fallback-credit (127 lines fetched;
its Reference section headings were present but the redemption-rule tables were
not expanded in the fetched text - those rules below are taken from the
platform mirror, marked AWS):
AWS Bedrock Docs "Fallback credit for refused requests (beta)"
https://docs.aws.amazon.com/bedrock/latest/userguide/claude-messages-fallback-credit.html (465 lines)
Key facts: Prompt caches are per-model. A retry on another model must
write the cached prefix into the new model's cache in full; cache writes
cost more than reads. Fallback credit removes that extra cost: the
refusal carries a credit token, you echo it on the retry, and the retry
is billed as though the conversation had been on the new model from the
start (overlapping prefix billed as cache reads, not writes). This page
is needed ONLY when you build the retry yourself (raw HTTP / custom
retry logic): server-side fallback and client-side fallback with the
SDK middleware apply fallback credit automatically.
Flow: (1) Opt in: send the possibly-refused request with beta header
anthropic-beta: fallback-credit-2026-07-01. The server-side-fallback-
2026-07-01 header also grants the same fields, EXCEPT on Claude Models
on Google Cloud (Google managed) and Amazon Bedrock, which return 400
for that header. fallback-credit-2026-06-01 is accepted, same fields.
(2) Read two fields from the refusal's stop_details:
fallback_credit_token (opaque string) and fallback_has_prefill_claim
(boolean choosing the retry body shape). Both are null when no credit
is available. (AWS: a token requires a cache read - a refusal on the
first request of a conversation, which only writes the cache, carries
none; minting failures produce null, never an error; in streaming the
fields arrive in the final message_delta's stop_details.)
(3) Build the retry: start from the refused request body, set model to
the fallback model, add the token as top-level fallback_credit_token.
(4) Send the retry with the SAME beta header - the retry needs the
header to redeem the token.
Prefill claim shapes: true -> refused body unchanged PLUS one appended
assistant message whose content echoes the refused response's content;
the retry model continues from where the refused model stopped and
completed server tool calls are not run again. false -> refused body
unchanged. (AWS adds: strip trailing whitespace from a final text
block; omit any client tool_use block with no matching tool_result;
on Bedrock prefill_claim can be absent with a token present - treat as
unknown, try continuation first.)
Permitted targets (Anthropic page): Fable 5.2 / 5.1 / 5 and Opus 5.5 ->
Opus 4.8 (claude-opus-4-8) and Opus 5 (claude-opus-5). Opus 5 -> Opus
4.8. Sonnet 5.5 -> Sonnet 5 (claude-sonnet-5). A Haiku 5.5 refusal
carries NO fallback credit - a retry after one pays the full cache
write. Availability (Anthropic page): Beta; Messages API and Managed
Agents; models Fable 5.2/5.1/5, Mythos 5.2/5.1, Opus 5.5/5, Sonnet 5.5.
Verification: the refund is visible in the retry's usage -
cache_creation_input_tokens lower and cache_read_input_tokens higher
by the SAME amount vs the same request without the token. A shift of
zero means the token was honored but there was nothing to reprice
(e.g. the retry model's cache was already warm). (AWS: a redeemed
retry also reports usage.fallback_credit {"status":{"type":"redeemed"}}
where that reporting exists; Converse does not report it - check the
cache token split instead. There is no separate credit line item.)
Rejection ladder (Anthropic page): (1) continuation retry rejected
with 400 -> resend the refused body unchanged, still with the token.
(2) unchanged body also rejected with a 400 whose message names
fallback_credit_token -> retry WITHOUT the token; the credit is
forfeited but the retry goes through. (AWS adds: if the message says
"redemption temporarily unavailable" the rejection is transient -
resend the SAME request with the SAME token inside the window instead
of stepping down.)
Redemption rules (AWS mirror of the same feature): the token expires
5 minutes after the refusal - after that, send the retry without it.
One-time and stateless; redeemable only by the same caller identity /
organization and workspace, on the same platform and endpoint that
issued it; no API to inspect or revoke. Fields that must match the
refused request: system, messages, tools, tool_choice, thinking,
cache_control, plus output_config, mcp_servers, context_management,
container when used - do not strip thinking / redacted_thinking
blocks. Fields that may change: model, max_tokens, stop_sequences,
stream, metadata, service_tier. Beta flags must be identical on both
requests - a flag on only one causes a "request body ... does not
match" 400 even if bodies are identical. Without the beta flag,
fallback_credit_token is rejected as an unknown field (400); it is
also rejected on CountTokens requests.
Batch: refusals in batch processing don't carry a credit token, and
batch requests can't redeem one - the API accepts a token on a batch
request but ignores it. Only direct Messages API requests redeem.
Server tools / shape limits (AWS + API reference): if the refused
request ran server tools, a retry WITHOUT the token runs and bills
those tools again - in that case surface the error instead of silently
retrying tokenless. The appended-assistant form is unavailable when
output_format is set or tool_choice forces tool use (and after server
tools ran under those settings the token can't be redeemed by either
shape - retry without it). A reasoning_extraction refusal has no
recommended fallback model - change the prompt instead of retrying.
The credit is a cost optimization only: if the token is null, expired
or rejected, retry without it - the retry itself does not need it.
Distinct from: refusal-check (detecting refusals and choosing
server-side vs client-side fallback - here only the manual-retry
credit redemption), prompt-caching-check (caching itself; here only
the cross-model repricing), service-tier-check (which tier served a
request), spend-limits-check (spend caps).
"""
import json, sys
CHECKS = [
 ("FC-0a","decided"), ("FC-0b","owner_recorded"), ("FC-0c","canonical_record"),
 ("FC-1a","manual_retry_only_scope_auto_paths_skip"), ("FC-1b","per_model_cache_premise_and_repricing"), ("FC-1c","beta_header_optin_both_requests"),
 ("FC-2a","two_fields_read_and_null_checked"), ("FC-2b","retry_body_from_refused_plus_model_and_token"), ("FC-2c","prefill_claim_shapes_retry"),
 ("FC-3a","permitted_targets_only_haiku_none"), ("FC-3b","five_minute_window_one_time_same_caller"), ("FC-3c","matching_fields_and_identical_beta_flags"),
 ("FC-4a","usage_shift_verifies_redemption"), ("FC-4b","batch_excluded_accepted_but_ignored"), ("FC-4c","rejection_ladder_and_transient_exception"),
 ("FC-5a","server_tools_rerun_and_shape_limits"), ("FC-5b","availability_and_models_recorded"), ("FC-5c","credit_is_optimization_retry_without_it"),
]
def main(path):
    d = json.load(open(path))
    fails = [cid for cid, key in CHECKS if d.get(key) is not True]
    for cid, key in CHECKS:
        print(f"{'PASS' if d.get(key) is True else 'FAIL'} {cid} {key}")
    print(f"TOTAL {len(CHECKS)-len(fails)}/{len(CHECKS)} pass, {len(fails)} fail")
    return 1 if fails else 0
if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
