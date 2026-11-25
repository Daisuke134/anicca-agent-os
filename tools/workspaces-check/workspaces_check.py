#!/usr/bin/env python3
"""workspaces-check: deterministic gate for the WORKSPACES surface.
Stdlib only, offline, free. Canonical source (read in full 2026-11-20):
Anthropic Claude Platform Docs "Workspaces"
https://platform.claude.com/docs/en/manage-claude/workspaces (328 lines)
Key facts: workspaces organize API usage inside one organization -
separate projects, environments, or teams - while billing and
administration stay centralized. Workspace IDs use the wrkspc_ prefix.
Max 100 workspaces per organization by default; archived workspaces do
not count; contact the account team for more. Every organization has a
Default Workspace that cannot be renamed, archived, or deleted; it has a
wrkspc_ ID like any other; List Workspaces includes it ONLY when
include_default=true; Get Workspace accepts its ID. Usage and Cost
Analytics reports Default usage/cost under that ID, while the legacy
Usage and Cost API reports null workspace_id for it; an API key bound to
the Default Workspace carries that ID in its scope field. Workspace
roles: User (playground only), Limited Developer (create/manage API
keys, use the API, with Console-only limits), Developer (create/manage
API keys, use the API), Admin (full control over workspace settings and
members), Billing (view workspace billing; inherited from the org
billing role). Limited Developer's limits apply ONLY to the Console
interface, not the API: in the Console they cannot open or start
Managed Agents sessions, open memory stores, or manage deployments, and
cannot download or delete files on the Files page. Inheritance: org
admins automatically get Workspace Admin on ALL workspaces; org billing
members automatically get Workspace Billing on ALL; org users and
developers must be explicitly added to each workspace. Service accounts
are added via the Service accounts page (Add to workspace); filter that
list by workspace to see a workspace's accounts. Claude Code workspace:
auto-created when the first org member signs in to Claude Code with a
Claude Console account; every later member who signs in is auto-added.
Claude Code mints a per-user API key in this workspace at sign-in; keys
cannot be created in it manually from the Console; a Claude Code key
STOPS working if its owner is removed from the workspace or the
organization, unlike a workspace key. Claude Code usage is rate-limited
separately and admins can cap its share of the org limits; it is the
ONLY workspace that supports per-user monthly spend limits. Resource
scoping: apart from organization-level requests (such as Admin API
requests), every request runs in exactly one workspace and can only
access resources within it. A workspace key (legacy key without an
owner) belongs to the workspace it was created in and always runs
there. A personal or service account key scoped to a single workspace
always runs there; an unscoped one runs in the workspace named by each
request's anthropic-workspace-id header, and the account must have
access to that workspace. Workspace-scoped resources: Files (Files
API), Message Batches (Batch API), Skills (Skills API). MCP tunnels are
managed differently: with a workspace:manage_tunnels OAuth token from
Workload Identity Federation, NOT an API key; tunnels are created in a
workspace; the Console MCP tunnels list and the Managed Agents MCP
server picker show tunnels in the current workspace only; the cap of 10
active tunnels is organization-wide; in the Console, managing tunnels
requires the admin organization role (org developers can view, not
change). Workspaces themselves and organization members are managed at
the organization level through the Admin API (Admin API key, org:admin
OAuth token, or a personal/service account key not scoped to a specific
workspace). Management: Console Workspaces page (create = name + color;
edit details; archive via More actions) or the Admin API (SDK
client.organization.workspaces; key read from ANTHROPIC_API_KEY env;
workspace members add / update role / remove via the Workspace Members
API). Member-removal trap: on the Members page, select the workspace in
the Workspace dropdown first - if it shows All, Remove member removes
the member from the ORGANIZATION instead. Archiving preserves
historical data for reporting, deactivates the workspace, archives
EVERY API key created for it, and CANNOT be undone. Identification:
Claude API responses carry an anthropic-workspace-id header (alongside
request-id and anthropic-organization-id) with the resolved workspace's
wrkspc_ ID, including for the Default Workspace; the header is ABSENT
when the credential does not resolve to a workspace (for example Admin
API requests) or when the request fails before authentication completes
(such as a 401). Uses: confirm which workspace's usage, cost, and rate
limits a request counted toward; match against workspace_id in Usage
and Cost Analytics rows and against the scope field of API keys in the
Admin API; check Default by passing the ID to Get Workspace (name comes
back "Default"). Workspace limits can keep a workspace BELOW the
organization's limits but cannot raise them: spend limits cap monthly
spending per workspace (Console Spend limits page, Workspace limits;
email alerts at a chosen amount when Anthropic bills the org directly);
rate limits cap RPM / input TPM / output TPM per workspace and model
(Console Rate limits page); the Rate Limits API stores a value above
the org limit but still enforces the LOWER of the two. Caveat: a spend
limit on the Default Workspace might not count or stop some usage in
it - Console usage such as playground, Claude Managed Agents sessions,
and Claude Code / Claude Desktop usage when a member signs in with a
Claude Console account - while the organization's spend limit applies
to ALL of that usage. Usage and costs are tracked per workspace with
the Usage and Cost Analytics API. Separate surfaces: Admin API itself
(admin-api-check), workspace spend limits as an API (spend-limits-check
covers the member-level API; the Console workspace-limit rows are
referenced there as out of scope), rate limits themselves
(rate-limits-check), data residency's workspace geo at creation
(data-residency-check). Exit 0 = all pass, 1 = any fail.
null/unverified = fail."""
import json, sys
def check(d):
    r = {}
    r["WS-0a_surface_decided"] = d.get("decided") is True
    r["WS-0b_owner_and_source"] = bool(d.get("owner")) and bool(d.get("source"))
    r["WS-0c_purpose_organize_usage_centralized_billing_admin"] = d.get("purpose_separate_projects_environments_teams_centralized_billing_and_administration_known") is True
    r["WS-1a_id_prefix_max_100_archived_excluded"] = d.get("ids_wrkspc_prefix_max_100_per_org_default_archived_do_not_count_contact_account_team_for_more_known") is True
    r["WS-1b_default_unrenamable_unarchivable_list_include_default_get_accepts"] = d.get("default_workspace_cannot_be_renamed_archived_or_deleted_has_wrkspc_id_list_includes_only_with_include_default_true_get_workspace_accepts_it_known") is True
    r["WS-1c_default_reporting_analytics_id_legacy_null_key_scope"] = d.get("default_usage_cost_analytics_reports_under_its_id_legacy_usage_cost_api_reports_null_workspace_id_key_bound_to_default_carries_id_in_scope_known") is True
    r["WS-2a_five_roles_permissions"] = d.get("roles_user_playground_only_limited_developer_keys_api_with_console_limits_developer_keys_api_admin_full_billing_view_inherited_known") is True
    r["WS-2b_inheritance_admins_billing_all_explicit_others_service_accounts"] = d.get("org_admins_get_workspace_admin_all_org_billing_get_workspace_billing_all_org_users_developers_explicit_per_workspace_service_accounts_added_via_service_accounts_page_known") is True
    r["WS-2c_limited_developer_console_only_limits"] = d.get("limited_developer_limits_console_interface_only_not_api_no_managed_agents_sessions_memory_stores_deployments_no_files_download_delete_in_console_known") is True
    r["WS-3a_claude_code_workspace_auto_created_auto_added"] = d.get("claude_code_workspace_auto_created_on_first_member_signin_with_console_account_later_signins_auto_added_known") is True
    r["WS-3b_claude_code_key_minted_no_manual_stops_on_removal"] = d.get("claude_code_mints_per_user_key_at_signin_no_manual_key_creation_in_console_key_stops_if_owner_removed_from_workspace_or_org_unlike_workspace_key_known") is True
    r["WS-3c_claude_code_separate_rate_limits_only_per_user_spend_limits"] = d.get("claude_code_usage_rate_limited_separately_admins_cap_share_of_org_limits_only_workspace_supporting_per_user_monthly_spend_limits_known") is True
    r["WS-4a_exactly_one_workspace_workspace_key_fixed"] = d.get("apart_from_org_level_requests_every_request_runs_in_exactly_one_workspace_access_only_its_resources_workspace_key_legacy_no_owner_always_runs_in_creation_workspace_known") is True
    r["WS-4b_personal_service_key_scoping_header_access"] = d.get("personal_or_service_key_single_workspace_always_there_unscoped_runs_in_anthropic_workspace_id_request_header_workspace_account_must_have_access_known") is True
    r["WS-4c_scoped_resources_tunnels_exception_org_level_management"] = d.get("scoped_resources_files_message_batches_skills_tunnels_via_wif_workspace_manage_tunnels_token_not_api_key_created_in_workspace_lists_current_workspace_only_cap_10_active_org_wide_console_tunnel_mgmt_org_admin_developers_view_only_workspaces_and_members_managed_org_level_admin_api_known") is True
    r["WS-5a_admin_api_and_console_management_member_removal_trap"] = d.get("manage_via_console_workspaces_page_name_color_or_admin_api_sdk_client_organization_workspaces_key_env_members_add_update_role_remove_removal_trap_select_workspace_dropdown_or_all_removes_from_org_known") is True
    r["WS-5b_archive_preserves_deactivates_archives_keys_irreversible"] = d.get("archive_preserves_historical_data_deactivates_workspace_archives_every_api_key_created_for_it_cannot_be_undone_known") is True
    r["WS-5c_response_header_identification_limits_lower_only_default_caveat"] = d.get("responses_carry_anthropic_workspace_id_header_incl_default_absent_when_credential_resolves_to_no_workspace_or_auth_fails_401_match_analytics_workspace_id_and_key_scope_get_workspace_name_default_limits_lower_only_never_raise_rate_limits_api_enforces_lower_of_two_default_spend_limit_may_miss_console_managed_agents_claude_code_desktop_usage_org_limit_covers_all_known") is True
    r["pass_count"] = sum(1 for v in r.values() if v is True)
    r["fail_count"] = sum(1 for v in r.values() if v is False)
    r["pass"] = r["fail_count"] == 0
    return r
if __name__ == "__main__":
    v = check(json.load(open(sys.argv[1])))
    print(json.dumps(v, indent=2)); sys.exit(0 if v["pass"] else 1)
