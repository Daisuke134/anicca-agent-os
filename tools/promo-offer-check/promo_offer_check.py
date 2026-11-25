#!/usr/bin/env python3
"""promo-offer-check: deterministic gate for the PROMOTIONAL OFFER surface
(retention / win-back discounts for current and lapsed subscribers).
Stdlib only, offline, free.
Sources:
- RevenueCat "iOS Subscription Offers" (www-docs.revenuecat.com/docs/
  subscription-guidance/subscription-offers/ios-subscription-offers):
  promotional offers apply ONLY to existing and lapsed users, are NOT
  applied automatically, and require a subscription / In-App Purchase key
  uploaded so the offer request can be validated. Configure the offer in
  App Store Connect first (Reference Name + Promotional Offer Product
  Code; types: pay-up-front, pay-as-you-go, free). Before presenting,
  fetch and validate the PromoOffer via getPromotionalOffer /
  eligiblePromotionalOffers, selecting a specific offer by its Product
  Code identifier when several exist - not discounts.first blindly.
  Purchase must pass the validated offer: purchase(package:
  promotionalOffer:). If validation fails, default to normal terms.
  Eligibility is the app's own business logic, bounded by Apple's rule:
  the user must have, or have had, an active subscription in the group;
  Apple enforces that floor - a never-subscribed user is shown the
  regular product regardless.
- Apple / ASC (via RevenueCat + ASC Help summaries): up to 10 active
  promotional offers per subscription; a promotional offer can be taken
  even after an introductory offer was used.
Exit 0=PASS, 1=FAIL.
Extension PO-6..PO-9 added 2026-11-22 (spec hidden_files/promo-offer-routing-
signature-gate-spec-2026-11-22.md). Sources read in full:
- Apple ASC Help "Set up win-back offers" (developer.apple.com/help/app-store-
  connect/manage-subscriptions/set-up-win-back-offers): win-back offers are the
  only offer type Apple itself surfaces (Manage Subscriptions page, in-app
  win-back sheet iOS 18+, product page/editorial if promoted, redemption URL);
  configured PER PRODUCT (most recently lapsed product per group); before
  sharing a redemption URL, "Make sure you check customers eligibility before
  you send out the link"; a deleted offer's link shows "no longer available".
- RevenueCat "The beginner's guide to Apple win-back offers" (2024-12-03,
  updated 2025-02-14): promotional offers require the user to open the app;
  win-back adds App Store / Settings placements and streamlined purchasing
  (on by default; disable it when the app must sign the user in first);
  win-back requires StoreKit 2 + an uploaded in-app purchase key for tracking.
- Sonar comparison (secondary, checked against Apple docs 2026-10-01): only
  promotional offers need a server signature; the hard part is measuring
  whether an offer made money or just discounted people who would have paid
  full price. https://trysonar.app/blog/apple-subscription-offers-compared
The `routing` section is OPTIONAL and backward compatible: when absent, its
items are reported as WARN (unknown), the verdict is PARTIAL and exit is 2 -
never counted as a pass.
Exit 0=PASS, 1=FAIL, 2=PARTIAL (new-section unknown only).
"""
import json, sys
def check(d):
    f=[]
    dec=d.get("decision") or {}
    if not dec.get("presentation_decision_recorded"): f.append("PO-0 how promotional offers are used (which segment, which surface, which offer) is not recorded as a decision - drift is not a decision")
    if not dec.get("owner_recorded"): f.append("PO-0 no single promotional-offer owner is recorded")
    if not dec.get("asc_and_key_verified"): f.append("PO-0 the App Store Connect promotional-offer configuration (product code, type, duration, price) and the uploaded In-App Purchase / subscription key in RevenueCat are not verified from ASC / the dashboard (without the key, no offer request can be validated at all)")
    eli=d.get("eligibility") or {}
    if not eli.get("segment_from_subscription_history"): f.append("PO-1 the presented segment is not determined from subscription history (current subscriber / lapsed subscriber) - promotional offers exist only for those two segments")
    if not eli.get("never_subscribed_excluded"): f.append("PO-1 never-subscribed users are not explicitly excluded from promotional presentation (Apple will silently show them the regular product, so the app's promise and the store's terms diverge at purchase time)")
    if not eli.get("history_source_verified"): f.append("PO-1 the subscription-history source is not a verified one (CustomerInfo entitlements / server record) - a local or self-reported flag can present a signed discount to the wrong segment")
    fet=d.get("fetch") or {}
    if not fet.get("fetches_and_validates_before_display"): f.append("PO-2 the PromoOffer is not fetched and validated (getPromotionalOffer / eligiblePromotionalOffers) before its terms are shown - an unvalidated discount may not exist or may not apply to this user")
    if not fet.get("selects_by_offer_id"): f.append("PO-2 a specific offer is not selected by its Promotional Offer Product Code when several offers exist on one product (taking discounts.first couples the retention surface to ASC ordering and can show the cancellation offer in a win-back campaign, or vice versa)")
    if not fet.get("validation_failure_falls_back_to_standard"): f.append("PO-2 a validation failure does not fall back to normal package terms (RevenueCat's shape: promoOffer nil -> default to normal terms; showing discounted terms that then purchase at full price is a false promise)")
    pre=d.get("presentation") or {}
    if not pre.get("terms_shown_before_purchase"): f.append("PO-3 the offer terms (discounted price, duration, what it renews at) are not shown before purchase - a signed discount without disclosed renewal terms is a dark pattern")
    if not pre.get("purchase_passes_promo_offer"): f.append("PO-3 purchase does not pass the validated promotional offer (purchase(package:promotionalOffer:)) - a plain purchase(package:) charges the regular price no matter what the screen promised")
    if not pre.get("presentation_confined_to_segment_surfaces"): f.append("PO-3 promotional presentation is not confined to segment surfaces (retention / win-back / customer-center for current and lapsed users) and kept out of the first-sale onboarding paywall for new users, where its audience cannot redeem it")
    mea=d.get("measurement") or {}
    if not mea.get("offer_id_logged_per_view"): f.append("PO-4 the promotional offer identifier is not logged with offer views / purchase attempts (which offer was shown to whom is invisible, so take-rate per offer cannot be read)")
    if not mea.get("promo_purchase_distinguished"): f.append("PO-4 promotional purchases are not distinguished from regular purchases in measurement (discounted retention revenue is blended into full-price revenue and gross profit per offer cannot be judged)")
    if not mea.get("fallback_and_take_rate_measured"): f.append("PO-4 the validation-failure / ineligible fallback rate and the offer take-rate are not measured (the silent failure mode of this surface - validation failing for everyone - would look exactly like 'nobody wanted the discount')")
    ver=d.get("verification") or {}
    if not ver.get("sandbox_current_and_lapsed_e2e"): f.append("PO-5 the current-subscriber and lapsed-subscriber cases are not end-to-end verified in sandbox (manual testing with fresh, never-subscribed accounts can never exercise this surface at all)")
    if not ver.get("unit_tests_segments_and_fallback"): f.append("PO-5 segment resolution and the validation-failure fallback are not unit-tested (current / lapsed / never-subscribed / validation-failed)")
    if not ver.get("debug_offer_guarded"): f.append("PO-5 a debug / test path that forces a promotional presentation is not confined to debug builds or is unrecorded (an override reaching release, screenshots or E2E recordings promises a discount the audience cannot get)")
    w=[]
    r=d.get("routing")
    if r is None:
        w.append("PO-6..PO-9 routing section absent - offer-type routing / signature hygiene / link-distribution checks / incrementality are unknown (not a pass)")
    else:
        if not r.get("tool_routing_recorded_per_segment"): f.append("PO-6 no per-segment routing across Apple's four offer tools is recorded (intro=new subscribers, promotional=current/past subscribers reachable in-app, win-back=lapsed subscribers Apple itself surfaces, offer codes=off-store distribution) - one tool used for every segment silently misses the segments that tool cannot reach")
        if not r.get("promo_not_used_as_only_channel_for_unreachable_lapsed"): f.append("PO-6 promotional offers are the only channel planned for lapsed subscribers who no longer open the app (a promotional offer can only be seen inside the app; Apple-surfaced win-back offers or a checked redemption URL are the routes that reach non-openers)")
        if not r.get("signature_server_side_with_fresh_nonce"): f.append("PO-7 the promotional-offer signature is not generated server-side with a unique nonce and a fresh timestamp per request (promotional offers are the only offer type needing a signature; a reused or client-generated signature fails validation or can be replayed)")
        if not r.get("eligibility_checked_before_sending_any_link"): f.append("PO-8 eligibility is not checked before a redemption URL / offer link is sent (Apple: check customers' eligibility before you send out the link - an ineligible recipient gets a dead offer and a broken promise)")
        if not r.get("dead_link_and_streamlined_decision_recorded"): f.append("PO-8 the dead-link case (deleted/expired offer shows 'no longer available') and the streamlined-purchasing decision (on = redeem completes in the App Store; off = route into the app when sign-in must happen first) are not recorded")
        if not r.get("incrementality_measured_with_control"): f.append("PO-9 no control (holdout or would-have-paid-full comparison) separates recovered subscribers from subscribers who would have returned at full price - take-rate alone counts discounted full-payers as wins")
        if not r.get("recovered_margin_measured"): f.append("PO-9 recovered margin (net revenue after discount and store fee) is not measured per offer - gross take-rate can rise while gross profit falls")
        if r.get("discount_escalates_across_offers"): f.append("PO-9 discount depth escalates across successive offers to the same segment (training subscribers to wait for a deeper discount; cf. win-back timing gate WT-11)")
    return f, w
if __name__=="__main__":
    data=json.load(open(sys.argv[1])); fails, warns = check(data)
    if fails:
        print(f"FAIL ({len(fails)} fails, {len(warns)} warns):")
        [print(" -",x) for x in fails]
        [print(" ~",x) for x in warns]; sys.exit(1)
    if warns:
        print(f"PARTIAL (0 fails, {len(warns)} warns):")
        [print(" ~",x) for x in warns]; sys.exit(2)
    print("PASS")
