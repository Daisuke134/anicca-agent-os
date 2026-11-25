#!/usr/bin/env python3
"""admin-api-check: deterministic gate for the ADMIN API / organization
administration surface. Stdlib only, offline, free. Canonical source (read
in full 2026-11-20): Anthropic Claude Platform Docs "Admin API"
https://platform.claude.com/docs/en/manage-claude/admin-api (220 lines)
Key facts: Admin API manages org members/roles, invites, workspaces and
their members, and API keys programmatically instead of by hand in the
Console. Availability: Claude Console and Claude Enterprise organizations
only; NOT claude.ai Team plan, NOT individual Console accounts (an
individual must first set up an organization in Console Settings ->
Organization). Enterprise (claude.ai) orgs use a scoped key created in
claude.ai and, from this page, only members/invites/organization-info
endpoints apply; they also get Usage and Cost Analytics API (beta) and
legacy Usage and Cost API (both need read:analytics scope), Enterprise-only
groups/custom-role reads and Spend Limits API, and beta Plugins and Claude
Tag APIs. On Claude Platform on AWS only workspace endpoints
(/v1/organizations/workspaces create/get/list/update/archive), external
key endpoints for CMEK (/v1/organizations/external_keys; NO validate
endpoint - keys are validated when attached to a workspace), telemetry
destination endpoints, and Usage and Cost Analytics endpoints are
available; members, workspace members, invites, API keys, legacy Usage
and Cost API, and rate limit reports are NOT available on AWS.
Authentication accepts three credentials: (1) Admin API key
(sk-ant-admin...) in x-api-key, provisionable only by a member with the
admin role; (2) OAuth bearer token with org:admin scope in Authorization
Bearer, obtainable only by users/service accounts with the admin role
(owners/primary owners included in the wider doc set); (3) a personal key
or service account key NOT scoped to a specific workspace, in x-api-key,
carrying the same permissions as the linked account. An Admin API key
covers most endpoints, but service-account, federation-issuer, and
federation-rule endpoints accept ONLY an org:admin OAuth token. SDK
exposes client.organization; ant CLI exposes ant organization; the
default client reads ANTHROPIC_API_KEY (Admin key) or
ANTHROPIC_AUTH_TOKEN (OAuth bearer).
OAuth hygiene: log in with ant CLI under a dedicated admin profile; the
exported ANTHROPIC_AUTH_TOKEN applies to EVERY SDK/CLI call in that shell,
so use a shell reserved for administration, unset the variable when done,
and switch back with ant profile activate default. Interactive tokens are
short-lived: on 401 rerun the export to refresh. Leave ANTHROPIC_API_KEY
UNSET in the same shell so the bearer is actually sent. An org:admin token
grants access to the WHOLE organization regardless of the workspace the
profile/federation rule is bound to. Automated/CI workloads skip
interactive login and mint the token via Workload Identity Federation.
Resources: org members and roles, org invites, workspaces and workspace
members, API keys, plus service accounts (svac_...), federation issuers
(fdis_...), federation rules (fdrl_...) (OAuth only). Common uses:
automating onboarding/offboarding, managing workspace access, auditing
API keys. Console org roles (5): user = playground; claude_code_user =
playground + Claude Code; developer = playground + manage API keys;
billing = playground + manage billing details; admin = all preceding +
manage users. Owners/primary owners have all admin permissions and can
also manage admins; Enterprise orgs have a different role set including
owners and a primary owner.
API keys: each key response includes expires_at (null = no expiration)
and principal - user_actor {user_id} for a personal key,
service_account_actor {service_account_id} for a service account key,
null for a workspace key - and a scope object: {type: workspace,
workspace_id: wrkspc_...} or {type: organization}. Filtering the key list
by workspace_id with the Default Workspace ID returns ONLY keys bound to
the Default Workspace; organization-scoped keys are not returned under
ANY workspace_id filter. Org info: GET /v1/organizations/me returns the
organization the credential belongs to. Adjacent APIs are separate
surfaces: Usage and Cost Analytics API (legacy Usage and Cost API is the
legacy one), Claude Code Analytics API, Rate Limits API (read org and
workspace limits, set workspace limits), Compliance API (Admin API keys
can read ONLY the Activity Feed; full access needs separate setup),
organization webhooks (enforcement-action events on user profiles).
Best practices: meaningful names/descriptions for workspaces and API
keys; handle errors from failed operations; regularly audit member roles
and permissions; archive unused workspaces and delete pending invites no
longer needed; monitor API key usage, audit each key's expires_at, and
rotate keys periodically. WIF itself is the wif-check surface; rate
limits themselves are the rate-limits-check surface. Exit 0 = all pass,
1 = any fail. null/unverified = fail."""
import json, sys
def check(d):
    r = {}
    r["AA-0a_surface_decided"] = d.get("decided") is True
    r["AA-0b_owner_and_source"] = bool(d.get("owner")) and bool(d.get("source"))
    r["AA-0c_availability_console_enterprise_not_team_individual_org_setup_first"] = d.get("availability_console_enterprise_only_not_team_not_individual_setup_org_first_known") is True
    r["AA-1a_three_credentials_admin_key_oauth_personal_service_unscoped"] = d.get("three_credentials_admin_key_sk_ant_admin_x_api_key_oauth_org_admin_bearer_personal_or_service_key_unscoped_same_permissions_known") is True
    r["AA-1b_admin_key_provision_admin_only_oauth_only_endpoints"] = d.get("admin_key_provisioned_only_by_admin_role_service_federation_endpoints_oauth_only_known") is True
    r["AA-1c_oauth_shell_hygiene_dedicated_profile_unset_key_unset_401_refresh_orgwide_wif_ci"] = d.get("oauth_dedicated_profile_shell_wide_unset_when_done_api_key_unset_shortlived_401_rerun_export_orgwide_token_wif_for_ci_known") is True
    r["AA-2a_console_five_roles_permissions"] = d.get("console_five_roles_user_claude_code_user_developer_billing_admin_permissions_known") is True
    r["AA-2b_owners_superset_enterprise_different"] = d.get("owners_primary_owners_all_admin_plus_manage_admins_enterprise_role_set_differs_known") is True
    r["AA-2c_sdk_cli_surface_and_env_reads"] = d.get("sdk_client_organization_ant_cli_ant_organization_default_client_reads_api_key_or_auth_token_known") is True
    r["AA-3a_resources_and_uses"] = d.get("resources_members_invites_workspaces_members_api_keys_service_federation_ids_uses_onoffboarding_access_audit_known") is True
    r["AA-3b_aws_subset_and_exclusions_cmek_no_validate"] = d.get("aws_only_workspaces_external_keys_no_validate_telemetry_analytics_members_invites_keys_legacy_ratelimit_reports_excluded_known") is True
    r["AA-3c_enterprise_scope_and_adjacent_apis"] = d.get("enterprise_scoped_key_members_invites_orginfo_only_analytics_read_scope_groups_spend_plugins_tag_compliance_activity_feed_only_webhooks_known") is True
    r["AA-4a_key_expires_at_and_principal_types"] = d.get("key_expires_at_null_means_none_principal_user_actor_service_account_actor_null_workspace_known") is True
    r["AA-4b_key_scope_and_default_filter_trap"] = d.get("key_scope_workspace_or_organization_default_workspace_filter_returns_only_bound_keys_org_scoped_never_under_filter_known") is True
    r["AA-4c_org_info_endpoint"] = d.get("org_info_get_v1_organizations_me_returns_credentials_org_known") is True
    r["AA-5a_audit_roles_archive_workspaces_delete_invites"] = d.get("regularly_audit_roles_archive_unused_workspaces_delete_unneeded_pending_invites_known") is True
    r["AA-5b_monitor_keys_audit_expiry_rotate_names_errors"] = d.get("monitor_key_usage_audit_expires_at_rotate_periodically_meaningful_names_descriptions_handle_errors_known") is True
    r["AA-5c_adjacent_surfaces_separate"] = d.get("adjacent_usage_cost_analytics_vs_legacy_claude_code_analytics_rate_limits_api_set_workspace_limits_wif_and_rate_limits_own_surfaces_known") is True
    r["pass_count"] = sum(1 for v in r.values() if v is True)
    r["fail_count"] = sum(1 for v in r.values() if v is False)
    r["pass"] = r["fail_count"] == 0
    return r
if __name__ == "__main__":
    v = check(json.load(open(sys.argv[1])))
    print(json.dumps(v, indent=2)); sys.exit(0 if v["pass"] else 1)
