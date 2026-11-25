#!/usr/bin/env python3
"""winback-check: deterministic gate for Apple-native win-back design in subscription apps.
Stdlib only, offline, free. Sources (read in full 2026-11-13):
- RevenueCat, The beginner's guide to Apple win-back offers (2024-12-03, updated 2026-09-11):
  win-back offers are free/discounted offers for eligible churned users, configured per
  subscription product in App Store Connect; the subscription must already be App Review
  approved; requires iOS 18+ / StoreKit 2; eligibility is set by Minimum Paid Duration,
  Time Since Last Subscribed, and optional Wait Between Offers; placements are the App
  Store (incl. product page / editorial if promoted), in-app (StoreKit message sheet or
  custom paywall), the Subscriptions section of the customer's Apple account, and a
  unique URL; performance is read in RevenueCat Charts segmented/filtered by Offer type.
  https://www.revenuecat.com/blog/growth/guide-to-apple-win-back-offers
- RevenueCat, How to win back lost customers (Hannah Parvaz, Aperture, 2024-06-27,
  updated 2026-09-11): a win-back target is someone who turned off auto-renew AND whose
  billing period has elapsed; understand the churn reason first and personalise the
  offer/message to it; use multiple channels (push can lift conversion >25%, plus
  in-app and email); A/B test discount depth (20% vs 30% converted the same — keep the
  margin); be persistent but not annoying, timing around when subscribers actually
  change billing status; author's own rates were 6% at month 2 / 8% at month 6, best
  in peer group 35% at month 6.
  https://www.revenuecat.com/blog/growth/win-back-customers-how-to-guide
- Apple limits via App Store Connect help, as quoted in in-house
  app-store-offer-codes-winback-spec-2026-11-06: up to 350 win-back offers per
  subscription, at most 5 active per storefront, minimum run 3 days; Minimum Paid
  Duration 1-24 months (or 3/4/5 years); Time Since Last Subscribed 1-24 months with
  BOTH a minimum and a maximum required; eligibility attaches to the most recently
  lapsed product in each group; reference name / identifier / price cannot be changed
  after creation. Splitting offers by lapse window beat one blanket 1-24 month offer.
- In-house affirmation-winback-spec-2026-11-05: four states must stay separate —
  A cancelled-but-still-active (save banner, highest leverage), B voluntarily expired,
  C involuntarily expired (billing error -> dunning spec, never a discount win-back),
  D trial-cancelled (value re-presentation, not a discount); post-expiry sequence is
  7/30/60/90 days, capped, quiet hours respected; reactivation is read by state and
  plan against a no-treatment holdout (monthly reactivates ~20.1% and annual ~5%
  within a year on RevenueCat State of Subscription Apps 2026, so natural return must
  not be counted as the campaign's effect), and annual reactivation does not move
  with discount size (4.4-5.9% across discount bands).
Exit 0 = PASS, 1 = FAIL. Warnings do not fail.
Input JSON: {app, apple_winback_configured, subscription_app_review_approved,
 uses_storekit2, segments_handled:[...], involuntary_routed_to_dunning,
 winback_trigger, save_banner_for_cancelled_active, offers:[{min_paid_months,
 lapse_min_months, lapse_max_months, wait_between_months, run_days, active_count,
 discount_escalates}], channels:[...], message_style, reason_based_personalisation,
 churn_reason_captured, touches:[days...], quiet_hours_respected, stops_on_renewal,
 measurement:{denominator, split_by_plan, split_by_segment, holdout, recovered_mrr_tracked,
 window_days, benchmark_by_plan}}
"""
import json, sys

REQUIRED_SEGMENTS = {"cancelled_still_active", "voluntary_expired", "trial_cancelled"}

def check(d):
    fails, warns = [], []
    if not d.get("apple_winback_configured"):
        fails.append("W-0 no Apple win-back offer configured in App Store Connect (a spec or a proposal table is not an offer a lapsed subscriber can redeem)")
    if not d.get("subscription_app_review_approved"):
        fails.append("W-0 subscription product is not recorded as App Review approved (Apple allows win-back offers only on approved products)")
    if not d.get("uses_storekit2"):
        fails.append("W-0 StoreKit 2 is not in use (Apple win-back offers require iOS 18+ / StoreKit 2, including for RevenueCat event tracking)")
    segs = set(d.get("segments_handled") or [])
    missing = REQUIRED_SEGMENTS - segs
    if missing:
        fails.append(f"W-1 segments not handled separately: {sorted(missing)} (cancelled-but-active, voluntarily expired, and trial-cancelled churn need different handling; one treatment for all churn is the blanket failure)")
    if not d.get("involuntary_routed_to_dunning"):
        fails.append("W-1 involuntary (billing-error) churn is not routed away to dunning/grace handling (a discount win-back treats a card problem as a price problem and cannot fix it)")
    if d.get("winback_trigger") != "subscription_expired":
        fails.append(f"W-2 win-back trigger is {d.get('winback_trigger')!r}, not subscription_expired (firing the win-back discount at cancel time spends margin on people still inside their paid period; the offer belongs at/after actual expiry)")
    if not d.get("save_banner_for_cancelled_active"):
        fails.append("W-2 no save treatment for the cancelled-but-still-active window (that window is the highest-leverage one: the user still has access and something to lose; expiry-only win-back fights the ~5% annual ceiling alone)")
    offers = d.get("offers") or []
    if d.get("apple_winback_configured") and not offers:
        fails.append("W-3 win-back is marked configured but no offer eligibility is recorded (eligibility dials are the offer; unrecorded dials cannot be audited)")
    for i, o in enumerate(offers):
        tag = f"W-3 offer[{i}]"
        mp = o.get("min_paid_months")
        if mp is None or not (1 <= mp <= 24 or mp in (36, 48, 60)):
            fails.append(f"{tag} minimum paid duration is {mp!r} months (Apple allows 1-24 months, or 3/4/5 years)")
        lo, hi = o.get("lapse_min_months"), o.get("lapse_max_months")
        if lo is None or hi is None or not (1 <= lo < hi <= 24):
            fails.append(f"{tag} time-since-last-subscribed window is {lo!r}-{hi!r} (Apple requires BOTH bounds inside 1-24 months, min < max)")
        wb = o.get("wait_between_months")
        if wb is not None and not (2 <= wb <= 24):
            fails.append(f"{tag} wait-between-offers is {wb!r} months (Apple allows 2-24 months when set)")
        if o.get("run_days") is not None and o.get("run_days") < 3:
            fails.append(f"{tag} run length is {o.get('run_days')} days (Apple minimum run is 3 days)")
        if o.get("active_count") is not None and o.get("active_count") > 5:
            fails.append(f"{tag} {o.get('active_count')} active offers in one storefront (Apple allows at most 5 per storefront)")
        if o.get("discount_escalates"):
            fails.append(f"{tag} discount escalates over the sequence (annual reactivation is flat at 4.4-5.9% across discount bands and 20% vs 30% converted the same in Parvaz's A/B — escalation burns margin without lifting the ceiling)")
    if len(offers) == 1:
        lo, hi = offers[0].get("lapse_min_months"), offers[0].get("lapse_max_months")
        if lo is not None and hi is not None and (hi - lo) >= 12:
            fails.append("W-3 a single offer blankets a lapse window of 12+ months (the documented failure: one 1-24 month offer redeemed poorly until it was split by lapse window — recent lapses and year-old lapses must not see the same offer)")
    channels = set(d.get("channels") or [])
    if len(channels) < 2:
        fails.append(f"W-4 fewer than two win-back channels {sorted(channels)} (Parvaz: use multiple channels — push alone or in-app alone leaves the lift on the table; push can lift conversion >25%)")
    if d.get("message_style") in (None, "generic_we_miss_you"):
        fails.append("W-5 message is generic ('we miss you') or undefined (win-back works by addressing the specific reason and naming the specific value missed, not by sentiment)")
    if not d.get("reason_based_personalisation"):
        fails.append("W-5 offers/messages are not varied by the recorded churn reason (price, unused, no-effect, switched, accidental churn are different objections; one message answers none of them)")
    if not d.get("churn_reason_captured"):
        fails.append("W-5 no churn reason is captured at cancellation (without the reason there is nothing to personalise with — capture is the precondition, not an extra)")
    touches = d.get("touches") or []
    if not touches:
        fails.append("W-6 no post-expiry touch sequence is defined (a single send is not a campaign; the in-house cadence is 7/30/60/90 days)")
    if len(touches) > 4:
        fails.append(f"W-6 {len(touches)} post-expiry touches (persistent but not annoying: the sequence is capped at 4 and stops at day 90)")
    if touches and max(touches) > 90:
        fails.append(f"W-6 touches extend to day {max(touches)} (past day 90 the sequence stops; indefinite re-mailing a lapsed subscriber is harassment, not win-back)")
    if not d.get("quiet_hours_respected"):
        fails.append("W-6 quiet hours are not respected for win-back pushes (in-house push rule: nothing between 22:00 and 08:00)")
    if not d.get("stops_on_renewal"):
        fails.append("W-6 the sequence does not stop on renewal (continuing to offer a discount to someone who already came back trains discount-waiting and wastes the cap)")
    m = d.get("measurement") or {}
    if m.get("denominator") != "eligible_lapsed":
        fails.append(f"W-7 reactivation denominator is {m.get('denominator')!r}, not eligible lapsed subscribers (rating win-back over installs or all churn hides who the offer could actually reach)")
    if not m.get("split_by_plan"):
        fails.append("W-7 reactivation is not split by plan (the ceilings differ by an order of magnitude: monthly ~20.1% vs annual ~5% reactivate within a year — an unsplit average judges an annual cohort by a monthly ceiling)")
    if not m.get("split_by_segment"):
        fails.append("W-7 reactivation is not split by segment (cancelled-active saves, voluntary expiries, and trial cancellations must not be averaged into one rate)")
    if not m.get("holdout"):
        fails.append("W-7 no no-treatment holdout (roughly one in five monthly churners returns anyway; without a holdout, natural return is booked as campaign effect)")
    if not m.get("recovered_mrr_tracked"):
        fails.append("W-7 recovered revenue (MRR) is not tracked (redemption counts alone reward cheap, fast-churning returns; win-back is judged on money that stays)")
    if m.get("window_days") is not None and m.get("window_days") < 90:
        fails.append(f"W-7 measurement window is {m.get('window_days')} days (returns arrive late; read at least 90 days before judging a win-back cohort)")
    if not m.get("benchmark_by_plan"):
        warns.append("W-7 no per-plan reactivation benchmark recorded (compare against monthly ~20.1% / annual ~5% within a year before calling a rate good or bad)")
    return fails, warns

def main():
    with open(sys.argv[1]) as fh:
        d = json.load(fh)
    fails, warns = check(d)
    for w in warns:
        print(f"WARN {w}")
    for f in fails:
        print(f"FAIL {f}")
    print(f"{'PASS' if not fails else 'FAIL'} {d.get('app','?')}: {len(fails)} fail(s), {len(warns)} warning(s)")
    sys.exit(0 if not fails else 1)

if __name__ == "__main__":
    main()
