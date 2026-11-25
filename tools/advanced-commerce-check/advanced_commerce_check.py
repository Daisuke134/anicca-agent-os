#!/usr/bin/env python3
"""advanced-commerce-check: deterministic gate for Apple's Advanced Commerce
API eligibility decision (large one-time catalogs / large multi-creator
subscription catalogs / subscriptions with auto-renewing add-ons, sold via
server-defined SKUs instead of App Store Connect products). Stdlib only,
offline, free.
Sources (read in full 2026-11-23):
- Apple Developer, Advanced Commerce API (official)
  https://developer.apple.com/in-app-purchase/advanced-commerce-api/
  Eligibility: ONE of three business models must be CORE to the app --
  (1) exceptionally large catalogs of one-time purchases, frequently added;
  (2) exceptionally large catalogs of subscription content from multiple
  creators, each creator merchandised as a single auto-renewable sub;
  (3) a subscription with optional add-on content renewing as ONE purchase.
  An app may also apply when another program (e.g. Mini Apps Partner
  Program) requires the API. Access is requested PER APP via a form;
  approval is per app; rejected apps may reapply. Updates such as new
  product identifiers, new business models, or significant price changes
  go back through the Access form.
  App requirements: manage the catalog as SKUs in your OWN system;
  StoreKit 2; in-app subscription management (showManageSubscriptions);
  App Store Server API + Server Notifications V2; an in-app refund path
  (Report a Problem link or beginRefundRequest); minimum iOS 15.0 /
  iPadOS 15.0 / Mac Catalyst 15.0 / tvOS 15.0 / visionOS 1.0 / watchOS 8.0.
  Recommendations: App Store Server Library; enable Billing Grace Period;
  Send Consumption Information on refund requests.
  Limitations (Q&A): purchases through the API can't be promoted on the
  App Store and can't use subscription offers, Family Sharing, or StoreKit
  Testing in Xcode. Commission rate is UNCHANGED. An approved app may use
  the API, App Store Connect, or both -- approval is not all-or-nothing.
  Review: submit binary + generic product ID, and state in the review
  notes that the app uses the Advanced Commerce API.
- RevenueCat, What you need to know about Apple's Advanced Commerce API
  https://www.revenuecat.com/blog/growth/what-you-need-to-know-apples-advanced-commerce-api
  (secondary explainer; limits and requirements match Apple's page.)
Boundary: product-architecture-check owns the ASC product catalog and
price-change mechanics; multiseat-check owns seat/group purchasing; this
gate owns ONLY the Advanced Commerce eligibility decision, its readiness
requirements, and acceptance of its limitations.
Exit 0 = PASS, 1 = FAIL.
"""
import json, sys
CHECKS = [
 ("AC-0","eligibility_assessed_per_app","Advanced Commerce eligibility was never assessed per app against Apple's three core business models (large one-time catalog / large multi-creator subscription catalog / subscription with renewing add-ons) -- unassessed = the decision was never made"),
 ("AC-0","decision_recorded_per_app","no deliberate adopt / not-adopt decision is recorded per app (for a single-subscription app 'not eligible, stay on ASC' IS the decision -- silence is not)"),
 ("AC-0","channel_owner_recorded","no single owner is recorded for the Advanced Commerce decision (an unowned platform decision drifts until a catalog or add-on need hits it unprepared)"),
 ("AC-1","core_business_model_verified","the claimed business model is not verified as CORE to the app (Apple requires the model to be core functionality; a side catalog or a future idea does not qualify)"),
 ("AC-1","eligibility_not_assumed_by_analogy","eligibility is assumed by analogy (another app's or another program's approval does not transfer -- access is requested and approved per app)"),
 ("AC-1","program_dependency_checked","program dependencies were not checked (some programs, e.g. Mini Apps Partner Program, REQUIRE the API; not checking means a program application could stall on a missing prerequisite)"),
 ("AC-2","own_sku_catalog_managed","the purchase catalog is not managed as SKUs in the house's own system (the API model is server-defined SKUs sent at purchase time, not products created one by one in App Store Connect)"),
 ("AC-2","uses_storekit2","the app does not use StoreKit 2 to initiate and merchandise purchases (a hard requirement)"),
 ("AC-2","in_app_subscription_management","there is no easy in-app subscription management surface (Apple names showManageSubscriptions; server-defined SKUs without in-app management strand the subscriber)"),
 ("AC-2","server_api_and_notifications_v2","the App Store Server API and Server Notifications V2 are not both in use (real-time status is a requirement, not an enhancement, when the catalog lives on your server)"),
 ("AC-2","in_app_refund_path","there is no in-app refund path (a Report a Problem link or beginRefundRequest; Advanced Commerce even exposes developer-initiated refund/revoke endpoints for eligible subscription apps, which presuppose this surface)"),
 ("AC-2","minimum_os_floor_met","the minimum OS floor is not met (iOS 15.0 / iPadOS 15.0 / Mac Catalyst 15.0 / tvOS 15.0 / visionOS 1.0 / watchOS 8.0)"),
 ("AC-3","limitations_accepted","the API's limitations are not accepted in writing BEFORE applying (purchases can't be promoted on the App Store, can't use subscription offers or Family Sharing, and can't use StoreKit Testing in Xcode -- discovering this after migration breaks the offer stack)"),
 ("AC-3","commission_unchanged_understood","a commission benefit is expected from the API (Apple states the rate is unchanged; a business case built on a fee cut is built on nothing)"),
 ("AC-3","dual_management_understood","it is not understood/recorded that an approved app may use the API, App Store Connect, or BOTH (treating approval as all-or-nothing forces a flag-day migration Apple does not require)"),
 ("AC-4","application_per_app_and_addendum","access was not requested per app through the Access form with its terms (per-app is the only route; there is no account-wide switch)"),
 ("AC-4","review_submission_hygiene","the review submission plan is missing (submit the binary WITH the generic product ID and state in the review notes that the app uses the Advanced Commerce API; omitting either delays or rejects)"),
 ("AC-4","updates_reapplied_via_form","catalog/model/significant-price updates are not routed back through the Access form (Apple requires updates such as new product identifiers, new business models, or significant price changes to be submitted there)"),
]
def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "-"
    data = json.load(open(path)) if path != "-" else json.load(sys.stdin)
    fails = [f"{g} {k}: {msg}" for g, k, msg in CHECKS if not data.get(k)]
    if fails:
        print(f"FAIL {len(fails)}/{len(CHECKS)}")
        for f in fails: print(" -", f)
        return 1
    print(f"PASS {len(CHECKS)}/{len(CHECKS)}")
    return 0
if __name__ == "__main__":
    sys.exit(main())
