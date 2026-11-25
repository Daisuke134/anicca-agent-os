#!/usr/bin/env python3
"""entitlement-check: deterministic gate for the paywall -> paid-access
handoff (purchase success vs entitlement unlock). Stdlib only, no API,
no cost.
Sources (both read in full 2026-11-13):
1) Funnel Leak Audit, "Your Paywall May Not Be the Leak: Audit These 5
   Subscription Handoffs First", dev.to, published 2026-07-18.
   https://dev.to/funnelleakaudit/your-paywall-may-not-be-the-leak-audit-these-5-subscription-handoffs-first-4nok
   - Handoff 4 (paywall -> paid access): "A store purchase can return
     successfully while the UI remains locked. Restore can fail after an
     identity transition. Offerings can be empty in one environment.
     Trial eligibility can disagree with the copy. An anonymous customer
     can become identified without the expected entitlement
     reconciliation."
   - Minimal QA matrix: eligible and ineligible trial users; successful,
     cancelled, and interrupted purchases; purchase success followed by
     entitlement unlock; restore on a new install using the same store
     account; anonymous-to-identified user transitions; expiration,
     refund, and billing-retry states; sandbox/TestFlight where
     applicable.
   - Separate events: purchase_started, purchase_result,
     entitlement_unlocked, restore_result, with result, error_code,
     product_id, entitlement_id, and unlock latency.
   - "If purchase_result=success and entitlement_unlocked disagree,
     that is not a copy problem. It is a revenue and trust leak."
   - Its RevenueCat numbers (82% of trial starts on Day 0; 6.2% median
     trial-start, 20.3% p90) are the article citing RevenueCat State of
     Subscription Apps 2025 -- secondary, not our measurement.
2) RevenueCat official docs, "Getting Subscription Status"
   (CustomerInfo), read in full 2026-11-13.
   https://www.revenuecat.com/docs/customers/customer-info
   - Access is checked via customerInfo.entitlements[<id>]?.isActive.
   - "CustomerInfo will be empty if no purchases have been made and no
     transactions have been synced. This means that entitlements may
     not exist in CustomerInfo even if they have been set up in the
     RevenueCat dashboard."
   - Cache: SDK updates the cache if older than 5 minutes, but ONLY if
     you call getCustomerInfo(), make a purchase, or restore purchases;
     "CustomerInfo updates are not pushed to your app from the
     RevenueCat backend".
   - "It is recommended that all apps have some way for users to
     trigger the restorePurchases method, even if you require all
     customers to create accounts."
   - An unsubscribe or a billing issue being detected does NOT mean
     the entitlement is inactive.
   - On Google Play, entitlements can briefly go empty around renewal
     before grace / a deferred charge is applied.
Exit 0 = PASS, 1 = FAIL. Warnings do not fail.
"""
import json, sys

QA_CASES = [
    "trial_eligible",
    "trial_ineligible",
    "purchase_success",
    "purchase_cancelled",
    "purchase_interrupted",
    "restore_new_install_same_store_account",
    "anonymous_to_identified_transition",
    "expiration_refund_billing_retry_states",
]
EVENTS = ["purchase_started", "purchase_result", "entitlement_unlocked", "restore_result"]
EVENT_FIELDS = ["result", "error_code", "product_id", "entitlement_id"]


def check(d):
    fails, warns = [], []

    # E-0 access decided by entitlement, not product
    acc = d.get("access_check") or {}
    if acc.get("basis") != "entitlement_is_active":
        fails.append(
            "E-0 access is not decided by entitlement isActive -- RevenueCat's "
            "documented check is customerInfo.entitlements[<id>]?.isActive; "
            "deciding by product ID or by the active-subscriptions list breaks "
            "when one entitlement is unlocked by several products, by a "
            "promotion, or by family sharing"
        )
    if acc.get("missing_entitlement_handled") is not True:
        fails.append(
            "E-0 a missing entitlement in CustomerInfo is not handled -- the "
            "docs state CustomerInfo is EMPTY until a purchase or restore has "
            "synced, so the entitlement may not exist even though it is set up "
            "in the dashboard; force-unwrapping it is a crash path and "
            "treating absence as a hard error misreads every new user"
        )

    # E-1 four events separated and fully attributed
    ev = d.get("events") or {}
    for name in EVENTS:
        e = ev.get(name)
        if not e or not e.get("recorded"):
            fails.append(
                f"E-1 event {name} is not recorded as a separate event -- the "
                "source separates purchase_started / purchase_result / "
                "entitlement_unlocked / restore_result precisely so a "
                "successful charge with a locked UI is visible instead of "
                "being averaged into 'paywall conversion'"
            )
            continue
        missing = [f for f in EVENT_FIELDS if f not in (e.get("fields") or [])]
        if missing:
            fails.append(
                f"E-1 event {name} is recorded without fields: "
                f"{', '.join(missing)} -- without result / error_code / "
                "product_id / entitlement_id the failing step cannot be "
                "attributed to a product, an entitlement, or an error class"
            )
    if ev.get("unlock_latency_recorded") is not True:
        warns.append(
            "E-1 unlock latency (purchase success -> entitlement active) is "
            "not recorded -- the source lists it as part of the event set; "
            "without it a slow unlock is indistinguishable from no unlock in "
            "support reports"
        )

    # E-2 mismatch is measured and is zero in verified runs
    mm = d.get("mismatch") or {}
    if mm.get("measured") is not True:
        fails.append(
            "E-2 the purchase_result=success vs entitlement_unlocked "
            "mismatch is not measured -- the source: 'If purchase_result="
            "success and entitlement_unlocked disagree, that is not a copy "
            "problem. It is a revenue and trust leak.' An unmeasured "
            "mismatch is not a zero mismatch"
        )
    elif (mm.get("cases_in_verified_runs") or 0) > 0:
        fails.append(
            f"E-2 {mm.get('cases_in_verified_runs')} verified case(s) of "
            "purchase success without entitlement unlock are on record -- "
            "each one is a paying user looking at a locked app; this blocks "
            "any paywall copy or price experiment until fixed, because the "
            "experiment would be judged on a broken handoff"
        )

    # E-3 QA matrix coverage
    qa = d.get("qa_matrix") or {}
    done = set(qa.get("cases_verified") or [])
    missing_cases = [c for c in QA_CASES if c not in done]
    if missing_cases:
        fails.append(
            "E-3 QA matrix cases not verified: "
            + ", ".join(missing_cases)
            + " -- these are the source's minimal matrix for the paywall -> "
            "paid-access handoff; the unverified cases are exactly where "
            "restore-after-identity-change and eligibility-vs-copy leaks "
            "hide"
        )
    if qa.get("sandbox_testflight_covered") is not True:
        warns.append(
            "E-3 sandbox / TestFlight behaviour is not covered -- the source "
            "includes it 'where applicable'; sandbox receipts and empty "
            "offerings in one environment are a named failure mode, so an "
            "uncovered sandbox is recorded here rather than assumed fine"
        )

    # E-4 cache / refresh / restore discipline (RevenueCat official docs)
    rf = d.get("refresh") or {}
    if rf.get("refresh_on_premium_access") is not True:
        fails.append(
            "E-4 CustomerInfo is not refreshed when premium content is "
            "accessed -- the docs: the cache updates only if it is older "
            "than 5 minutes AND getCustomerInfo() is called, a purchase is "
            "made, or purchases are restored; without a refresh at the "
            "premium gate, a user who just paid (or just renewed) can be "
            "shown the locked state from a stale cache"
        )
    if rf.get("assumes_backend_push") is True:
        fails.append(
            "E-4 the design assumes CustomerInfo updates are pushed from "
            "the backend -- the docs state the opposite: 'CustomerInfo "
            "updates are not pushed to your app from the RevenueCat "
            "backend, updates can only happen from an outbound network "
            "request'; any screen waiting for a push will wait forever"
        )
    if rf.get("restore_trigger_available") is not True:
        fails.append(
            "E-4 users have no way to trigger restorePurchases -- the docs "
            "recommend every app provide one 'even if you require all "
            "customers to create accounts'; restore is the documented "
            "recovery for reinstall, new device, and identity transitions"
        )
    if rf.get("billing_or_unsubscribe_read_as_inactive") is True:
        fails.append(
            "E-4 an unsubscribe detection or a billing-issue detection is "
            "read as 'entitlement inactive' -- the docs state neither "
            "means the entitlement is inactive; cutting access on either "
            "signal locks out users who are still entitled (including "
            "users inside a billing grace period)"
        )
    return fails, warns


def main():
    if len(sys.argv) != 2:
        print("usage: entitlement_check.py <fixture.json>")
        return 2
    with open(sys.argv[1]) as f:
        d = json.load(f)
    fails, warns = check(d)
    for w in warns:
        print(f"WARN: {w}")
    for x in fails:
        print(f"FAIL: {x}")
    print(f"RESULT: {'PASS' if not fails else 'FAIL'} "
          f"({len(fails)} fail, {len(warns)} warn) "
          f"for {d.get('app', 'unknown')}")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
