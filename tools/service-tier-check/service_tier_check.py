#!/usr/bin/env python3
"""service-tier-check: deterministic gate for the SERVICE TIERS surface.
Stdlib only, offline, free. Canonical source (read in full 2026-11-20):
Anthropic Claude Platform Docs "Service tiers"
https://platform.claude.com/docs/en/api/service-tiers
Key facts: three tiers - Priority (only for organizations with an existing
capacity commitment), Standard (default for piloting and scaling, best-effort
availability, prioritized alongside all other requests), Batch (asynchronous
workflows that can wait or benefit from being outside normal capacity).
Priority requests are prioritized over all other requests, which minimizes
"server overloaded" errors even at peak. Assignment: a request is assigned
Priority only when the org has sufficient Priority capacity in BOTH input
tokens per minute AND output tokens per minute; otherwise it proceeds at
standard tier. Burndown against Priority capacity: cache reads 0.1 tokens per
token, cache writes 1.25 (5-minute TTL) / 2.00 (1-hour TTL), US-only inference
(inference_geo "us", Claude 4.6+) input and output 1.1 tokens per token, all
other tokens 1 per token. Control: request parameter service_tier accepts
"auto" (default: use Priority capacity if available, fall back to other
capacity if not) and "standard_only" (never consume Priority capacity). The
response usage object reports the tier actually assigned; with service_tier
"auto" on a committed model, response headers show Priority eligibility even
when the request was over the limit. A commitment consists of input TPM,
output TPM, a duration of 1/3/6/12 months, and a specific model version; it
targets 99.5% uptime with prioritized compute, and requests beyond committed
capacity automatically fall back to standard. Priority is supported on all
available models EXCEPT Fable 5.2/5.1, Haiku 5.5, Mythos 5.2/5.1/5/Preview,
Opus 5.5/5, Sonnet 5.5/5. The feature status on the page is Legacy; APIs are
Messages API and Managed Agents.
Exit 0 = all pass, 1 = any fail. null/unverified = fail."""
import json, sys
def check(d):
    r = {}
    r["ST-0a_surface_decided"] = d.get("decided") is True
    r["ST-0b_owner_and_source"] = bool(d.get("owner")) and bool(d.get("source"))
    r["ST-0c_workloads_classified_by_latency"] = d.get("workloads_classified_interactive_vs_async") is True
    r["ST-1a_standard_default_best_effort"] = d.get("standard_is_default_best_effort_known") is True
    r["ST-1b_priority_prioritized_minimizes_overloaded"] = d.get("priority_prioritized_over_all_minimizes_overloaded_known") is True
    r["ST-1c_batch_for_async_outside_normal_capacity"] = d.get("batch_used_for_async_workloads") is True
    r["ST-2a_assignment_needs_input_and_output_capacity"] = d.get("assignment_requires_sufficient_input_and_output_capacity") is True
    r["ST-2b_burndown_rates_known"] = d.get("burndown_rates_known_cache_read_01_write_125_200") is True
    r["ST-2c_us_only_multiplier_and_standard_fallback"] = d.get("us_only_11_multiplier_and_fallback_to_standard_known") is True
    r["ST-3a_service_tier_param_set_deliberately"] = d.get("service_tier_param_auto_vs_standard_only_set_deliberately") is True
    r["ST-3b_usage_service_tier_read"] = d.get("response_usage_service_tier_read_per_request") is True
    r["ST-3c_priority_headers_eligibility_detected"] = d.get("priority_response_headers_used_for_eligibility_detection") is True
    r["ST-4a_commitment_shape_known"] = d.get("commitment_shape_tpm_duration_model_version_known") is True
    r["ST-4b_uptime_target_and_overflow_fallback"] = d.get("uptime_995_target_and_beyond_capacity_falls_back_standard_known") is True
    r["ST-4c_excluded_models_checked"] = d.get("priority_excluded_models_checked_before_assuming") is True
    r["ST-5a_existing_commitment_prerequisite"] = d.get("priority_not_assumed_without_existing_commitment") is True
    r["ST-5b_tier_matched_per_workload"] = d.get("tier_choice_matched_per_workload_not_one_global_default") is True
    r["ST-5c_legacy_status_and_availability_checked"] = d.get("legacy_status_and_api_model_availability_checked") is True
    r["pass_count"] = sum(1 for v in r.values() if v is True)
    r["fail_count"] = sum(1 for v in r.values() if v is False)
    r["pass"] = r["fail_count"] == 0
    return r
if __name__ == "__main__":
    v = check(json.load(open(sys.argv[1])))
    print(json.dumps(v, indent=2)); sys.exit(0 if v["pass"] else 1)
