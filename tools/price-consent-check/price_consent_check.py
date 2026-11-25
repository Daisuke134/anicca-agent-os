#!/usr/bin/env python3
"""price-consent-check: deterministic gate for the PRICE INCREASE CONSENT
surface (existing subscribers facing a scheduled price increase that
requires their agreement). Stdlib only, offline, free.
Sources:
- Apple App Store Connect Help "Manage pricing for auto-renewable
  subscriptions" (developer.apple.com/help/app-store-connect/manage-
  subscriptions/manage-pricing-for-auto-renewable-subscriptions, read in
  full): an increase results in either a notice or a request for consent.
  Consent is required when the subscriber is in a region requiring consent
  for any price change, when the increase is more than 50% of the current
  price AND exceeds approx US$5 per period (US$50/year for annual), or when
  the subscriber had a price increase on that subscription within the past
  12 months. Apple contacts subscribers by email/push and repeats the
  request approximately weekly via email, push and in-app messaging until
  expiry. First notice: 60 days before renewal for 2-month+ plans, 27 days
  monthly, 7 days weekly. A subscriber who does not consent expires at the
  end of the last cycle at the former price. An increase that takes effect
  cannot be reversed. Intro/promo subscribers renew at least one more
  period at the displayed price so consent is requested 30+ days ahead.
- RevenueCat "Changing Prices" (revenuecat.com/docs/subscription-guidance/
  price-changes, read in full): on iOS 13.4+ affected subscribers are also
  notified through a message sheet that automatically displays in the app;
  if opt-in is required and they do not agree, the subscription expires at
  the end of the current billing cycle. Grandfathering (preserving the
  current price) needs no consent. By default RevenueCat assumes renewals
  happen at the purchase price, so reporting stays accurate after a
  non-grandfathered increase only with automatic price detection enabled
  (V2 App Store Server Notifications + App Store Connect API key).
This gate is the CLIENT/OPERATIONS layer for a pending consent-required
increase. Whether to change a price at all is the price-change gate
(price-check, 2026-11-13); this gate starts where that one ends.
Exit 0=PASS, 1=FAIL.
"""
import json, sys
def check(d):
    f=[]
    dec=d.get("decision") or {}
    if not dec.get("decision_recorded"): f.append("PC-0 how a pending consent-required price increase will be handled in the app (surface, own notice, measurement) is not recorded as a decision - when Apple starts asking, the app's behaviour will be whatever happens by default")
    if not dec.get("owner_recorded"): f.append("PC-0 no single price-consent owner is recorded")
    if not dec.get("change_register_recorded"): f.append("PC-0 no register of scheduled price changes classifying each (product, storefront) as consent-required vs notice-only before it is scheduled - consent classification depends on the subscriber's region, increase size and 12-month history, so an unclassified change is an unplanned expiry wave")
    det=d.get("detection") or {}
    if not det.get("renewal_price_status_read"): f.append("PC-1 the subscriber's renewal price / price-increase status is never read (only willRenew-style booleans) - a subscriber with a pending consent-required increase is indistinguishable from a normal renewing subscriber until they are gone")
    if not det.get("pending_consent_state_distinguished"): f.append("PC-1 no distinct pending-consent state exists in the subscription model - the cohort Apple is emailing weekly cannot be surfaced, helped, or counted")
    if not det.get("preserved_distinguished_from_moved"): f.append("PC-1 preserved-price (grandfathered) subscribers are not distinguished from subscribers moved to the new price - the two cohorts face opposite futures (nothing changes vs expiry without consent) and one display cannot tell the truth to both")
    dsp=d.get("display") or {}
    if not dsp.get("renewal_price_shown_is_subscribers_own"): f.append("PC-2 the price shown to an existing subscriber is not their own renewal price (it is the offering's current product price) - after an increase is scheduled, a moved subscriber and a preserved subscriber see the same number while owing different amounts")
    if not dsp.get("pending_shows_old_new_and_deadline"): f.append("PC-2 a pending increase is not shown with old price, new price and the consent deadline (end of current period) together - Apple's sheet is transient; the app's own persistent surface is where a subscriber can re-check what they agreed to")
    if not dsp.get("copy_states_expiry_not_silent_move"): f.append("PC-2 copy does not state the actual consequence of not consenting: the subscription expires at the end of the current billing period at the old price - it neither continues silently at the new price nor cancels immediately, and any other wording misleads in one direction or the other")
    ntc=d.get("notice") or {}
    if not ntc.get("own_voice_notice_present"): f.append("PC-3 the app adds no notice of its own in its own voice (reason for the increase, what stays the same) alongside Apple's system requests - Apple's weekly prompts say what and when, never why, and unexplained increases are the ones subscribers refuse")
    if not ntc.get("notice_not_blocking"): f.append("PC-3 the in-app notice blocks or gates normal app use until the subscriber decides - a price decision forced at the door is a dark pattern (cf. the Prayer Lock ban); Apple's own sheet is dismissible and the app's notice must be too")
    if not ntc.get("manage_path_alongside"): f.append("PC-3 no manage-subscription path is offered alongside the notice - a subscriber who wants to agree, or to leave deliberately instead of expiring by default, needs the door next to the message, not in another part of the app")
    aft=d.get("aftermath") or {}
    if not aft.get("expiry_reflected_in_entitlement"): f.append("PC-4 a subscription that expires for non-consent does not flow back into entitlement state - a lapsed subscriber who keeps premium has converted a refused price increase into a free subscription")
    if not aft.get("price_increase_reason_recorded"): f.append("PC-4 expirations caused by a refused price increase are not recorded distinctly (expiration/cancel reason PRICE_INCREASE) - they merge into ordinary churn and the true cost of the increase can never be read back (the price-change gate's post-observation depends on this separation)")
    if not aft.get("auto_price_detection_verified"): f.append("PC-4 automatic price detection (V2 App Store Server Notifications + App Store Connect API key uploaded) is not verified as enabled - without it, RevenueCat keeps assuming the purchase price and every renewal after a non-grandfathered increase is mispriced in reporting")
    if not aft.get("consent_cohort_measured"): f.append("PC-4 the consent cohort is not measured (pending vs agreed vs expired-by-deadline counts) - the expiry wave arrives as unexplained churn weeks after the change was scheduled")
    ver=d.get("verification") or {}
    if not ver.get("scheduled_change_tested"): f.append("PC-5 no end-to-end test of a scheduled increase exists (Sandbox / test change: notice -> consent -> renewal at the new price, and no-consent -> expiry at period end) - the first real run of this path is on paying subscribers")
    if not ver.get("state_unit_tests"): f.append("PC-5 the pending-consent state mapping (renewal-info -> app state -> display) is not unit-tested")
    return f
if __name__=="__main__":
    data=json.load(open(sys.argv[1])); fails=check(data)
    if fails:
        print(f"FAIL ({len(fails)}):")
        [print(" -",x) for x in fails]; sys.exit(1)
    print("PASS")
