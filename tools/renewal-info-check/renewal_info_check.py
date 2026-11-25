#!/usr/bin/env python3
"""renewal-info-check: deterministic gate for the RENEWAL INFORMATION surface
(why a subscription will / will not renew, and what happens next).
Stdlib only, offline, free.
Sources (read 2026-11-17):
- RevenueCat "Getting Subscription Status"
  https://www.revenuecat.com/docs/customers/customer-info (full read via
  browser.open): EntitlementInfo exposes, beyond isActive, willRenew,
  periodType, expirationDate, unsubscribeDetectedAt (null until the user
  opts out of auto-renew; an unsubscribe does NOT mean inactive),
  billingIssueDetectedAt (null again once resolved; a billing issue does
  NOT mean inactive), ownershipType and managementURL. The presented shape
  is to drive UI decisions from these fields, not from isActive alone.
- Apple "JWSRenewalInfoDecodedPayload" (App Store Server API): the signed
  renewal payload carries autoRenewStatus, autoRenewProductId (the product
  that will be charged at the next renewal - different means a scheduled
  plan change), expirationIntent (1 customer cancelled, 2 billing error,
  3 price increase not consented, 4 product unavailable, 5 other reason),
  gracePeriodExpiresDate, isInBillingRetryPeriod, priceIncreaseStatus
  (0 no response yet, 1 consented), renewalDate and the offer applied to
  the next renewal. A subscription therefore has at least five states
  (subscribed / cancelled-but-active / grace / billing retry / expired
  with a reason), not two.
Exit 0=PASS, 1=FAIL.
"""
import json, sys
def check(d):
    f=[]
    dec=d.get("decision") or {}
    if not dec.get("decision_recorded"): f.append("RI-0 treating renewal information (why a subscription will/won't renew and what happens next) as a first-class surface is not recorded as a decision - the app reads access (isActive) and improvises the rest")
    if not dec.get("owner_recorded"): f.append("RI-0 no single renewal-information owner is recorded (capture, state routing and expiration-reason follow-up are ongoing work, not a one-time model field)")
    if not dec.get("source_decided"): f.append("RI-0 the renewal-information source of truth is not decided and recorded (RevenueCat EntitlementInfo fields vs Apple signedRenewalInfo/JWSRenewalInfo) - two sources read ad hoc will disagree about the same subscriber")
    cap=d.get("capture_core") or {}
    if not cap.get("will_renew_captured"): f.append("RI-1 willRenew / autoRenewStatus is not captured - the app cannot distinguish a renewing subscriber from one who already cancelled but still has access")
    if not cap.get("unsubscribe_detected_captured"): f.append("RI-1 unsubscribeDetectedAt is not captured - the moment of cancellation (the start of the save window, while access still runs) is invisible; cancellation is only discovered at expiration, when it is too late")
    if not cap.get("billing_issue_detected_captured"): f.append("RI-1 billingIssueDetectedAt is not captured directly (inference from a server status string is not the field) - the start of the billing-recovery window has no trustworthy timestamp")
    ren=d.get("capture_renewal") or {}
    if not ren.get("grace_period_date_captured"): f.append("RI-2 gracePeriodExpiresDate is not captured - the billing-issue surface cannot show the actual deadline the customer must act by, only a generic warning")
    if not ren.get("next_plan_captured"): f.append("RI-2 the next-renewal product (autoRenewProductId) is not captured - a scheduled upgrade/downgrade is invisible, so the app promises the current plan while Apple will charge a different one")
    if not ren.get("expiration_intent_captured"): f.append("RI-2 expirationIntent / expiration reason is not captured - voluntary cancel, billing error, unaccepted price increase and product-unavailable expirations collapse into one unexplained 'expired', and each needs a different follow-up")
    rou=d.get("routing") or {}
    if not rou.get("billing_issue_surface"): f.append("RI-3 no in-app billing-issue surface exists (a banner/route to the subscription management page driven by the billing-issue state) - a customer in grace/billing retry is never told to fix their payment method")
    if not rou.get("grace_deadline_shown"): f.append("RI-3 the grace-period deadline is not shown on the billing-issue surface - a warning without the date it expires converts worse than the same warning with the real deadline")
    if not rou.get("cancelled_expiry_notice"): f.append("RI-3 a cancelled-but-still-active subscriber gets no expiry notice (access until a stated date, with a way back) - the save window that unsubscribeDetectedAt opens is left unused")
    mea=d.get("measurement") or {}
    if not mea.get("renewal_states_measured"): f.append("RI-4 renewal states are not measured as states (renewing / cancelled-active / grace / billing-retry counts over time) - churn is only visible after expiration, never while it is still preventable")
    if not mea.get("expiration_by_intent_measured"): f.append("RI-4 expirations are not broken down by expirationIntent - voluntary and involuntary churn are summed into one number, so recovery effort cannot be aimed")
    if not mea.get("billing_resolution_measured"): f.append("RI-4 billing-issue resolution is not measured (issues detected vs resolved before grace expiry) - the recovery surface has no outcome number")
    ver=d.get("verification") or {}
    if not ver.get("sandbox_states_tested"): f.append("RI-5 the renewal states are not walked in sandbox/TestFlight (cancel-while-active, billing retry, grace) - the states that only appear around renewal day are exactly the ones never seen before production")
    if not ver.get("tests_cover_renewal_fields"): f.append("RI-5 no automated test covers the renewal-field mapping (willRenew/unsubscribe/billing-issue/grace/next-plan/intent into the app's model) - a model refactor can silently drop the fields the retention surfaces depend on")
    if not ver.get("lifetime_edge_handled"): f.append("RI-5 the lifetime edge is not handled (willRenew=false must not mark a lifetime/non-renewing purchase as cancelled) - the most loyal customers would be shown cancellation UI")
    return f
if __name__=="__main__":
    data=json.load(open(sys.argv[1])); fails=check(data)
    if fails:
        print(f"FAIL ({len(fails)}):")
        [print(" -",x) for x in fails]; sys.exit(1)
    print("PASS")
