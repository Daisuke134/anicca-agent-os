#!/usr/bin/env python3
"""trial-recovery-check: deterministic gate for recovering users whose free
trial expired without ever paying (trial-never-paid cohort).
Stdlib only, offline, free. Exit 0 = PASS, 1 = FAIL.

Sources (read in full 2026-11-21):
- Winback HQ (vendor primary, full read) https://winbackhq.com/
  Lost subscribers sort into three kinds needing three different messages:
  cancelled (chose to leave), card failed (did not mean to leave; one-tap fix,
  NO discount), and trial ended / never paid ("they never really started;
  usually the biggest group; a reminder of what they set up, and a short
  extension if you allow it"). Limits are set per group (max offer, budget);
  every message carries a unique return code; a return counts within 60 days
  of the message; judgement is recovered revenue per person, re-measured with
  a fresh export 30 days later. Vendor claims are encoded as design rules,
  not as expected results.
- Adapty, Trial conversion rates for in-app subscriptions (2026 refresh,
  full read) https://adapty.io/blog/trial-conversion-rates-for-in-app-subscriptions/
  Totango research cited there: nearly 50% of eventual conversions happen
  AFTER the formal trial period expires, so conversion must be tracked by
  cohort beyond the trial end date, not as a snapshot at expiry.
- Superwall result via secondary summary (Consumoteca 2026 benchmarks,
  secondary -- labelled as such, not a primary read): targeting unsubscribed
  users with additional trial offers increased trial starts by 240% and
  proceeds per user by 97%. Encoded only as support for TR-5 (an additional
  trial offer is a real lever), never as an expected lift.

Separation from existing gates: trial-check = trial length and the
pre-charge reminder (in-trial); winback-check / winback-timing-check =
subscribers who paid at least once and then expired; dunning-check =
billing failure; later-paywall-check = in-app second surface for free
users at intent actions. This gate is only the never-paid trial cohort
and what happens after their trial ends.
"""
import json, sys


def check(d):
    fails = []
    c = d.get("cohort") or {}
    # TR-1 cohort separated from both paid-lost kinds
    if not (c.get("separated_trial_never_paid") and c.get("distinct_from_cancelled_paid")
            and c.get("distinct_from_card_failed")):
        fails.append("TR-1 trial-never-paid is not a separate cohort (Winback HQ: cancelled / card-failed / trial-never-paid are three kinds of lost needing three different messages; one merged 'we miss you' list sends the wrong note to at least two of them)")
    # TR-2 cohort size + revenue recorded
    if not c.get("size_and_revenue_recorded"):
        fails.append("TR-2 the trial-never-paid cohort's size and revenue-at-stake are not recorded (vendor primary calls it usually the biggest lost group; an uncounted biggest group is managed by anecdote)")
    m = d.get("measurement") or {}
    # TR-3 post-expiry cohort window >=30d, by start date
    w = m.get("window_days_after_expiry") or 0
    if w < 30 or not m.get("cohort_by_start_date"):
        fails.append(f"TR-3 conversions are not tracked by cohort for >=30 days after trial expiry (window={w}d, cohort_by_start_date={m.get('cohort_by_start_date')}); Totango via Adapty: nearly 50% of eventual conversions happen after the trial expires -- a snapshot at expiry misreads half the outcome")
    msg = d.get("message") or {}
    # TR-4 message built from what the user set up
    if not msg.get("built_from_user_setup") or msg.get("generic_coupon_only"):
        fails.append("TR-4 the recovery message is not built from what this user set up during the trial (their own answers / plan / progress); the trial cohort 'never really started', so the evidenced note is a reminder of what they set up -- a generic coupon is the merged-list failure of TR-1 in copy form")
    o = d.get("offer") or {}
    # TR-5 offer is a short extension / second trial, capped, once per user
    if o.get("type") not in ("short_extension", "second_trial"):
        fails.append(f"TR-5 the recovery offer type is {o.get('type')!r}, not a short extension / additional trial (the evidenced lever for never-paid trials; Superwall via secondary summary: additional trial offers to unsubscribed users raised trial starts and proceeds per user)")
    if not o.get("capped"):
        fails.append("TR-5 the recovery offer has no recorded cap (per-group maximum offer and budget are set before any message, per the vendor primary)")
    if not o.get("once_per_user"):
        fails.append("TR-5 the extension / second trial is not limited to once per user (repeatable free trials train waiting and farm the offer)")
    # TR-6 no discount deepening; card-failed cohort never gets the discount
    if o.get("discount_deepening_sequence"):
        fails.append("TR-6 the recovery path deepens the discount across touches (a deeper second discount teaches waiting and cuts gross profit; same root as later-paywall / winback-timing non-deepening)")
    if o.get("discount_to_card_failed"):
        fails.append("TR-6 a discount is offered to the card-failed cohort (they did not mean to leave; they get a one-tap card fix, not a discount -- a card problem is not a price problem)")
    s = d.get("segmentation") or {}
    # TR-7 segmented by trial engagement
    if not s.get("by_trial_engagement") or not s.get("activated_vs_not_different"):
        fails.append("TR-7 the cohort is not segmented by trial engagement with different treatment for activated vs never-activated users (someone who finished the core experience and someone who never opened it did not lose the same thing)")
    sup = d.get("suppression") or {}
    # TR-8 suppression + state rechecked at touch time
    if not (sup.get("excludes_converted_and_subscribed") and sup.get("excludes_card_failed")):
        fails.append("TR-8 suppression is incomplete: already-converted / currently subscribed users and the card-failed cohort must both be excluded from trial recovery (offering an extension to a paying subscriber, or a discount path to a billing failure, is a trust and margin error)")
    if not sup.get("state_rechecked_at_touch"):
        fails.append("TR-8 entitlement state is not rechecked at touch time (a user who converted yesterday must not receive today's recovery note)")
    ch = d.get("channel") or {}
    # TR-9 reachability recorded + in-app return surface
    if not ch.get("reachability_recorded"):
        fails.append("TR-9 reachability of this cohort is not recorded (push permission and/or $email presence measured for the cohort itself; an unmeasured channel plan assumes contact data the app may never have collected)")
    if not ch.get("in_app_return_surface"):
        fails.append("TR-9 there is no in-app return surface for this cohort (on their next organic open, the extension offer must be present in-app; outbound channels alone miss everyone who returns on their own)")
    a = d.get("attribution") or {}
    # TR-10 attribution + 30-60d return window
    rw = a.get("return_window_days") or 0
    if not a.get("per_person_or_cohort_code") or not (30 <= rw <= 60):
        fails.append(f"TR-10 returns are not attributed per person/cohort with a 30-60 day return window (code={a.get('per_person_or_cohort_code')}, window={rw}d; the vendor primary counts a return within 60 days of the message, person by person)")
    # TR-11 judged on money
    if m.get("primary_metric") != "revenue_per_expired_trial_user":
        fails.append(f"TR-11 the primary metric is {m.get('primary_metric')!r}, not revenue per expired-trial user with recovered subscribers counted (opens and clicks do not pay; the vendor primary re-measures recovered revenue with a fresh export 30 days later)")
    t = d.get("timing") or {}
    # TR-12 timing: first touch <=7d, capped touches, intent surface after
    ft = t.get("first_touch_days_after_expiry")
    if ft is None or ft > 7:
        fails.append(f"TR-12 the first recovery touch is {ft} days after expiry (must be <=7; the setup the user made is freshest in the first week, and later-paywall evidence puts intent-window value early)")
    mt = t.get("max_touches") or 0
    if mt < 1 or mt > 3:
        fails.append(f"TR-12 recovery touches are not capped at 1-3 (max_touches={mt}; uncapped recovery is nagging and trains ignoring every later message)")
    if not t.get("intent_surface_after"):
        fails.append("TR-12 after the capped touches there is no intent-triggered in-app surface (recovery continues only when the user shows intent, per the later-paywall Gate; it does not continue as outbound pressure)")
    return fails


def main():
    if len(sys.argv) != 2:
        print("usage: trial_recovery_check.py <state.json>"); return 2
    with open(sys.argv[1]) as f:
        d = json.load(f)
    fails = check(d)
    total = 12
    passed = total - len({x.split()[0] for x in fails})
    for x in fails:
        print(f"FAIL {x}")
    print(f"RESULT {'PASS' if not fails else 'FAIL'} app={d.get('app')} pass={passed}/{total} fails={len(fails)}")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
