#!/usr/bin/env python3
"""spend-limits-check: deterministic gate for the SPEND LIMITS API surface.
Stdlib only, offline, free. Canonical source (read in full 2026-11-20):
Anthropic Claude Platform Docs "Spend Limits API"
https://platform.claude.com/docs/en/manage-claude/spend-limits-api (287 lines)
Key facts: 8 endpoints, 2 resources. Spend limits: GET effective, GET {id},
POST (set per-user override), DELETE {id}. Increase requests: GET list,
GET {id}, POST {id}/approve, POST {id}/deny. Prerequisites: Claude
Enterprise plan AND usage credits turned on (primary owner turns them on in
claude.ai billing settings). SDK client.beta.organization.spend_limits;
CLI ant beta:organization:spend-limits; both send anthropic-version; key
from ANTHROPIC_API_KEY; SDK/CLI auto-paginate (limit = page size).
Hierarchy: per-user override > rbac_group > seat_tier > organization
default; group limit is a per-member default, NOT a pooled budget. GET
effective returns every current member + resolved limit + source + period-
to-date spend. source in {user, seat_tier, rbac_group, organization};
scope types are an OPEN set (fall through on unknown). period: monthly
only today, resets 00:00 UTC on the 1st; a limit is identified by
(scope, period); period is also an open set. Amounts: decimal strings in
MINOR units (cents for USD), "50000" = $500.00; parse as decimal, divide
by 100, avoid binary float. amount null = unlimited in an effective row;
"0" = cannot use Claude beyond included usage; on a configured row null
only means no numeric limit set (read the effective row to distinguish).
period_to_date_spend may carry a fraction and may read "0" when the
reading is temporarily unavailable: informational, not transactional.
Increase requests are created ONLY by a member clicking "Request more
usage" in claude.ai, never via this API. Statuses pending / approved /
denied; approved and denied are terminal; at most one pending per member;
after a denial the member can re-request immediately (only pending blocks);
an admin can still raise the limit directly at any time. Pending normally
carries a live spend_summary (may be null); resolved rows have null
spend_summary. Approving writes the SAME per-user row POST spend_limits
writes, at an admin-supplied amount (the request carries no amount).
Setting a limit directly does NOT transition a pending request. Default:
Anthropic emails the member on approve/deny; suppress_notification:true
suppresses it. Scopes: read:spend_limits for reads, write:spend_limits
for writes. All 8 endpoints share ONE per-org limit of 60 req/min; over
returns 429. Pagination: opaque cursor, pass next_page unchanged as page
until null; DO NOT change query params mid-sequence (cursor is bound to
its filters; mismatch = 400 "cursor does not match current query
parameters"; restart from page 1). List params use bracket notation.
Errors follow the standard shape; quote request_id to support. POST set
is an upsert keyed on (scope, period) and accepts ONLY scope.type "user"
(seat-tier/group/org defaults live in claude.ai settings). DELETE removes
only a per-user override; member falls back to inherited default, or
unlimited if none exists at any level. Deny is idempotent on denied
(re-deny returns 200 with the existing resource) and REJECTS denying an
already-approved request. Workflows: sweep with the Usage and Cost
Analytics cost endpoint first (needs read:analytics; one combined Admin
key can hold every scope, selected by the primary owner), then read caps
via /effective; flag period_to_date_spend/amount at a threshold (example
80%); a "0" cap is already at-limit; there is NO server-side ratio filter.
Rapid-change: per-member daily cost, trailing 2 weeks, recent 7d vs prior
7d, flag at a multiple (example 3x); recent cost can still change, so pin
ending_at at/before a seen data_refreshed_at. Incident: raise gated on a
live incident ID with the member assigned; record the prior cap first;
roll back on close (restore the recorded limit, or DELETE if there was
none) and remove any temporary group membership. Reporting (Analytics /
Usage and Cost Analytics) is a separate surface. Exit 0 = all pass,
1 = any fail. null/unverified = fail."""
import json, sys
def check(d):
    r = {}
    r["SL-0a_surface_decided"] = d.get("decided") is True
    r["SL-0b_owner_and_source"] = bool(d.get("owner")) and bool(d.get("source"))
    r["SL-0c_prereqs_enterprise_and_usage_credits_primary_owner"] = d.get("prereqs_enterprise_plan_usage_credits_on_primary_owner_enables_in_claude_ai_billing_known") is True
    r["SL-1a_eight_endpoints_two_resources"] = d.get("eight_endpoints_spend_limits_effective_get_post_delete_and_requests_list_get_approve_deny_known") is True
    r["SL-1b_scopes_read_write_spend_limits"] = d.get("scopes_read_spend_limits_for_reads_write_spend_limits_for_writes_known") is True
    r["SL-1c_sdk_cli_key_and_shared_60rpm_429"] = d.get("sdk_client_beta_organization_spend_limits_ant_cli_beta_spend_limits_version_header_key_env_all_eight_share_60_per_min_429_known") is True
    r["SL-2a_hierarchy_override_group_seattier_org_not_pooled"] = d.get("hierarchy_user_override_then_rbac_group_then_seat_tier_then_organization_group_limit_is_per_member_not_pooled_known") is True
    r["SL-2b_effective_read_source_open_set"] = d.get("effective_returns_all_members_resolved_limit_source_period_to_date_source_values_user_seat_tier_rbac_group_organization_scope_types_open_set_fallthrough_known") is True
    r["SL-2c_period_monthly_reset_identity_open_set"] = d.get("period_monthly_only_resets_0000_utc_first_limit_identified_by_scope_period_pair_period_open_set_known") is True
    r["SL-3a_amounts_minor_units_decimal"] = d.get("amounts_decimal_strings_minor_units_cents_50000_is_500_parse_decimal_divide_100_avoid_binary_float_known") is True
    r["SL-3b_null_vs_zero_semantics"] = d.get("amount_null_unlimited_in_effective_row_zero_means_included_usage_only_configured_row_null_means_no_numeric_limit_read_effective_to_distinguish_known") is True
    r["SL-3c_period_spend_informational_fraction_zero_unavailable"] = d.get("period_to_date_spend_may_be_fractional_may_read_zero_when_unavailable_informational_not_transactional_known") is True
    r["SL-4a_request_origin_and_lifecycle"] = d.get("requests_created_only_by_member_click_in_claude_ai_never_via_api_statuses_pending_approved_denied_terminal_at_most_one_pending_denied_can_rerequest_immediately_known") is True
    r["SL-4b_spend_summary_live_pending_null_resolved"] = d.get("pending_request_normally_carries_live_spend_summary_may_be_null_resolved_summary_null_known") is True
    r["SL-4c_approve_writes_override_direct_set_does_not_resolve_notification"] = d.get("approve_writes_same_per_user_row_at_admin_supplied_amount_request_carries_no_amount_direct_set_does_not_transition_pending_default_email_suppress_notification_true_known") is True
    r["SL-5a_pagination_cursor_bound_bracket_errors"] = d.get("pagination_opaque_cursor_next_page_unchanged_until_null_params_frozen_mid_sequence_mismatch_400_restart_bracket_notation_standard_errors_quote_request_id_known") is True
    r["SL-5b_upsert_user_only_delete_fallback_deny_rules"] = d.get("post_upsert_scope_period_user_scope_only_defaults_in_claude_ai_settings_delete_only_override_fallback_or_unlimited_deny_idempotent_on_denied_rejects_deny_on_approved_known") is True
    r["SL-5c_workflows_sweep_ratio_rapid_incident_rollback_separate_reporting"] = d.get("workflows_cost_sweep_then_effective_ratio_flag_example_80pct_zero_cap_at_limit_no_server_filter_rapid_7v7_example_3x_pin_data_refreshed_incident_live_id_record_prior_rollback_restore_or_delete_remove_group_reporting_separate_known") is True
    r["pass_count"] = sum(1 for v in r.values() if v is True)
    r["fail_count"] = sum(1 for v in r.values() if v is False)
    r["pass"] = r["fail_count"] == 0
    return r
if __name__ == "__main__":
    v = check(json.load(open(sys.argv[1])))
    print(json.dumps(v, indent=2)); sys.exit(0 if v["pass"] else 1)
