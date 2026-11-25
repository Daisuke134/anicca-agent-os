#!/usr/bin/env python3
"""offer-routing-check: deterministic gate for Apple subscription OFFER ROUTING
(choosing among introductory / promotional / offer-code / win-back offers).
Stdlib only, offline, free.
Sources (read in full this run, 2026-11-13):
- RevenueCat docs, "iOS Subscription Offers": all four offer types require an
  uploaded In-App Purchase key for RevenueCat validation. Introductory = new
  users, applied automatically, eligibility checkable. Promotional = existing
  and lapsed only, NOT applied automatically (the app decides who sees it;
  Apple enforces only that the user had/has a subscription, otherwise the
  regular product is shown). Offer codes = new and existing, SDK 3.8.0+,
  redeemed via the in-app sheet (RevenueCat warns the sheet is unstable and
  recommends redirecting to the App Store redeem URL) or the redeem URL
  https://apps.apple.com/redeem?ctx=offercodes&id={app_id}&code={code}, with
  syncPurchases/restore on return. Win-back = lapsed only, iOS 18+ for the
  in-app sheet, product must be App-Review approved first; eligibility dials
  are minimum paid duration, time since last subscribed, wait between offers.
  In-App Purchase promo codes are NOT recommended: treated as a regular
  purchase, revenue inaccurate, no auto-renew, not compatible with the
  redemption sheet, non-commercial only, 1,000 per 6 months, and no new codes
  can be created after 2026-03-26.
  https://www-docs.revenuecat.com/docs/subscription-guidance/subscription-offers/ios-subscription-offers
- Sonar, "Apple Offer Codes vs Win-Back & Promotional Offers" (limits checked
  against Apple developer documentation 2026-10-01): route by job --
  acquisition=introductory, retention/upsell you trigger=promotional,
  off-store campaigns (email, partners, podcasts, events)=offer codes,
  reacquisition Apple distributes=win-back. Intro eligibility is one offer
  per SUBSCRIPTION GROUP (not per product), lost permanently after
  redemption; check isEligibleForIntroOffer before rendering a trial claim.
  Promotional is the only type needing a server signature (JWS, back-deployed
  to iOS 15). Offer codes: 1M per app per quarter shared, up to 10 active
  offers per subscription, one-time batches 500-25,000, max 6 months
  validity, one redemption per customer per offer, existing subscribers can
  only redeem upgrades/same level, custom codes leak publicly so they need a
  redemption cap and an end date. Win-back: up to 5 live per storefront per
  subscription, 350 configured, min 3-day run; promoted win-back appears on
  the product page and in editorial/personalised placements (iOS 18+).
  Measurement: tag every transaction with offerType (1 intro, 2 promotional,
  3 offer-code, 4 win-back) plus offerIdentifier; keep a holdout for anything
  you trigger and judge 90-day revenue per eligible user, not conversion
  (worked example: 40% off lifting conversion 20% = 1.2 x 0.6 = 0.72 of
  baseline, a 28% loss over the discounted period); win-back cannot be held
  out inside one window, so compare lapse cohorts (run 2-6 months lapsed,
  leave 7-12 untouched, then swap) and track full-price renewals after the
  discount ends; watch intro-offer stacking (code applying after the intro
  offer gives two discounted periods). Suggested order (author's judgement,
  not Apple's): win-back first (it surfaces itself), then promotional at the
  cancellation screen once a holdout exists, offer codes last, when a
  distribution channel exists.
  https://trysonar.app/blog/apple-subscription-offers-compared
Exit 0 = PASS, 1 = FAIL. Warnings do not fail.
"""
import json, sys

OFFER_TYPES = {"introductory", "promotional", "offer_code", "winback"}
JOB_TO_TYPE = {
    "acquisition": "introductory",
    "retention_upsell_in_app": "promotional",
    "off_store_campaign": "offer_code",
    "reacquisition_apple_surfaced": "winback",
}

def check(d):
    fails, warns = [], []
    offers = d.get("offers") or []
    by_type = {}
    for o in offers:
        by_type.setdefault(o.get("type"), []).append(o)
    # O-0 routing recorded, one type per job, no deprecated promo codes
    routing = d.get("routing") or {}
    if not routing.get("recorded"):
        fails.append("O-0 offer routing is not recorded (each job -- acquisition / in-app retention-upsell / off-store campaign / Apple-surfaced reacquisition -- must be mapped in writing to exactly one of the four offer types before ASC is touched; an unrecorded discount is an unmeasurable one)")
    for job, want in JOB_TO_TYPE.items():
        got = routing.get("jobs", {}).get(job)
        if routing.get("recorded") and got is not None and got != want:
            fails.append(f"O-0 job '{job}' is routed to '{got}' but the evidenced routing is '{want}' (introductory=new subscribers only, promotional=existing/lapsed in-app only, offer codes=off-store distribution, win-back=lapsed via Apple surfaces -- routing a job to the wrong mechanism means Apple will not honour it for the people it was meant for)")
    if d.get("uses_iap_promo_codes"):
        fails.append("O-0 the design uses In-App Purchase promo codes -- RevenueCat marks them not recommended (revenue reads inaccurately, no auto-renew, not compatible with the redemption sheet, non-commercial only, 1,000 per 6 months) and Apple stops new IAP promo code creation after 2026-03-26; use offer codes instead")
    # O-1 eligibility
    elig = d.get("eligibility") or {}
    if "introductory" in by_type:
        if not elig.get("intro_group_scoped_understood"):
            fails.append("O-1 introductory eligibility is not recorded as subscription-GROUP scoped (one intro offer per group, not per product, and eligibility is lost permanently after redemption -- a per-product mental model promises trials Apple will not honour)")
        if not elig.get("intro_checked_before_paywall_claim"):
            fails.append("O-1 the paywall renders a trial/intro claim without checking eligibility first (StoreKit 2 isEligibleForIntroOffer) -- showing 'start free trial' to someone ineligible promises a discount the App Store will not apply")
    for o in by_type.get("promotional", []):
        aud = set(o.get("audience") or [])
        if "never_subscribed" in aud:
            fails.append("O-1 a promotional offer targets never-subscribed users -- Apple enforces that promotional offers require a current or past subscription; never-subscribed users are shown the regular product regardless, so the campaign silently does nothing for them")
        if not aud.intersection({"existing", "lapsed"}):
            fails.append("O-1 a promotional offer has no existing/lapsed audience recorded (its only eligible audiences are current and previously subscribed customers)")
    for o in by_type.get("offer_code", []):
        if not (o.get("audience") or []):
            fails.append("O-1 an offer code has no eligibility combination recorded (new / existing / expired must be chosen explicitly in ASC, and Apple checks it against the whole subscription group, not just that product)")
    # O-2 prerequisites
    pre = d.get("prerequisites") or {}
    if offers and not pre.get("iap_key_uploaded"):
        fails.append("O-2 offers are configured but the In-App Purchase key upload is not recorded -- RevenueCat requires the subscription key to authenticate and validate every offer type (introductory in StoreKit 2, promotional, offer codes, win-back); without it, offer revenue tracking is not accurate")
    if "promotional" in by_type and not pre.get("promo_server_signature_ready"):
        fails.append("O-2 promotional offers are configured but server signing is not ready -- promotional is the only offer type that requires a server-side signature (JWS in StoreKit 2); an unsigned promotional offer cannot be purchased")
    if "winback" in by_type:
        if not pre.get("winback_product_review_approved"):
            fails.append("O-2 a win-back offer is configured for a product whose App Review approval is not recorded -- win-back offers can only be configured for subscription products already approved by App Review")
        if not pre.get("winback_ios18_surfaces_understood"):
            warns.append("O-2 win-back iOS 18 surfaces are not marked understood (Manage Subscriptions works from iOS 14.3, but the automatic in-app sheet and product-page/editorial promotion need iOS 18 -- judge reach on the older surface, treat iOS 18 surfaces as the bonus)")
    if "offer_code" in by_type and not pre.get("offer_code_return_sync_ready"):
        fails.append("O-2 offer codes are configured but the return path is not ready (RevenueCat warns the in-app redemption sheet is unstable with no success callback; the evidenced path is the App Store redeem URL plus syncPurchases/restore when the user returns -- without it, a redeemed user comes back to a locked app)")
    # O-3 limits and leakage
    for t in ("promotional", "offer_code"):
        n = len(by_type.get(t, []))
        if n > 10:
            fails.append(f"O-3 {n} active {t} offers recorded (>10) -- Apple allows up to 10 active offers per subscription for this type")
    oc = d.get("offer_codes") or {}
    if "offer_code" in by_type:
        if (oc.get("quarterly_codes_planned") or 0) > 1_000_000:
            fails.append("O-3 planned offer codes exceed 1,000,000 per app per quarter (the shared Apple quota across all subscriptions and IAPs)")
        if (oc.get("validity_months") or 0) > 6:
            fails.append(f"O-3 offer code validity is {oc.get('validity_months')} months (>6) -- one-time codes expire at most 6 months after creation")
        if oc.get("custom_code_public"):
            if not oc.get("custom_code_has_cap"):
                fails.append("O-3 a public custom code has no redemption cap -- a memorable public code that escapes to a deal forum lets full-price prospects wait for the discount; cap it (up to 25,000 per batch)")
            if not oc.get("custom_code_has_end_date"):
                fails.append("O-3 a public custom code has no end date -- custom codes can run with 'No End Date', which is exactly how a leaked code becomes a permanent parallel price")
        if not oc.get("one_per_customer_per_offer"):
            fails.append("O-3 one-redemption-per-customer-per-offer is not recorded/enforced for offer codes (Apple's rule; without it the same person can stack redemptions across distributions of the same offer)")
    # O-4 stacking
    stk = d.get("stacking") or {}
    if stk.get("code_applies_after_intro"):
        if not stk.get("stacking_intentional_recorded"):
            fails.append("O-4 offer codes are set to apply AFTER the introductory offer without a recorded intentional decision -- new customers then get two consecutive discounted periods; that is fine for a deliberate partner bundle and expensive for a public promo, and the difference must be a decision, not a default")
    # O-5 measurement
    ms = d.get("measurement") or {}
    if offers:
        if not ms.get("tags_offer_type_and_identifier"):
            fails.append("O-5 transactions are not tagged with offerType (1 intro / 2 promotional / 3 offer-code / 4 win-back) and offerIdentifier -- redemption counts without offer tagging cannot be separated from full-price purchases, so no offer can ever be judged")
        if ms.get("primary_metric") in ("redemption_count", "conversion_rate"):
            fails.append(f"O-5 offers are judged on '{ms.get('primary_metric')}' -- the redemption count tells you nothing about incrementality, and a 40% discount lifting conversion 20% still yields 0.72x baseline revenue per eligible user over the discounted period; judge 90-day revenue per ELIGIBLE user")
        if not ms.get("denominator_is_eligible"):
            fails.append("O-5 the measurement denominator is not the eligible population (rates over all users or all installs dilute the offer's actual audience and hide both leakage and lift)")
        triggered = "promotional" in by_type or "offer_code" in by_type
        if triggered and not ms.get("holdout_for_triggered_offers"):
            fails.append("O-5 a self-triggered offer (promotional and/or offer-code) runs without a holdout -- randomly withhold the offer from a slice of eligible users and compare 90-day revenue per user; without a holdout you cannot tell an offer that made money from one that discounted people who would have paid full price")
        if "winback" in by_type and not ms.get("winback_judged_by_lapse_cohort"):
            fails.append("O-5 a win-back offer is not judged by lapse-cohort comparison (Apple controls win-back targeting, so no in-window holdout exists; run one lapse window, leave another untouched, then swap, and track full-price renewals after the discount ends)")
        if not ms.get("tracks_full_price_renewals_after_discount"):
            warns.append("O-5 full-price renewals after the discount period ends are not tracked (an offer is only recovered money if subscribers renew at full price afterwards; the discounted period alone almost always reads as a loss)")
    # O-6 sequence
    seq = d.get("sequence") or {}
    if "offer_code" in by_type and not seq.get("offer_code_distribution_channel_exists"):
        fails.append("O-6 offer codes are launched without a distribution channel (email list, partner, podcast, event) -- offer codes are the one type you must distribute yourself, and the evidenced order puts them last, after win-back (self-surfacing) and promotional at the cancellation screen with a holdout")
    if "promotional" in by_type and seq.get("promotional_before_winback") and not seq.get("sequence_deviation_recorded"):
        warns.append("O-6 promotional offers precede any win-back offer without a recorded reason (the evidenced order is win-back first because Apple surfaces it with almost no code; deviating is allowed, silently deviating is not)")
    return fails, warns

def main():
    d = json.load(open(sys.argv[1]))
    fails, warns = check(d)
    for w in warns: print("WARN:", w)
    for f in fails: print("FAIL:", f)
    print(f"{'PASS' if not fails else 'FAIL'}: {len(fails)} fail(s), {len(warns)} warning(s) -- {d.get('app','?')}")
    sys.exit(0 if not fails else 1)

if __name__ == "__main__":
    main()
