#!/usr/bin/env python3
"""openai-compat-check: deterministic gate for the OPENAI SDK COMPATIBILITY surface.
Stdlib only, offline, free. Canonical source (read in full 2026-11-20):
Anthropic Claude Platform Docs "OpenAI SDK compatibility"
https://platform.claude.com/docs/en/cli-sdks-libraries/libraries/openai-sdk (239 lines)
Key facts: setup is an official OpenAI SDK + base URL pointed at the Claude
API + a Claude API key + a Claude model name; a personal/service key not
scoped to a workspace also needs the anthropic-workspace-id header on every
request. Most unsupported fields are SILENTLY IGNORED rather than erroring.
The strict parameter for function calling is ignored (tool JSON is not
guaranteed to follow the schema; use the native Claude API with structured
outputs for a guarantee). response_format accepts only json_schema with
strict: true; json_object or text returns 400. Audio and file inputs are not
supported (input_audio / file content parts return 400). Prompt caching is
not supported on this layer (it is in the Anthropic SDKs) and no
OpenTelemetry spans are emitted. System/developer messages are hoisted
wherever they appear and concatenated with a single newline into the
top-level system field ahead of every message; mid-conversation system
instructions need native mid-conversation system messages. Thinking: on
Claude 5 / Mythos Preview it is on by default; on other models pass the
extra body field thinking={"type":"enabled","budget_tokens":N} with
N >= 1024 and < max_tokens / max_completion_tokens; the response never
includes thinking, {"type":"adaptive"} returns 400, and on models that
reject enabled natively the layer converts enabled to adaptive (budget
required but without effect). Sampling: temperature is 0..1 (values > 1 are
capped at 1) and on Claude 4.7+ / Mythos Preview any value below 1 returns
400, so omit it; top_p passes through but those models 400 on any value
other than 0.99, and setting both temperature and top_p returns 400; n must
be exactly 1. tool_choice: "required" and a named function force a call, but
Fable 5.2, Mythos 5.2, Opus 5.5, Sonnet 5.5, Fable 5.1 and Mythos 5.1 return
400 for forced tool use (use "auto"); parallel_tool_calls is fully
supported. Response: choices[] always has length 1; completion/prompt token
details, refusal, audio, logprobs, service_tier and system_fingerprint are
always empty. Error formats match OpenAI's shape but the detailed messages
are NOT equivalent - use them only for logging and debugging. Headers:
x-ratelimit-limit-requests / -limit-tokens are not returned (the limits are
in x-ratelimit-requests / x-ratelimit-tokens), openai-version and
openai-processing-ms are not returned, and x-request-id carries the Claude
request ID. Rate limits follow the standard /v1/messages limits. Setting
temperature or top_p to a non-default value can drop the text watermark -
omit both if you rely on it. Prompts heavily tuned for OpenAI should be
reworked for Claude per the prompting best practices. Availability: Messages
API, all models. Note: the fetched text of the tools/functions and messages
array tables carried no rows, so this gate asserts nothing about those two
tables. Distinct from: structured-output-check (the native guarantee
itself), tool-choice-check (native tool choice), thinking-check (native
thinking), service-tier-check (the tier itself - service_tier is ignored
here), api-errors-check (native HTTP errors), prompt-caching-check (native
caching). This gate is the compatibility layer itself.
"""
import json, sys
CHECKS = [
 ("OC-0a","decided"), ("OC-0b","owner_recorded"), ("OC-0c","canonical_record"),
 ("OC-1a","setup_official_sdk_baseurl_key_model"), ("OC-1b","workspace_header_unscoped_key"), ("OC-1c","silently_ignored_fields_audited"),
 ("OC-2a","strict_ignored_native_for_guarantee"), ("OC-2b","response_format_json_schema_strict_only"), ("OC-2c","audio_file_400_no_caching_no_otel"),
 ("OC-3a","system_developer_hoisting_newline"), ("OC-3b","thinking_extra_field_rules"), ("OC-3c","sampling_limits_temp_topp_n"),
 ("OC-4a","tool_choice_forced_400_models"), ("OC-4b","response_shape_empties"), ("OC-4c","error_messages_not_equivalent_logging_only"),
 ("OC-5a","header_mapping_differences"), ("OC-5b","rate_limits_follow_messages_endpoint"), ("OC-5c","watermark_caution_and_prompt_retuning"),
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
