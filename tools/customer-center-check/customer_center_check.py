#!/usr/bin/env python3
"""customer-center-check: deterministic gate for the CUSTOMER CENTER
(self-service subscription management surface). Stdlib only, offline, free.
Sources (read 2026-11-17):
- RevenueCat "Customer Center" https://www.revenuecat.com/docs/tools/customer-center
  (full read via browser.open): a dashboard-configured self-service UI - cancel,
  restore purchases (+ support email fallback), contact support, refunds (iOS),
  plan changes (iOS), feedback prompts for cancellation/refund reasons, and
  automatic promotional offers to retain. Available on Pro and Enterprise plans.
- RevenueCat "Configure Customer Center" (search-result full read 2026-11-17):
  the default configuration ships four paths (Cancellation, Missing Purchases,
  Refund Request iOS-only, Plan Changes iOS-only) plus default feedback surveys
  ("Too expensive" / "Don't use the app" / "Bought by mistake"); promotional
  offers must FIRST be created in App Store Connect / Play Console and then
  assigned per product under Lifecycle -> Retention in the Customer Center tab,
  otherwise the offer is never shown; survey responses are read in the
  Customer Center Survey Responses chart.
- RevenueCat "Configuring Apple Promotional Offers for Customer Center"
  (search-result full read 2026-11-17): if the SDK cannot locate a matching
  promotional offer id for the user's active subscription, it BYPASSES the
  survey and proceeds with the requested cancellation/refund - a wired view
  with unassigned offers silently loses the retention moment.
Exit 0=PASS, 1=FAIL.
"""
import json, sys
def check(d):
    f=[]
    dec=d.get("decision") or {}
    if not dec.get("decision_recorded"): f.append("CC-0 adopting Customer Center as THE self-service subscription surface (vs a hand-rolled settings page or nothing) is not recorded as a decision - the surface exists by accident of an SDK import, not by choice, so nobody owns its configuration")
    if not dec.get("owner_recorded"): f.append("CC-0 no single Customer Center owner is recorded (dashboard configuration, offer assignment and survey review are ongoing work, not a one-time view)")
    if not dec.get("plan_tier_verified"): f.append("CC-0 the RevenueCat plan tier is not verified (Customer Center is Pro/Enterprise only) - on a legacy/free tier the view can render without the configured paths ever applying")
    fou=d.get("foundation") or {}
    if not fou.get("view_wired"): f.append("CC-1 CustomerCenterView is not presented anywhere in the app - customers must leave for the App Store subscription page or support email for every management task")
    if not fou.get("entry_always_available"): f.append("CC-1 the Customer Center entry is not available regardless of subscription state (RevenueCat ships a dedicated screen for users WITHOUT an active subscription; hiding the entry behind subscriber state strands exactly the users with missing-purchase problems)")
    if not fou.get("no_dead_config"): f.append("CC-1 dead Customer Center configuration exists (a declared key/property that nothing consumes - CustomerCenterView is configured from the dashboard, not from an app-side ID; dead config misleads every future reader into thinking the surface is wired through it)")
    ret=d.get("retention") or {}
    if not ret.get("cancellation_path_decided"): f.append("CC-2 the cancellation path is not deliberately decided and recorded (default vs customised paths/flows) - an unexamined default is an original design, not the winner's configured one")
    if not ret.get("feedback_survey_decided"): f.append("CC-2 the cancellation/refund feedback survey is not deliberately configured (question and answer options recorded) - the exit-reason data the whole retention loop learns from is whatever the default happens to ask")
    if not ret.get("promo_offer_wired"): f.append("CC-2 no promotional offer is verifiably wired end-to-end (created in App Store Connect AND assigned per product under Lifecycle -> Retention) - without a matching offer id the SDK bypasses the survey and proceeds straight to cancellation, so the retention moment silently never happens")
    sup=d.get("support") or {}
    if not sup.get("restore_path_present"): f.append("CC-3 no restore path is available to the customer (Missing Purchases path in Customer Center and/or an in-app restore action) - a paying customer on a new device has no self-service way back")
    if not sup.get("support_contact_configured"): f.append("CC-3 the support contact inside Customer Center is not configured (support email / custom URL / FAQ link, including the restore-trouble fallback) - the paths that cannot self-resolve dead-end instead of reaching a human channel")
    if not sup.get("refund_planchange_decided"): f.append("CC-3 the iOS-only paths (Refund Request, Plan Changes) are not decided and recorded - both ship in the default configuration, so an unrecorded decision means they are live by default, untested")
    mea=d.get("measurement") or {}
    if not mea.get("survey_responses_reviewed"): f.append("CC-4 feedback survey responses are not reviewed on a recorded cadence (Customer Center Survey Responses chart) - exit reasons are collected into a chart nobody reads, so the product never learns why it is cancelled")
    if not mea.get("actions_observed"): f.append("CC-4 Customer Center actions/outcomes are not observed beyond the entry screen view (offer shown/accepted, cancellation completed, restore completed) - the surface's effect is invisible in the company's own measurement")
    if not mea.get("outcome_measured"): f.append("CC-4 the retention outcome is not measured (cancellations saved by the offer / total cancellation-path entries) - a retention surface with no save rate is a hope, not a mechanism")
    ver=d.get("verification") or {}
    if not ver.get("sandbox_e2e_tested"): f.append("CC-5 no sandbox end-to-end walk of the cancellation path exists (open Customer Center with a sandbox subscription, enter cancellation, see the survey and the offer actually render) - the bypass failure mode is only visible in this walk")
    if not ver.get("no_subscription_state_tested"): f.append("CC-5 the no-active-subscription state is not tested (open Customer Center signed out / never subscribed) - the dedicated management screen for that state is a separate surface that breaks separately")
    if not ver.get("tests_cover_entry"): f.append("CC-5 no automated test covers the Customer Center entry point - a settings refactor can silently delete the only subscription-management door in the app")
    return f
if __name__=="__main__":
    data=json.load(open(sys.argv[1])); fails=check(data)
    if fails:
        print(f"FAIL ({len(fails)}):")
        [print(" -",x) for x in fails]; sys.exit(1)
    print("PASS")
