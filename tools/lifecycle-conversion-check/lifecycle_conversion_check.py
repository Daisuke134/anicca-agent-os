#!/usr/bin/env python3
"""lifecycle-conversion-check: deterministic gate for DELAYED / LIFECYCLE
conversion (subscriptions that start weeks to months after install).
Stdlib only, offline, free. Exit 0 = PASS, 1 = FAIL.

Sources (read in full 2026-11-21):
- RevenueCat Sub Club, Mike Charniatsou (Flo), published 2026-11-11:
  https://www.revenuecat.com/blog/growth/mike-charniatsou-flo-sub-club-podcast-2026
  40% of Flo subscriptions start more than six months after install.
  Core use case stays free; the team watches needs evolve and steps in
  only when it has something new of value to offer. "Your paywall
  conversion is not your monetization strategy" -- conversion is a life
  cycle (trial start, activation, retention), and a test that lifts the
  onboarding paywall can still lose money downstream (BoldVoice: removed
  the X, conversion jumped, refunds spiked). Keep analyzing experiments
  long after rollout; once a year reconcile the sum of reported uplifts
  against actual business growth. Failed-test rule: iterate only on new
  EVIDENCE, not a new explanation -- Flo reran a -10% test on an
  explanation and lost again; dissecting the audience showed ~75% of
  users were never assigned a phase because the question was
  unanswerable, and those users hit a dead-end "sorry" screen. Rewriting
  the question and letting unassigned users move on quietly gave +23%
  on the third iteration, confirmed by a fourth blackout test that
  removed the section and lost. Marketing found a need first (an ad
  narrative gaining traction); product built a dedicated branch that
  acknowledges the arrival source. Borrow the idea, not the solution:
  the Blinkist trial-reminder paywall, copied pixel-to-pixel, failed at
  both Loona and Flo. Flo uses proxy events to make early calls when
  the real conversion (delayed trial activation) is slow.
- Adapty, Paywall Optimization / State of Paywalls 2026 (read in full
  2026-11-21): https://adapty.io/blog/paywall-optimization-tests/
  7 in 10 paywall views happen after the first session; subscriptions
  started at later paywalls bring 38% of revenue (48% in Lifestyle and
  Utilities). Easiest first segment is lapsed subscribers: 56% of
  returning subscribers who take an offer are still paying three months
  later, versus about 1 in 10 new users who start with one.

Separation from existing gates: later-paywall-check covers a second
in-app surface shown after an intent action; winback-timing covers
lapsed-subscriber offers; paywall-decision covers the hard/soft model
choice. This gate covers only the time dimension: measuring, waiting
for, and correctly learning from conversions that arrive late.
"""
import json, sys


def check(d):
    fails = []
    m = d.get("measurement") or {}
    # LC-1 late conversion is measured as its own share
    if not m.get("late_share_tracked"):
        fails.append("LC-1 the share of subscriptions starting late (after Day 35, and after 6 months) is not tracked (Flo: 40% of subscriptions start after six months; Adapty: later paywalls bring 38% of revenue -- a funnel judged only to Day 35 cannot see this money at all)")
    # LC-2 success is not judged on the early window alone
    if m.get("judged_on_day35_only"):
        fails.append("LC-2 monetization is judged on Day 35 / onboarding conversion alone (Flo: 'your paywall conversion is not your monetization strategy'; conversion is a life cycle of trial start, activation and retention, and an onboarding win can lose downstream, e.g. via refunds)")
    s = d.get("strategy") or {}
    # LC-3 core use case stays free; no squeeze-only Day 1/Day 7 strategy
    if not s.get("core_stays_free"):
        fails.append("LC-3 the core use case does not stay free for non-payers (Flo keeps cycle tracking free and protects the relationship instead of monetizing hard on day one and day seven; squeezing the lemon has a ceiling)")
    # LC-4 needs-evolution triggers are watched
    if not s.get("needs_triggers_defined"):
        fails.append("LC-4 no needs-evolution triggers are defined or watched (Flo steps in when a user's life stage / need changes -- trying to conceive, pregnancy, perimenopause; willingness to pay moves with the need, not with the install date)")
    # LC-5 late offers carry genuinely new value
    if not s.get("late_offer_requires_new_value"):
        fails.append("LC-5 late monetization does not require something new of value to offer (Flo converts users 3, 6 and 12 months later by bringing new value besides the core offering; re-showing the same paywall is pressure, not a lifecycle strategy)")
    # LC-6 proxy events defined for delayed conversion
    if not m.get("proxy_events_defined"):
        fails.append("LC-6 no proxy events are defined for delayed conversion (when the real event is a trial activation months later, early experiment calls need a validated proxy; without one, late-converting tests are killed or kept on noise)")
    e = d.get("experiments") or {}
    # LC-7 experiments re-analyzed long after rollout + annual reconciliation
    if not e.get("reanalyzed_after_rollout") or not e.get("annual_reconciliation"):
        fails.append("LC-7 experiments are not re-analyzed long after rollout and there is no annual reconciliation of claimed uplifts against actual business growth (Flo: if the business did not grow by the sum of reported wins, the difference is wins that were never business wins)")
    # LC-8 iterate only on new evidence; audience dissected before a rerun
    if e.get("rerun_on_explanation_only") or not e.get("audience_dissected_before_rerun"):
        fails.append("LC-8 failed tests can be rerun on a new explanation without new evidence or an audience dissection (Flo reran a -10% test on an explanation and lost the same way; 'explanation tells you what you want to be true, evidence tells you where to look')")
    o = d.get("onboarding") or {}
    # LC-9 unanswerable-question guard: assignment rate + quiet pass-through
    ar = o.get("assignment_rate_measured")
    if not ar or o.get("unassigned_hits_dead_end"):
        fails.append("LC-9 segmentation-question assignment is unmeasured or unassigned users hit a dead end (Flo: ~75% of users were never assigned a phase because the question was unanswerable, and they were shown a 'sorry, we couldn't pinpoint it' screen; unassigned users must move quietly to the next section)")
    # LC-10 big wins confirmed by a blackout / reversal test
    if not e.get("blackout_test_for_big_wins"):
        fails.append("LC-10 large wins are trusted without a blackout / reversal confirmation (Flo did not trust its +23% until a fourth test removed the new section entirely and lost, confirming the uplift was real)")
    # LC-11 acquisition narrative carried through in a dedicated branch
    if not s.get("source_branch_acknowledges_arrival"):
        fails.append("LC-11 no dedicated branch carries an acquisition narrative through onboarding (Flo: an ad narrative gaining traction at Meta became a branch that acknowledges which ad the user arrived from and asks tailored questions; marketing can validate needs faster than the product funnel, so changes are shared weekly)")
    # LC-12 imported patterns are hypotheses; returning segment tracked 3 months
    if s.get("imported_pattern_assumed_proven"):
        fails.append("LC-12 an imported winner pattern is treated as proven in this app (Flo copied the Blinkist trial-reminder paywall pixel-to-pixel and it failed at both Loona and Flo: borrow the idea, not the solution -- an external result is a hypothesis until this funnel's evidence confirms it)")
    r = d.get("returning") or {}
    if not r.get("returning_segment_tracked_months") or (r.get("returning_segment_tracked_months") or 0) < 3:
        fails.append("LC-13 returning / lapsed subscribers are not tracked as a distinct late segment for at least 3 months (Adapty: 56% of returning subscribers who take an offer are still paying three months later, versus about 1 in 10 new users who start with one -- the easiest late segment is invisible without its own cohort)")
    return fails


def main():
    if len(sys.argv) != 2:
        print("usage: lifecycle_conversion_check.py <state.json>"); return 2
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
