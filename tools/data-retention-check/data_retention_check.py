#!/usr/bin/env python3
"""data-retention-check: deterministic gate for the API AND DATA RETENTION surface.
Stdlib only, offline, free. Canonical source (read in full 2026-11-20):
Anthropic Claude Platform Docs "API and data retention"
https://platform.claude.com/docs/en/manage-claude/api-and-data-retention
Key facts: the page covers platforms where Anthropic is the data processor
(first-party API, Claude Platform on AWS, Claude Models on Google Cloud
Anthropic managed, Claude in Microsoft Foundry); on Bedrock and Google
Cloud (Google managed) the cloud provider is the processor. Commitments:
retained data is never used for model training without express permission;
only what is technically necessary is retained; conversation content is not
retained by default, except Covered Models which require 30-day retention;
retention is purged on the shortest practical TTL. Outside the arrangements:
the Compliance API follows its own retention model, the Activity Feed
retains data for 6 years, local session transcripts are stored 6 years by
default or the org custom conversation period, remote session transcripts
have no default period, the Compliance API does not capture local sessions
under ZDR, and under HIPAA readiness it captures Cowork and Claude Code
local sessions only, for 30 days. ZDR: Anthropic does not store customer
prompts or responses at rest after the API response is returned; requested
via sales, enabled per organization, each new organization separately, no
automatic extension to other orgs under the same account. ZDR orgs cannot
call the API directly from a browser (CORS rejected; use your own backend).
ZDR covers Messages and Token Counting APIs for eligible features, Claude
Code with API keys from a Commercial organization (metrics logging data is
exempted and may be retained), and Claude Platform on AWS / Claude Models
on Google Cloud (Anthropic managed) on request. ZDR does not cover the
Console (incl. playground), consumer plans, Teams/Enterprise product
interfaces (Claude Code on Claude Enterprise has a separate ZDR offering),
or Claude for Excel. Managed Agents is stateful: session transcripts
persist until you delete them; self-hosted Managed Agents is the exception
(you store transcripts yourself). Third-party integrations are not covered.
Under ZDR, "No" features are NOT blocked: using one steps outside the
arrangement for that data and the feature's own retention applies (Batch
29 days, Files until deleted or expiry, code execution / programmatic tool
calling up to 30 days); No features are typically stateful. Covered Models
(Fable 5.2, Mythos 5.2, Fable 5.1, Mythos 5.1, Fable 5, Mythos 5) require
30-day retention and are not available under ZDR unless expressly
authorized; a request from an org whose retention configuration does not
meet the requirement returns 400 invalid_request_error; the requirement
applies wherever the models are offered (on Bedrock / Google Agent
Platform the retained data stays in the provider environment). A ZDR org
can enable 30-day retention for one specific non-default workspace only;
other workspaces keep ZDR and the Default Workspace always follows the
organization setting. HIPAA readiness: signed BAA plus a HIPAA-enabled
organization; it applies broader safeguards (encryption, access controls,
audit logging) rather than immediate deletion, so a PHI-handling org uses
HIPAA readiness and does not also need ZDR; enablement is permanent and
cannot be disabled; self-serve via Console with the standard BAA (bound to
the exact downloaded version) or a negotiated BAA via the account team.
HIPAA does not cover consumer products, processing PHI through the Console
interface, partner-operated platforms, Claude Platform on AWS, third-party
integrations, Claude Code, or beta features unless explicitly listed.
Under HIPAA the API BLOCKS requests containing a "No" feature with a 400
error listing the non-eligible features; client-side tools marked as not
blocked are accepted but remain outside HIPAA readiness. PHI appears in
message content, attached files, and file names/metadata; workspace names,
user info, billing data and support tickets are not expected to contain PHI.
PHI must never be included in JSON schema definitions (property names,
enum values, const values, pattern regexes) because strict structured
outputs / strict tools compile schemas into grammars cached separately
from message content (schema cached up to 24 hours since last use) without
the same PHI protections; patient-specific data belongs only in message
content. Eligibility values: Yes = fully eligible (for ZDR, assuming a
non-Covered model); Yes (qualified) = prompts/outputs not stored but a
bounded technical artifact is retained briefly (prompt caching holds KV
representations and hashes in memory for the cache TTL; structured outputs
cache only the schema; cache diagnostics retains a fingerprint of hashes
and token estimates); No = not eligible. Retention regardless of
arrangement: even with ZDR or HIPAA, Anthropic may retain data where
required by law or flagged by automated trust and safety systems; flagged
inputs and outputs may be retained for up to 2 years.
Exit 0 = all pass, 1 = any fail. null/unverified = fail."""
import json, sys
def check(d):
    r = {}
    r["AR-0a_surface_decided"] = d.get("decided") is True
    r["AR-0b_owner_and_source"] = bool(d.get("owner")) and bool(d.get("source"))
    r["AR-0c_processor_scope_distinguished"] = d.get("anthropic_processor_vs_provider_processor_scope_distinguished") is True
    r["AR-1a_no_training_without_permission"] = d.get("retained_data_never_trained_without_express_permission_known") is True
    r["AR-1b_conversation_not_retained_except_covered"] = d.get("conversation_not_retained_by_default_except_covered_models_30d_known") is True
    r["AR-1c_outside_models_known"] = d.get("outside_models_compliance_api_activity_feed_6y_local_6y_remote_none_hipaa_local_30d_known") is True
    r["AR-2a_zdr_definition_per_org"] = d.get("zdr_no_store_at_rest_after_response_per_org_via_sales_no_auto_extend_known") is True
    r["AR-2b_zdr_cors_rejected_backend_only"] = d.get("zdr_org_cors_rejected_backend_only_known") is True
    r["AR-2c_zdr_covers_messages_claudecode_cloud"] = d.get("zdr_covers_messages_token_counting_claude_code_commercial_metrics_exempt_aws_google_managed_on_request_known") is True
    r["AR-3a_zdr_exclusions_console_consumer_enterprise_excel"] = d.get("zdr_excludes_console_consumer_teams_enterprise_ui_excel_cc_enterprise_separate_known") is True
    r["AR-3b_managed_agents_excluded_selfhosted_exception"] = d.get("managed_agents_stateful_transcripts_until_deleted_selfhosted_exception_known") is True
    r["AR-3c_zdr_no_features_not_blocked_stateful"] = d.get("zdr_no_features_not_blocked_own_retention_applies_batch29_files_codeexec30_known") is True
    r["AR-4a_covered_models_30d_400"] = d.get("covered_models_fable_mythos_5_51_52_require_30d_400_on_noncompliant_known") is True
    r["AR-4b_workspace_carveout_nondefault_only"] = d.get("zdr_org_30d_carveout_one_nondefault_workspace_only_default_follows_org_known") is True
    r["AR-4c_hipaa_blocks_no_features_400"] = d.get("hipaa_blocks_no_features_400_listing_them_client_side_not_blocked_exception_known") is True
    r["AR-5a_hipaa_arrangement_permanent"] = d.get("hipaa_baa_enabled_org_broader_safeguards_not_zdr_permanent_console_or_negotiated_known") is True
    r["AR-5b_phi_never_in_schema_definitions"] = d.get("phi_never_in_schema_names_enum_const_pattern_grammar_cached_24h_message_content_only_known") is True
    r["AR-5c_regardless_flagged_2y_eligibility_semantics"] = d.get("retention_regardless_flagged_legal_up_to_2y_and_yes_qualified_no_semantics_known") is True
    r["pass_count"] = sum(1 for v in r.values() if v is True)
    r["fail_count"] = sum(1 for v in r.values() if v is False)
    r["pass"] = r["fail_count"] == 0
    return r
if __name__ == "__main__":
    v = check(json.load(open(sys.argv[1])))
    print(json.dumps(v, indent=2)); sys.exit(0 if v["pass"] else 1)
