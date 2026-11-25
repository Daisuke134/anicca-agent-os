#!/usr/bin/env python3
"""fine-grained-check: deterministic gate for the FINE-GRAINED TOOL STREAMING surface.
Stdlib only, offline, free. Canonical sources (read in full 2026-11-20):
Anthropic Claude Platform Docs "Fine-grained tool streaming"
https://platform.claude.com/docs/en/agents-and-tools/tool-use/fine-grained-tool-streaming
and the fine-grained section of AWS Bedrock "Anthropic Claude tool use"
https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-anthropic-claude-messages-tool-use.html
Key facts: set eager_input_streaming=true per user-defined tool + stream the
request; omitted = buffered+validated, explicit false stays buffered even
under the legacy header fine-grained-tool-streaming-2025-05-14 (request-wide
for unset tools, replaced by the per-tool field). The header cannot be
combined with a computer/browser toolset entry (API rejects the request).
Sonnet 4.5 supports the header but rejects the field (Extra inputs are not
permitted) - use the header for that model. Accumulation contract:
content_block_start carries input:{} as a placeholder; concatenate
input_json_delta partial_json fragments; parse at content_block_stop (SDK
accumulator helpers exist for Python/TS/Go/Java/Ruby). The server does NOT
validate or coerce, so the accumulated string may be invalid or incomplete
JSON: guard the parse, never run the tool on it, and report the failure back
as a tool_result with is_error=true whose content is the raw string wrapped
in a JSON object under a single key. A max_tokens stop can end the stream
mid-parameter: check stop_reason, retry with higher max_tokens or repair.
SDK tolerant parsers can silently return truncated input, so validate every
parsed tool input against its schema before executing. Enable only where a
large tool input makes first-fragment latency matter; small inputs gain
nothing and lose server-side validation. Availability: Messages API, all
models. Exit 0 = all pass, 1 = any fail. null/unverified counts as fail."""
import json, sys
def check(d):
    r = {}
    r["FG-0a_surface_decided"] = d.get("decided") is True
    r["FG-0b_owner_and_source"] = bool(d.get("owner")) and bool(d.get("source"))
    r["FG-0c_large_input_tools_inventoried"] = d.get("large_input_tools_inventoried") is True
    r["FG-1a_per_tool_field_default"] = d.get("eager_set_per_tool") is True and d.get("legacy_header_not_default") is True
    r["FG-1b_streaming_enabled"] = d.get("streaming_enabled_on_fg_requests") is True
    r["FG-1c_model_support_checked"] = d.get("model_support_checked_incl_sonnet45_header_only") is True
    r["FG-2a_accumulation_contract"] = d.get("accumulation_via_sdk_helper_or_manual_contract") is True
    r["FG-2b_placeholder_not_mistaken"] = d.get("placeholder_empty_input_not_treated_as_real") is True
    r["FG-2c_parse_guarded"] = d.get("parse_guarded_at_block_stop") is True
    r["FG-3a_invalid_json_error_result"] = d.get("invalid_json_reported_as_error_tool_result_single_key_wrapper") is True
    r["FG-3b_no_execution_on_partials"] = d.get("no_execution_on_partial_fragments") is True
    r["FG-3c_schema_validated_before_run"] = d.get("parsed_input_schema_validated_before_execution") is True
    r["FG-4a_max_tokens_truncation"] = d.get("max_tokens_truncation_checked_and_retried_or_repaired") is True
    r["FG-4b_header_toolset_conflict"] = d.get("header_never_combined_with_toolsets") is True
    r["FG-4c_explicit_false_respected"] = d.get("explicit_false_keeps_buffered_where_validation_matters") is True
    r["FG-5a_error_rates_measured"] = d.get("invalid_and_truncation_rates_measured_per_tool") is True
    r["FG-5b_scoped_to_large_inputs"] = d.get("enablement_scoped_to_large_inputs_only") is True
    r["FG-5c_revalidate_on_change"] = d.get("revalidated_on_model_or_sdk_change") is True
    r["pass_count"] = sum(1 for v in r.values() if v is True)
    r["fail_count"] = sum(1 for v in r.values() if v is False)
    r["pass"] = r["fail_count"] == 0
    return r
if __name__ == "__main__":
    v = check(json.load(open(sys.argv[1])))
    print(json.dumps(v, indent=2)); sys.exit(0 if v["pass"] else 1)
