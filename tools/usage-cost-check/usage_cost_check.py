#!/usr/bin/env python3
"""usage-cost-check: deterministic gate for the USAGE AND COST ANALYTICS surface.
Stdlib only, offline, free. Canonical sources (read in full 2026-11-20):
Anthropic Claude Platform Docs "Usage and Cost Analytics API" (recommended)
https://platform.claude.com/docs/en/manage-claude/usage-cost-analytics-api
and "Usage and Cost API" (legacy)
https://platform.claude.com/docs/en/manage-claude/usage-cost-api
Key facts: Analytics API (beta) has GET /v1/organizations/analytics/usage
(token+request counts) and /analytics/cost (USD); every request needs the
anthropic-beta: analytics-usage-cost-2026-08-24 header plus anthropic-version,
with an Admin API key (Console orgs) or Analytics API key (Enterprise orgs) -
never a standard API key. Rows are period (starting_at/ending_at) + group +
usage/cost; a dimension is null unless grouped (group_by[] up to 5), each
combination appears exactly once, no-usage combinations have no row. Rows are
ranked by order_by across the whole range; a time series needs
time_bucket_width + order_by=time and zero-filling of empty buckets. Filters
use bracket notation (up to 100 values; OR within a filter, AND across
filters) and are independent of grouping; an unknown ID or model name matches
nothing instead of erroring (rbac_group_id is the exception). Actor is the
user, service account, federated identity, or the API key itself; keyless,
WIF and Managed Agents (svac_...) usage can carry api_key_id null / actor
null. A Console default workspace has its own real wrkspc_ ID (List
Workspaces needs include_default=true); legacy reported it as null.
Ranges: starting_at on/after 2026-01-01 and within 365 days, at most 31 days
per request, ending_at required with time_bucket_width, 1m spans at most
24h; both ends round down to the UTC bucket (or hour). Freshness: every
response carries data_refreshed_at; data typically refreshes within 4h, can
take 24h, and values can be revised until about 7 days after month end -
final totals only from months ended at least 7 days ago; all pages of a
query read one snapshot. Legacy differs: data in ~5 minutes, polling once
per minute sustained, buckets oldest-first including empty ones, top 100
groups per bucket, limit counts buckets. Cost rows: amount is a decimal
string in cents with six decimals (after discounts, before credits) plus
list_amount at list prices; parse as decimal, never float. cost_type and
token_type are extra cost-only dimensions that do not count toward the
5-dimension limit and limit does not apply to them; requests is null on
those rows. Coverage blind spots: Priority Tier cost is absent from the
legacy cost report, code execution is absent from the legacy usage report
(it appears in Analytics usage with model null), and for Enterprise orgs
the legacy usage endpoint omits Cowork, Claude Code and chat usage while
its cost endpoint (from 2025-10-01) covers usage-based charges but not
seat fees. The billed cost report is the authority: response-side token
counting and usage-derived estimates are reconciled against it, never
double-counted. Exit 0 = all pass, 1 = any fail. null/unverified = fail."""
import json, sys
def check(d):
    r = {}
    r["UA-0a_surface_decided"] = d.get("decided") is True
    r["UA-0b_owner_and_source"] = bool(d.get("owner")) and bool(d.get("source"))
    r["UA-0c_spend_surfaces_inventoried"] = d.get("spend_surfaces_inventoried") is True
    r["UA-1a_key_type_per_org"] = d.get("admin_or_analytics_key_per_org_type_not_standard_key") is True
    r["UA-1b_beta_and_version_headers"] = d.get("beta_header_analytics_2026_08_24_and_version_on_every_request") is True
    r["UA-1c_analytics_endpoints"] = d.get("analytics_usage_and_cost_endpoints_used") is True
    r["UA-2a_row_shape"] = d.get("row_shape_period_group_metrics_handled") is True
    r["UA-2b_null_unless_grouped"] = d.get("dimensions_null_unless_grouped_semantics_handled") is True
    r["UA-2c_time_series_order_and_zero_fill"] = d.get("time_series_uses_order_by_time_and_zero_fills_empty_buckets") is True
    r["UA-3a_actor_semantics"] = d.get("actor_semantics_incl_keyless_wif_managed_nulls_handled") is True
    r["UA-3b_filter_logic"] = d.get("filter_bracket_or_within_and_across_up_to_100_unknown_matches_nothing") is True
    r["UA-3c_default_workspace_real_id"] = d.get("default_workspace_real_id_and_include_default_handled") is True
    r["UA-4a_range_limits"] = d.get("range_limits_since_2026_365d_31d_ending_required_1m_24h") is True
    r["UA-4b_bucket_rounding_utc"] = d.get("range_ends_rounded_down_to_utc_bucket") is True
    r["UA-4c_freshness_and_coverage"] = d.get("data_refreshed_at_gated_revisions_7d_and_coverage_blindspots_known") is True
    r["UA-5a_money_decimal_cents"] = d.get("cost_amount_decimal_cents_6dp_amount_vs_list_amount") is True
    r["UA-5b_extra_cost_dimensions"] = d.get("cost_type_token_type_extra_dims_not_counted_requests_null") is True
    r["UA-5c_billed_authority"] = d.get("billed_cost_report_is_authority_estimates_reconciled_never_double_counted") is True
    r["pass_count"] = sum(1 for v in r.values() if v is True)
    r["fail_count"] = sum(1 for v in r.values() if v is False)
    r["pass"] = r["fail_count"] == 0
    return r
if __name__ == "__main__":
    v = check(json.load(open(sys.argv[1])))
    print(json.dumps(v, indent=2)); sys.exit(0 if v["pass"] else 1)
