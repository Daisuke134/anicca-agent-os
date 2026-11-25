#!/usr/bin/env python3
"""mgmt-check: deterministic gate for the IN-APP SUBSCRIPTION MANAGEMENT
surface (Settings -> manage subscription / Customer Center / billing-issue
fix path). Stdlib only, offline, free.
Sources (read in full 2026-11-15):
- RevenueCat Codelabs, "Recover Involuntary Churn: Billing Grace Periods
  & Customer Center (2026)"
  (revenuecat.github.io/codelabs/recover-involuntary-churn-billing-retry.html):
  the billing-issue signal is entitlement.isActive == true AND
  entitlement.billingIssueDetectedAt != null (a voluntary cancel instead
  sets unsubscribeDetectedAt); detection is checked on foreground and kept
  current via CustomerInfo updates so the banner disappears the moment
  payment recovers; the fix is one tap to Customer Center (recommended,
  requires a Pro or Enterprise plan, configured in the dashboard under
  Monetization Tools) or to customerInfo.managementURL, which can be null
  and must be guarded.
- RevenueCat, "Customer Center: Automate in-app subscription support"
  (revenuecat.com/blog/company/introducing-customer-center): the
  management screen shows billing cycle, current pricing and next billing
  date; default paths are Missing purchases (restore), Refund request,
  Change plans and Cancel (with a feedback prompt); users with no active
  subscription get a dedicated screen showing where they subscribed plus
  restore / support options; iOS 15+.
Exit 0 = PASS, 1 = FAIL.
Input JSON: {app,
 inventory:{surface_decided, dashboard_config_evidenced,
   plan_eligibility_verified},
 entry:{settings_entry_present, entry_visible_regardless_of_entitlement,
   entry_label_localized},
 status_truth:{status_summary_shown_before_opening,
   status_from_live_entitlement_fields,
   billing_issue_from_billing_issue_detected_at,
   voluntary_cancel_distinguished},
 fix_path:{billing_banner_present, banner_opens_management_path,
   banner_clears_on_recovery_via_updates, management_url_null_safe},
 paths:{management_paths_decided,
   non_subscriber_screen_decided},
 measurement:{management_opens_counted,
   billing_issue_funnel_counted}}
"""
import json, sys

def check(d):
    fails = []
    inv = d.get("inventory") or {}
    if not inv.get("surface_decided"):
        fails.append("MG-0 the management surface is not decided (Customer Center vs StoreKit showManageSubscriptions vs managementURL is a recorded choice; an undecided surface is a surface nobody owns)")
    if not inv.get("dashboard_config_evidenced"):
        fails.append("MG-0 the server/dashboard side of the management surface is not evidenced (a Customer Center view in code renders whatever the dashboard holds -- paths, offers, feedback prompts; without a dashboard readback the surface's actual contents are unknown)")
    if not inv.get("plan_eligibility_verified"):
        fails.append("MG-0 plan eligibility for the management surface is not verified (RevenueCat Customer Center requires a Pro or Enterprise plan; embedding the view without verifying the plan risks shipping an entry that opens an unconfigured or unavailable center)")
    en = d.get("entry") or {}
    if not en.get("settings_entry_present"):
        fails.append("MG-1 there is no subscription-management entry in Settings (a subscriber who wants to fix payment, change plan or cancel must dig through the store's Settings app -- the exact friction that produces 1-star 'could not cancel' reviews)")
    if not en.get("entry_visible_regardless_of_entitlement"):
        fails.append("MG-1 the management entry is hidden from some state that needs it (lapsed and non-subscribers also need the management screen -- it is where restore and 'where did I subscribe' live; gating it on current entitlement strands exactly the users trying to come back)")
    if not en.get("entry_label_localized"):
        fails.append("MG-1 the management entry label is not localized (the entry is a settings row every subscriber reads; a single-language label in a multi-locale app is a broken signpost)")
    st = d.get("status_truth") or {}
    if not st.get("status_summary_shown_before_opening"):
        fails.append("MG-2 no subscription status summary is shown before opening the management surface (plan, price and next billing/expiration date exist in the model but the settings row shows none of them; the user cannot tell what they have, what it costs or when it renews without opening a second surface and hoping it is configured)")
    if not st.get("status_from_live_entitlement_fields"):
        fails.append("MG-2 the displayed status does not come from live entitlement fields (willRenew / expirationDate / periodType read from the current CustomerInfo; a cached boolean or a hardcoded string will lie after a cancel, a renewal or a billing failure)")
    if not st.get("billing_issue_from_billing_issue_detected_at"):
        fails.append("MG-2 the billing-issue state is not derived from billingIssueDetectedAt (RevenueCat's contract: isActive AND billingIssueDetectedAt != null is the billing-retry signal. A status-string set that the CustomerInfo initializer never produces makes the billing-issue banner unreachable in production -- tested, rendered, and dead)")
    if not st.get("voluntary_cancel_distinguished"):
        fails.append("MG-2 a voluntary cancel is not distinguished from a billing issue (unsubscribeDetectedAt / willRenew=false means the user chose to leave -- value/win-back language; billingIssueDetectedAt means their card failed -- fix-payment language. Showing either group the other's message is a category error)")
    fp = d.get("fix_path") or {}
    if not fp.get("billing_banner_present"):
        fails.append("MG-3 there is no in-app billing-issue prompt (a subscriber in billing retry who opens the app and sees nothing will simply expire at the end of the grace window; the store's own prompt alone is not an in-app recovery path)")
    if not fp.get("banner_opens_management_path"):
        fails.append("MG-3 the billing-issue prompt does not open a management path in one tap (Customer Center or managementURL; a banner that only informs, with no one-tap route to update the payment method, converts awareness into nothing)")
    if not fp.get("banner_clears_on_recovery_via_updates"):
        fails.append("MG-3 the billing-issue prompt does not clear on recovery via CustomerInfo updates (the codelab contract: keep the check current on foreground and on CustomerInfo updates so the banner disappears the moment payment recovers; a stale banner trains users to ignore it)")
    if not fp.get("management_url_null_safe"):
        fails.append("MG-3 the management URL is not null-safe (managementURL is null when there is no active store subscription and unsupported for some stores; opening it unguarded crashes or dead-ends -- a fallback to the store subscriptions page is required)")
    pa = d.get("paths") or {}
    if not pa.get("management_paths_decided"):
        fails.append("MG-4 the management paths are not decided as a set (restore / refund request / change plans / cancel-with-feedback are separate paths with separate configuration; a lone 'cancel' link or an unexamined default set means refund and plan-change users hit a wall or an unintended offer)")
    if not pa.get("non_subscriber_screen_decided"):
        fails.append("MG-4 what a user with no active subscription sees on the management surface is not decided (RevenueCat's form: show where they subscribed, offer restore and a support contact; an undecided non-subscriber screen is a blank or a paywall where a recovery path should be)")
    me = d.get("measurement") or {}
    if not me.get("management_opens_counted"):
        fails.append("MG-5 management-surface opens are not counted (opens split by state -- entitled / billing-issue / lapsed; an uncounted management surface cannot be told apart from a broken one)")
    if not me.get("billing_issue_funnel_counted"):
        fails.append("MG-5 the billing-issue funnel is not counted (banner shown -> fix tap -> recovered, with the grace deadline as the window; without it, involuntary-churn recovery work has no numerator and no denominator)")
    return fails

def main():
    if len(sys.argv) != 2:
        print("usage: mgmt_check.py <state.json>"); return 2
    with open(sys.argv[1]) as f:
        d = json.load(f)
    fails = check(d)
    print(f"app: {d.get('app','?')}")
    if fails:
        print(f"FAIL ({len(fails)})")
        for x in fails:
            print(f" - {x}")
        return 1
    print("PASS")
    return 0

if __name__ == "__main__":
    sys.exit(main())
