#!/usr/bin/env python3
"""offercode-check: deterministic gate for the OFFER CODE REDEMPTION
surface (whether subscription offer codes -- the free, off-store
acquisition / retention / win-back lever -- are decided in App Store
Connect, reachable inside the app, received without assuming a
callback, synced on return, truthfully represented, and measured).
Stdlib only, offline, free.
Sources (read in full 2026-11-16):
- Apple App Store Connect Help "Set up subscription offer codes"
  https://developer.apple.com/help/app-store-connect/manage-subscriptions/set-up-subscription-offer-codes
  Offer = per subscription; reference name identifies the offer in
  Sales and Trends and StoreKit transactions; eligibility (new /
  existing / expired) and the introductory-offer interaction are
  chosen at creation and an offer cannot be edited afterwards;
  pay-as-you-go / pay-up-front / free with a duration; renew to the
  standard price or prevent auto-renewal (free only); max 1 million
  redemptions per app per quarter shared across subscriptions; max
  10 active offers per subscription; one code per offer per customer;
  one-time-use codes in batches of 500-25,000 expiring at most six
  months after creation; custom codes up to 64 characters with an
  optional redemption limit; sandbox codes 10-10,000 for testing;
  distribution is the developer's own job (direct handout, redemption
  URL, or in-app via the StoreKit method on iOS 14+); deactivating a
  code expires it immediately and deactivating an offer is final.
- RevenueCat "iOS Subscription Offers"
  https://www-docs.revenuecat.com/docs/subscription-guidance/subscription-offers/ios-subscription-offers
  Offer codes need an uploaded In-App Purchase Key for accurate
  revenue tracking; in-app redemption is
  Purchases.shared.presentCodeRedemptionSheet() (SDK 3.8.0+); Apple
  provides NO callback for redemption success, so the app must react
  to CustomerInfo via the receivedUpdated delegate / listener; the
  in-app sheet is known to be unstable and may not display before
  the App Store terms are accepted, so the supported fallback is the
  App Store redemption URL
  https://apps.apple.com/redeem?ctx=offercodes&id={app_id}&code={code}
  plus calling syncPurchases when the user returns to the app --
  otherwise the user is left to trigger a manual restore.
Exit 0 = PASS, 1 = FAIL.
"""
import json, sys

def check(d):
    fails = []
    dec = d.get("decision") or {}
    if not dec.get("offer_decision_recorded"):
        fails.append("OC-0 no offer decision is recorded (no offer exists for any subscription product -- the StoreKit configuration carries no offer codes and no document records a reference name, target product, price form or duration; a free off-store acquisition channel that every subscription winner has is simply absent)")
    if not dec.get("eligibility_and_terms_fixed_before_distribution"):
        fails.append("OC-0 eligibility and terms are not fixed before distribution (Apple's form: eligibility new/existing/expired, the introductory-offer interaction, countries, price form and the renew-or-prevent-renewal choice are set at creation and the offer cannot be edited afterwards -- deciding them at distribution time means recreating the offer and invalidating every code already handed out)")
    if not dec.get("limits_accounted"):
        fails.append("OC-0 the platform limits are not accounted for in any recorded plan (1 million redemptions per app per quarter shared across subscriptions, at most 10 active offers per subscription, one redemption per customer per offer -- an unplanned campaign can silently exhaust the shared quarterly pool)")
    if not dec.get("iap_key_for_revenue_tracking_recorded"):
        fails.append("OC-0 no record that an In-App Purchase Key is uploaded to the billing layer (RevenueCat's form: without the key, offer-code revenue is not tracked accurately, so a redemption campaign would land in the funnel as unexplained or mispriced revenue)")
    ent = d.get("entry") or {}
    if not ent.get("inapp_redemption_sheet_entry"):
        fails.append("OC-1 the app has no in-app redemption entry (no presentCodeRedemptionSheet call and no offer-code redemption modifier anywhere in the tree -- a person holding a code who opens the app, the highest-intent moment, has nowhere inside the app to use it)")
    if not ent.get("redemption_url_route_prepared"):
        fails.append("OC-1 no redemption-URL route is prepared (the https://apps.apple.com/redeem?ctx=offercodes&id=&code= form is the one distribution asset that works before install and doubles as the fallback when the in-app sheet fails to display -- without it every code must be typed by hand into the App Store)")
    if not ent.get("entry_copy_localized"):
        fails.append("OC-1 there is no localised redemption entry copy (no redeem string in any locale -- the entry, if added later as an English-only afterthought, would break the app's locale-first rule on exactly the screen a campaign sends people to)")
    rec = d.get("reception") or {}
    if not rec.get("customerinfo_listener_receives_redemption"):
        fails.append("OC-2 no CustomerInfo listener/delegate is in place to receive a redemption (Apple gives the sheet no success callback and a code can be redeemed entirely outside the app -- without a standing listener the entitlement arrives and nothing in the app reacts)")
    if not rec.get("no_callback_assumption"):
        fails.append("OC-2 the flow assumes a callback or return value from the redemption sheet (RevenueCat's form is explicit: there is none -- code that waits for one reports cancelled for successful redemptions and leaves redeemers locked out until some unrelated refresh)")
    if not rec.get("external_redemption_observed_at_launch"):
        fails.append("OC-2 a redemption completed in the App Store while the app was closed is not observed at launch (the delegate/listener must be registered during configuration, before any screen -- registered late, the first CustomerInfo after a cold start can be missed)")
    ret = d.get("return_sync") or {}
    if not ret.get("sync_purchases_on_return_from_appstore"):
        fails.append("OC-3 returning from an App Store redemption does not trigger syncPurchases (RevenueCat's form: record the departure, sync on return -- the foreground handlers that exist refresh content and permissions but never sync purchases, so the redirect path depends on the transaction queue happening to wake the listener)")
    if not ret.get("restore_exists_as_fallback"):
        fails.append("OC-3 no restore path exists as the last-resort fallback for a redeemer whose entitlement has not appeared (the redirect guidance ends with the user triggering a restore -- if even that button is absent, a successful redemption can present as a lost payment)")
    truth = d.get("truth") or {}
    if not truth.get("offer_period_distinguished_from_trial"):
        fails.append("OC-4 an offer-code period is not distinguished from a trial (the subscription mapping reads only periodType == .trial, so a redeemed free or discounted period is labelled and counted as an ordinary trial -- campaign cohorts become indistinguishable from organic trial cohorts and the offer can never be evaluated)")
    if not truth.get("entitlement_drives_paywall_and_settings"):
        fails.append("OC-4 the paywall and settings do not derive from the live entitlement (a redeemer who is already entitled must stop seeing purchase prompts -- surfaces that render from cached or local state keep selling to a person who just redeemed)")
    meas = d.get("measurement") or {}
    if not meas.get("redemption_measured_by_reference_name"):
        fails.append("OC-5 redemptions are not measurable by offer reference name (no analytics property, webhook field or report keyed to the offer -- codes can be handed out but nobody can count how many came back, per campaign or at all)")
    if not meas.get("expiry_and_deactivation_ops_recorded"):
        fails.append("OC-5 expiry and deactivation operations are not recorded (one-time codes die at most six months after creation and deactivation is immediate and, at offer level, irreversible -- with no recorded owner or calendar, live campaigns expire mid-flight and nobody notices)")
    if not meas.get("sandbox_redemption_tested_and_recorded"):
        fails.append("OC-5 no sandbox redemption test is recorded (Apple provides sandbox codes, 10-10,000 per offer, precisely because the sheet is unstable and TestFlight behaviour differs -- shipping the entry untested means the first real redeemer is the test)")
    return fails

if __name__ == "__main__":
    with open(sys.argv[1]) as f:
        data = json.load(f)
    failures = check(data)
    if failures:
        print(f"FAIL ({len(failures)}):")
        for x in failures:
            print(" -", x)
        sys.exit(1)
    print("PASS")
