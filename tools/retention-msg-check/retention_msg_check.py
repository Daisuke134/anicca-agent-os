#!/usr/bin/env python3
"""retention-msg-check: deterministic gate for Apple Retention Messaging
(cancel-confirmation screen). Stdlib only, offline, free. Exit 0=PASS, 1=FAIL.

Sources (read in full 2026-11-21):
- RevenueCat, "How to set up your first Apple retention message in App
  Store Connect" (2026-11-05, updated 2026-11-06)
  https://www.revenuecat.com/blog/growth/apple-retention-messaging
  GA to every developer in ASC on 2026-11-04, no code/server/access
  request. One message per subscription; offer eligibility only in ASC
  (min paid duration from 1 month, so trial users cannot get offers;
  wait between offers from 2 months). 22M messages / 309 apps: offer
  acceptance ~1.1%, plan-switch ~0.6%. Dipsea: 50% off raised save rate
  22.1% vs 18.8% but revenue per subscriber fell to $1.24 vs $3.16 and
  fewer stayed set to renew -- save rate alone is the wrong judge.
  Top cancel reasons (Google Play surveys via RC): not enough usage
  37%, cost 35% -- a discount only helps the price group. Never put
  price/discount wording in header/body: Apple shows the offer
  separately and rejects messages that mention it.
- Lightning Studio guide (2026-11-08) citing Apple ASC Help / WWDC26 309
  https://lightning-studio.org/blog/apple-retention-messages-subscriptions-setup-guide/
  Limits: <=10 messages/app, <=10 retention offers per plan type, image
  3840x2160 or 5244x2950, offer replaces image for eligible users,
  offerType=5 in signed transactions (backends expecting 1-4 misbucket),
  rejections: prices/offers in text, coercion, unverifiable claims /
  superlatives, all-caps; localise for every storefront sold; sandbox
  QA incl. the ineligible version; measure 30-60 days (save rate, full-
  price renewal after offer, refunds) before requesting real-time API.
  Apple WWDC26: average save-rate increase +1.4pp, promo-offer +5.5pp.
- ASC save-rate caveat (Dodecaidr, 2026-11-16, via search read): Apple's
  Save Rate counts leaving the screen without cancelling as a save, so
  it must be read with voluntary churn, never alone.

Separation: exit-survey = in-app reason capture at cancel intent;
winback = after lapse; cancel-check = in-app cancel flow; dunning =
billing failure. This gate is only Apple's system cancel-confirmation
screen (Settings/App Store), configured in App Store Connect.
"""
import json, sys


def check(d):
    fails = []
    c = d.get("config") or {}
    if not c.get("configured_in_asc") or not c.get("review_approved"):
        fails.append("RM-1 no retention message is configured in App Store Connect and approved (GA to all developers 2026-11-04, no code or access request; an unconfigured screen shows subscribers nothing -- a draft or a plan is not a message)")
    cov = d.get("coverage") or {}
    if not cov.get("every_sold_subscription_assigned") or not cov.get("one_message_per_subscription"):
        fails.append("RM-2 coverage is incomplete (every sold subscription must be assigned exactly one message -- one subscription carries only one message at a time, up to 10 messages per app; an unassigned plan reaches the cancel screen with no message at all)")
    msg = d.get("message") or {}
    if not msg.get("angle_from_recorded_cancel_reasons"):
        fails.append("RM-3 the message angle is not chosen from recorded cancel reasons (exit survey / reviews / support; in ASC every canceller of a plan sees the same text, so the angle must fit the recorded majority reason -- top reasons are low usage 37% and cost 35%, and a generic 'we will miss you' fits neither)")
    if not msg.get("names_specific_loss_functional_and_emotional"):
        fails.append("RM-4 the message does not name the specific loss (strongest form pairs a functional loss -- the named features/content the subscriber gives up -- with why it matters emotionally; a value claim without a named loss gives no reason to stay)")
    if msg.get("price_or_discount_wording_in_text"):
        fails.append("RM-5 header/body contains price or discount wording (Apple rejects it: every subscriber sees the text including those ineligible for the offer; price lives only in the attached offer, rendered by Apple)")
    if msg.get("coercion_or_unverifiable_claims") or msg.get("all_caps_or_shouting_style"):
        fails.append("RM-6 copy uses coercion, unverifiable claims/superlatives, or shouting style (App Review rejects coercive and unprovable claims and non-plain style; factual loss statements are the accepted form)")
    if not d.get("localized_for_every_storefront_sold"):
        fails.append("RM-7 the message is not localised for every storefront where the subscription is sold (ASC has no auto-translate on this path; an unlocalised storefront shows a message its subscribers cannot read as intended)")
    img = d.get("image") or {}
    if not (img.get("present_real_app_content") or img.get("deliberate_text_only_recorded")):
        fails.append("RM-8 no image of real app content and no recorded deliberate text-only choice (the image is what ineligible subscribers see instead of the offer; original screens/content outperform generic stock, at 3840x2160 or 5244x2950, without long text)")
    off = d.get("offer") or {}
    if off.get("attached") and not off.get("price_is_recorded_top_cancel_reason"):
        fails.append("RM-9 an offer is attached but price is not a recorded top cancel reason (a discount only helps the price group; for low-usage cancellers it buys back people who will not use the app -- Dipsea: 50% off saved slightly more people and earned less than half the revenue per subscriber)")
    if off.get("attached"):
        md = off.get("min_paid_duration_months") or 0
        wb = off.get("wait_between_offers_months") or 0
        if md < 1 or wb < 2 or off.get("trial_users_eligible"):
            fails.append(f"RM-10 offer eligibility is loose (min_paid={md}mo, wait={wb}mo, trial_eligible={off.get('trial_users_eligible')}; ASC floor is 1 month paid -- trial users cannot receive offers there -- and wait starts at 2 months; loose eligibility trains subscribers to open the cancel screen for a discount)")
        if (off.get("discount_pct") or 0) > 30 or (off.get("duration_periods") or 0) > 2:
            fails.append(f"RM-11 the retention offer is deep or long (discount={off.get('discount_pct')}%, periods={off.get('duration_periods')}; start conservative -- a modest discount for 1-2 billing periods; acceptance across 22M messages was only ~1.1%, so depth mostly subsidises people who would have stayed or returned anyway)")
    meas = d.get("measurement") or {}
    if not meas.get("save_rate_read_with_voluntary_churn_and_revenue") or meas.get("judged_on_save_rate_only"):
        fails.append("RM-12 the message is judged on save rate alone (Apple's save counts leaving the screen without cancelling; Dipsea's discount won save rate and lost revenue and set-to-renew -- judge on save rate together with voluntary churn, realised revenue per subscriber, and still-set-to-renew over 30-60 days)")
    ops = d.get("operations") or {}
    if not ops.get("offertype5_handled_separately") or not ops.get("sandbox_qa_eligible_and_ineligible") or ops.get("realtime_api_requested_before_asc_baseline"):
        fails.append("RM-13 operations are incomplete (retention redemptions arrive as offerType 5 -- backends expecting types 1-4 misbucket the revenue; sandbox QA must cover both the eligible offer version and the ineligible image version; the real-time API is requested only after a 30-60 day ASC baseline, not before)")
    return fails


def main():
    if len(sys.argv) != 2:
        print("usage: retention_msg_check.py <state.json>"); return 2
    with open(sys.argv[1]) as f:
        d = json.load(f)
    fails = check(d)
    total = 13
    passed = total - len({x.split()[0] for x in fails})
    for x in fails:
        print(f"FAIL {x}")
    print(f"RESULT {'PASS' if not fails else 'FAIL'} app={d.get('app')} pass={passed}/{total} fails={len(fails)}")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
