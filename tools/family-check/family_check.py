#!/usr/bin/env python3
"""family-check: deterministic gate for the SUBSCRIPTION FAMILY SHARING
surface (per-product shareability decision, paywall truth, grant/revoke
plumbing, shared-user education, honest revenue counting).
Stdlib only, offline, free.
Sources (read in full 2026-11-15):
- Apple, App Store Connect Help, "Turn on Family Sharing for In-App
  Purchases" (developer.apple.com/help/app-store-connect/configure-in-app-
  purchase-settings/turn-on-family-sharing-for-in-app-purchases):
  Family Sharing is supported only by auto-renewable subscriptions and
  non-consumables; it is turned on per product in App Store Connect and,
  once turned on, it CANNOT be turned off. Sharing reaches up to five
  additional family members. For subscriptions, new purchasers share by
  default per their Manage Subscriptions preference; existing subscribers
  must opt in from their manage-subscriptions page.
- RevenueCat, "Family sharing in-app purchases iOS - Guide to why, what
  & how" (www-docs.revenuecat.com/blog/engineering/implement-apple-family-
  sharing/, updated 2024-06-06): enabling is per SKU and irreversible;
  the paywall should state shareability using SKProduct.isFamilyShareable
  (via the RevenueCat Package) rather than a hardcoded claim; shared
  transactions arrive through the transaction queue, so observe it /
  initialize the SDK as early as possible; revocation arrives via
  didRevokeEntitlementsForProductIdentifiers / receipt refresh and access
  must follow it; revenue must be counted only for transactions with
  in_app_ownership_type = PURCHASED, never for FAMILY_SHARED copies;
  family members never saw the paywall, so use EntitlementInfo
  .ownershipType to educate shared users about what they received;
  introductory-offer eligibility must account for shared purchases;
  Family Sharing does not work in Sandbox.
Exit 0 = PASS, 1 = FAIL.
Input JSON: {app,
 decision:{per_product_decision_recorded, irreversibility_acknowledged,
   asc_state_evidenced_per_product, revenue_tradeoff_recorded},
 paywall_truth:{callout_driven_by_is_family_shareable,
   no_sharing_claim_when_not_shareable},
 grant_revoke:{sdk_initialized_early, access_from_live_entitlement,
   shared_restore_or_sync_path},
 shared_education:{ownership_type_distinguished,
   shared_user_premium_education},
 measurement:{revenue_counts_purchased_only, shared_cohort_counted,
   intro_eligibility_accounts_for_shared}}
"""
import json, sys

def check(d):
    fails = []
    de = d.get("decision") or {}
    if not de.get("per_product_decision_recorded"):
        fails.append("FS-0 no per-product Family Sharing decision is recorded (shareability is a per-SKU choice in App Store Connect, not an app-wide default; four products sitting at a configuration file's false default is not a decision -- nobody chose it, so nobody can defend it or revisit it)")
    if not de.get("irreversibility_acknowledged"):
        fails.append("FS-0 the irreversibility of the toggle is not acknowledged in the decision record (Apple: once Family Sharing is turned on for a product it cannot be turned off; a decision made without that fact on the page is a one-way door walked through blind)")
    if not de.get("asc_state_evidenced_per_product"):
        fails.append("FS-0 the actual App Store Connect state is not evidenced per product (a local StoreKit configuration file's familyShareable flags describe the test environment, not the store; the live per-product state is unverified until read back from ASC)")
    if not de.get("revenue_tradeoff_recorded"):
        fails.append("FS-0 the revenue tradeoff is not recorded (sharing means fewer subscriptions sold per household, weighed against engagement, retention and word-of-mouth -- RevenueCat's stated pros and cons; an unrecorded tradeoff cannot be checked against later revenue reads)")
    pt = d.get("paywall_truth") or {}
    if not pt.get("callout_driven_by_is_family_shareable"):
        fails.append("FS-1 the paywall has no sharing callout driven by isFamilyShareable (RevenueCat's form: read the property from the product/Package and show the callout selectively; the property is referenced zero times, so the day the toggle is turned on in ASC the paywall will keep saying nothing -- and a hardcoded claim would be worse)")
    if not pt.get("no_sharing_claim_when_not_shareable"):
        fails.append("FS-1 a family-sharing claim is made while the products are not shareable (the store page badge problem RevenueCat warns about: users who bought expecting to share feel deceived and blame the developer; outside claims must exist inside)")
    gr = d.get("grant_revoke") or {}
    if not gr.get("sdk_initialized_early"):
        fails.append("FS-2 the purchase SDK is not initialized early in the app flow (shared purchases are delivered through the transaction queue to every family member; a late or on-demand initialization misses the delivery the grant depends on)")
    if not gr.get("access_from_live_entitlement"):
        fails.append("FS-2 premium access is not derived from the live entitlement (revocation -- leaving the family, sharing switched off -- surfaces as an expired/changed entitlement; access cached from a past purchase flag keeps revoked family members premium forever)")
    if not gr.get("shared_restore_or_sync_path"):
        fails.append("FS-2 a family member has no restore/sync path (RevenueCat community support record: a family-shared subscription may need restoreTransactions/sync to land on the member's device; without the path, shared access depends on a push that may never be re-delivered)")
    se = d.get("shared_education") or {}
    if not se.get("ownership_type_distinguished"):
        fails.append("FS-4 ownership type is never distinguished (EntitlementInfo.ownershipType / in_app_ownership_type separates PURCHASED from FAMILY_SHARED; referenced zero times, a shared user is indistinguishable from a payer in product, support and analytics)")
    if not se.get("shared_user_premium_education"):
        fails.append("FS-4 shared users receive no premium education (a family member granted access never saw the paywall and does not know what was unlocked; RevenueCat's form is to detect the shared grant and teach the benefits -- the post-purchase premium-win surface is exactly where this belongs)")
    me = d.get("measurement") or {}
    if not me.get("revenue_counts_purchased_only"):
        fails.append("FS-5 revenue counting does not separate PURCHASED from FAMILY_SHARED (the same purchase appears on every family member's receipt; counting all copies multiplies one sale into up to six -- unverified revenue is not revenue)")
    if not me.get("shared_cohort_counted"):
        fails.append("FS-5 the family-shared cohort is not counted (shared users are real active users with zero direct revenue; uncounted, they dilute conversion denominators invisibly and their retention -- the stated reason to enable sharing -- can never be read)")
    if not me.get("intro_eligibility_accounts_for_shared"):
        fails.append("FS-5 introductory-offer eligibility does not account for shared purchases (RevenueCat: a FAMILY_SHARED transaction must count when computing intro eligibility, or a family member who already received the intro offer through sharing can take it again as if new)")
    return fails

def main():
    if len(sys.argv) != 2:
        print("usage: family_check.py <state.json>"); return 2
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
