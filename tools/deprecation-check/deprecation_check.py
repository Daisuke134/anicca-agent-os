#!/usr/bin/env python3
"""deprecation-check: deterministic gate for the MODEL DEPRECATION surface.
Stdlib only, offline, free. Canonical source (read in full 2026-11-20):
Anthropic Claude Platform Docs "Model deprecations"
https://docs.claude.com/en/docs/about-claude/model-deprecations
Key facts: lifecycle is Active (fully supported, recommended) / Legacy (no
updates, might be deprecated) / Deprecated (still functional, not recommended,
named replacement + retirement date) / Retired (unavailable, requests fail).
Dates on the page apply to Anthropic-operated platforms only (Claude API,
Claude Platform on AWS, Claude Models on Google Cloud Anthropic-managed,
Microsoft Foundry); partner-operated platforms (Amazon Bedrock, Google-managed
Claude Models) set their own schedules. Claude Code uses the Claude API, so
these dates apply to it unless it is set up for another platform or a gateway.
Notice: at least 60 days before retirement for publicly released models, to
customers with active deployments, by email and in the documentation - and the
docs still tell you to check the page regularly yourself. Audit: Console Usage
page -> Export -> CSV broken down by API key and model. Migration: migrate ALL
usage before the retirement date, test replacements on your own tasks well
before it, adopt the recommended replacement as soon as possible; for Claude
Code, update Claude Code first, check which model is in use even when unset or
set via an alias such as `sonnet`, and change the old model everywhere it is
set, including subagent definitions and administrator-set models. A retirement
covers the undated alias too (claude-sonnet-4-5 retires with
claude-sonnet-4-5-20250929 on 2026-11-30; replacement claude-sonnet-5-5).
Claude Code fallback chains only soften the failure: on a retired model the
error begins "There's an issue with the selected model", a fallback chain
switches to the next model for that turn and tries the retired one again on
the next message - that is not a migration. Current table (2026-11-20 read):
claude-sonnet-4-5-20250929 Deprecated 2026-09-30, retires 2026-11-30;
claude-mythos-preview Deprecated, retirement TBA; several Active models carry
"not sooner than" tentative dates (e.g. claude-opus-4-5-20251101 not sooner
than 2026-11-24) which are earliest bounds, not retirement dates. Parameter
deprecations are a second track: temperature/top_p/top_k were REMOVED in API
version 2026-10-21 and return 400; earlier API versions return an error when
they are set to a non-default value on Claude 4.7+ models and Mythos Preview;
the replacement is to omit them and guide behavior with prompting.
Exit 0 = all pass, 1 = any fail. null/unverified = fail."""
import json, sys
def check(d):
    r = {}
    r["MD-0a_surface_decided"] = d.get("decided") is True
    r["MD-0b_owner_and_source"] = bool(d.get("owner")) and bool(d.get("source"))
    r["MD-0c_pinned_models_inventoried_all_surfaces"] = d.get("pinned_models_inventoried_incl_subagents_aliases_admin") is True
    r["MD-1a_lifecycle_state_tracked_per_model"] = d.get("lifecycle_state_tracked_per_pinned_model") is True
    r["MD-1b_platform_split_dates"] = d.get("retirement_dates_split_anthropic_vs_partner_platforms") is True
    r["MD-1c_notice_60d_and_regular_docs_check"] = d.get("notice_floor_60d_known_and_docs_checked_regularly_not_email_only") is True
    r["MD-2a_usage_audit_csv_by_key_and_model"] = d.get("usage_audit_via_console_export_csv_by_key_and_model") is True
    r["MD-2b_aliases_resolved_undated_counts"] = d.get("aliases_and_undated_ids_resolved_to_dated_models") is True
    r["MD-2c_claude_code_updated_first_changed_everywhere"] = d.get("claude_code_updated_first_and_model_changed_everywhere_incl_admin") is True
    r["MD-3a_migrate_all_before_retirement"] = d.get("all_usage_migrated_before_retirement_date") is True
    r["MD-3b_replacement_tested_well_before_on_own_tasks"] = d.get("replacement_tested_well_before_retirement_on_own_tasks") is True
    r["MD-3c_recommended_replacement_adopted_asap"] = d.get("recommended_replacement_adopted_asap_not_arbitrary") is True
    r["MD-4a_deprecated_params_inventoried"] = d.get("deprecated_request_params_inventoried_temp_topp_topk") is True
    r["MD-4b_api_version_removal_behavior_known"] = d.get("api_version_removal_400_and_earlier_nondefault_error_known") is True
    r["MD-4c_params_omitted_prompting_guides"] = d.get("deprecated_params_omitted_behavior_guided_by_prompting") is True
    r["MD-5a_retirement_calendar_not_fallback_chain"] = d.get("retirement_calendar_alerts_and_fallback_chain_not_treated_as_migration") is True
    r["MD-5b_tentative_dates_not_read_as_retirements"] = d.get("tentative_not_sooner_than_dates_not_misread_as_retirement_dates") is True
    r["MD-5c_migration_guides_and_support_path"] = d.get("migration_guides_followed_and_support_path_known") is True
    r["pass_count"] = sum(1 for v in r.values() if v is True)
    r["fail_count"] = sum(1 for v in r.values() if v is False)
    r["pass"] = r["fail_count"] == 0
    return r
if __name__ == "__main__":
    v = check(json.load(open(sys.argv[1])))
    print(json.dumps(v, indent=2)); sys.exit(0 if v["pass"] else 1)
