#!/usr/bin/env python3
"""data-residency-check: deterministic gate for the DATA RESIDENCY surface.
Stdlib only, offline, free. Canonical source (read in full 2026-11-20):
Anthropic Claude Platform Docs "Data residency"
https://platform.claude.com/docs/en/manage-claude/data-residency
Key facts: two INDEPENDENT controls - inference geo (where model inference
runs, per request, via the inference_geo parameter or a workspace default)
and workspace geo (where data is stored at rest and where endpoint
processing such as image transcoding and code execution occurs, set in the
Console at workspace level). inference_geo values: "global" (default,
inference may run in any available geography, standard pricing) and "us"
(inference runs only in US-based infrastructure). The response usage object
includes an inference_geo field indicating where inference actually ran.
Model availability: supported on Claude 4.6 and later models; requests with
inference_geo on Opus 4.5, Sonnet 4.5 (deprecated), Haiku 4.5 or earlier
return a 400 error. Workspace restrictions: allowed_inference_geos restricts
which geos a workspace can use (a request specifying a geo outside the list
returns 400); default_inference_geo is the fallback when the parameter is
omitted, must be one of the allowed geos, and a request can override it with
any other allowed geo. Both fields can also be set via the Admin API inside
the data_residency object of Create/Update Workspace (an omitted field in an
update keeps its value). Workspace geo is set at workspace creation and
can't be changed afterward; currently "us" is the only available workspace
geo. Pricing (4.6+): US-only inference is 1.1x the standard rate across ALL
token pricing categories (input, output, cache writes, cache reads); on
Haiku 5.5 the multiplier also applies to the higher prices for prompts over
100k tokens. Global routing is standard pricing. Older models don't support
inference_geo and including it returns 400. Pricing applies to the Claude
API (first-party), Claude Platform on AWS, and Claude Models on Google
Cloud (Anthropic managed); on Foundry the same 1.1x applies to Azure-hosted
deployments using the US Data Zone Standard deployment type; partner-
operated platforms (Google-managed, Bedrock) have their own regional
pricing. Managed Agents: when an agent's model configuration pins
inference_geo to "us", model requests in sessions running that agent are
priced at 1.1x. Batch API supports inference_geo per request. Legacy global-
routing opt-outs were auto-migrated to allowed_inference_geos ["us"] and
default_inference_geo "us" with no code changes needed. Limitations: rate
limits are shared across all geos; only "us" and "global" inference geos
exist; only "us" workspace geo exists and it is immutable after creation.
Exit 0 = all pass, 1 = any fail. null/unverified = fail."""
import json, sys
def check(d):
    r = {}
    r["DR-0a_surface_decided"] = d.get("decided") is True
    r["DR-0b_owner_and_source"] = bool(d.get("owner")) and bool(d.get("source"))
    r["DR-0c_two_controls_distinguished"] = d.get("inference_geo_vs_workspace_geo_distinguished_as_independent") is True
    r["DR-1a_values_global_default_us_only"] = d.get("inference_geo_values_global_default_and_us_only_known") is True
    r["DR-1b_us_means_us_infrastructure_only"] = d.get("us_value_means_us_based_infrastructure_only_known") is True
    r["DR-1c_global_any_geography_standard_pricing"] = d.get("global_means_any_geography_and_standard_pricing_known") is True
    r["DR-2a_supported_46_and_later_only"] = d.get("inference_geo_supported_on_46_and_later_only_known") is True
    r["DR-2b_older_models_400_param_gated_by_model"] = d.get("older_models_return_400_so_param_gated_by_model") is True
    r["DR-2c_batch_per_request_geo"] = d.get("batch_api_per_request_inference_geo_known") is True
    r["DR-3a_allowed_geos_restriction_400"] = d.get("allowed_inference_geos_restriction_and_400_on_violation_set") is True
    r["DR-3b_default_in_allowed_request_override"] = d.get("default_inference_geo_in_allowed_and_request_can_override_with_allowed") is True
    r["DR-3c_workspace_geo_us_only_immutable"] = d.get("workspace_geo_us_only_set_at_creation_immutable_known") is True
    r["DR-4a_us_only_11x_all_categories"] = d.get("us_only_11x_all_token_categories_incl_haiku_long_context_known") is True
    r["DR-4b_platform_pricing_scope"] = d.get("pricing_scope_firstparty_aws_google_managed_foundry_vs_partner_known") is True
    r["DR-4c_managed_agents_pinned_us_11x"] = d.get("managed_agents_pinned_us_also_11x_known") is True
    r["DR-5a_usage_inference_geo_read"] = d.get("response_usage_inference_geo_read_per_request") is True
    r["DR-5b_legacy_optout_migration_mapping"] = d.get("legacy_optout_migrated_to_allowed_us_default_us_known") is True
    r["DR-5c_limitations_shared_limits_endpoint_processing"] = d.get("limitations_shared_rate_limits_and_endpoint_processing_follows_workspace_geo_known") is True
    r["pass_count"] = sum(1 for v in r.values() if v is True)
    r["fail_count"] = sum(1 for v in r.values() if v is False)
    r["pass"] = r["fail_count"] == 0
    return r
if __name__ == "__main__":
    v = check(json.load(open(sys.argv[1])))
    print(json.dumps(v, indent=2)); sys.exit(0 if v["pass"] else 1)
