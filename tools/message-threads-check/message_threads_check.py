#!/usr/bin/env python3
"""message-threads-check: deterministic gate for the MESSAGE THREADS surface.
Stdlib only, offline, free. Canonical source (read in full 2026-11-20):
Anthropic Claude Platform Docs "Message threads"
https://platform.claude.com/docs/en/build-with-claude/message-threads (439 lines)
Key facts: public beta 2026-11-02, beta header message-threads-2026-08-12.
Gain is latency not cost: median TTFT about -35% on 500k-1M token requests
(Anthropic's own figure, no independent benchmark); token usage, pricing and
rate limits unchanged; Claude still reads the full conversation each turn.
Create: full conversation + system + tools + thread {type:create}; API stores
conversation incl. reply under response id. Continue: only new messages +
thread {type:continue, previous_message_id}; system/tools omitted (sending
either, even null, is 400). Fixed fields (model, tool_choice, thinking,
mcp_servers apart from auth token, context_management, output_config, skills
in container, top-level cache_control, anthropic-beta set, and fallbacks
all-or-none) must be identical every request; mismatch is 400
thread_fingerprint_mismatch naming differing fields. Free: max_tokens,
stop_sequences, stream, metadata, service_tier. Thread expires 5 min after
last request, deleted <=1h after last use, held in memory encrypted under a
server-managed key, never durable storage. Application stays source of truth:
keep own copy of every message, build replay from the start; no create/continue
response says whether the turn was stored. 404 thread_not_found (causes:
expiry, turn not stored e.g. tool call cut off by max_tokens, fallback model
wrote it, still generating, different org/workspace/user/key, first image)
-> replay full conversation in new create; check error_code first because a
nonexistent model also returns 404. Each response id can be continued once;
always continue from latest id; append-only (edit/branch/compact = new thread,
compaction written by client as summary message; built-in compaction not
available). Caching: thread does not cache; max 4 cache_control breakpoints
per threaded request, top-level counts as one, create-request system/tools
breakpoints count again on every continue; breakpoints cannot be moved/removed.
Streaming: response id in message_start but continue only after message_stop;
dropped stream -> resend same continue, on thread_already_continued /
thread_continue_in_flight replay. pause_turn: resume with continue from that
id and empty messages []; never send a new user message while paused; 404 ->
replay including paused response. Unsupported (400 thread_unsupported_request):
Message Batches, token counting, compaction, context editing except
clear_thinking_20251015 keep:all, HIPAA-readiness orgs, inference-hooks orgs;
unsupported values include context_management, cache_control, fallbacks, hipaa,
inference_hooks; unknown value -> send without thread. Refusal: do not continue;
new thread omitting/rephrasing the refused turn (helper drops it). Fallbacks:
thread keeps one model, fallback-written turns are not stored; detect
fallback_message in usage.iterations (stream: final message_delta); then new
create with full conversation (same request again, or new thread on fallback
model without fallbacks); sticky routing about 1 hour, continue requests never
start/use it, not under ZDR/CMEK orgs. Not ZDR eligible (does not affect other
features' ZDR). Files held by reference: keep files available. No API to list,
read or delete a thread. Available: Claude API, Claude Platform on AWS, Claude
Models on Google Cloud (Anthropic managed), Microsoft Foundry; all models.
Exit 0 = all pass, 1 = any fail. null/unverified = fail."""
import json, sys
def check(d):
    r = {}
    r["MT-0a_surface_decided"] = d.get("decided") is True
    r["MT-0b_owner_and_source"] = bool(d.get("owner")) and bool(d.get("source"))
    r["MT-0c_latency_not_cost_pricing_unchanged"] = d.get("gain_is_latency_not_cost_ttft35_500k_1m_pricing_ratelimits_unchanged_known") is True
    r["MT-1a_create_full_system_tools"] = d.get("create_sends_full_conversation_system_tools_thread_create_stored_under_response_id_known") is True
    r["MT-1b_continue_new_only_omit_system_tools"] = d.get("continue_sends_only_new_messages_previous_id_omits_system_tools_even_null_400_known") is True
    r["MT-1c_beta_header_every_request"] = d.get("beta_header_message_threads_2026_08_12_on_every_request_known") is True
    r["MT-2a_fixed_fields_identical_fingerprint"] = d.get("fixed_fields_model_toolchoice_thinking_mcp_ctxmgmt_outputconfig_skills_cachecontrol_betaset_identical_mismatch400_known") is True
    r["MT-2b_free_fields_and_fallbacks_all_or_none"] = d.get("free_fields_maxtokens_stop_stream_metadata_tier_can_change_and_fallbacks_all_requests_or_none_known") is True
    r["MT-2c_change_means_new_thread_thinking_drop"] = d.get("changing_createonly_or_fixed_means_new_thread_and_thinking_blocks_dropped_on_listed_models_known") is True
    r["MT-3a_expiry_5min_delete_1h_inmemory"] = d.get("expires_5min_deleted_within_1h_inmemory_encrypted_never_durable_known") is True
    r["MT-3b_own_copy_source_of_truth_replay"] = d.get("application_source_of_truth_keep_own_copy_replay_built_from_start_no_storage_confirmation_known") is True
    r["MT-3c_404_replay_check_code_once_latest"] = d.get("thread_not_found_404_replay_full_new_create_check_error_code_continue_once_from_latest_id_known") is True
    r["MT-4a_cache_max4_thread_does_not_cache"] = d.get("thread_does_not_cache_max4_breakpoints_toplevel_counts_create_breakpoints_recounted_known") is True
    r["MT-4b_streaming_after_message_stop_drop_recovery"] = d.get("continue_only_after_message_stop_dropped_stream_resend_then_replay_on_already_continued_in_flight_known") is True
    r["MT-4c_pause_turn_empty_resume"] = d.get("pause_turn_resume_continue_empty_messages_no_new_user_message_404_replay_including_paused_known") is True
    r["MT-5a_unsupported_list_400"] = d.get("unsupported_batches_tokencount_compaction_contextedit_except_clearthinking_keepall_hipaa_inferencehooks_400_known") is True
    r["MT-5b_refusal_and_fallback_new_thread"] = d.get("refusal_do_not_continue_new_thread_fallback_turn_not_stored_detect_fallback_message_new_create_sticky1h_known") is True
    r["MT-5c_not_zdr_files_by_reference_no_list_api"] = d.get("not_zdr_eligible_files_by_reference_keep_available_no_list_read_delete_api_known") is True
    r["pass_count"] = sum(1 for v in r.values() if v is True)
    r["fail_count"] = sum(1 for v in r.values() if v is False)
    r["pass"] = r["fail_count"] == 0
    return r
if __name__ == "__main__":
    v = check(json.load(open(sys.argv[1])))
    print(json.dumps(v, indent=2)); sys.exit(0 if v["pass"] else 1)
