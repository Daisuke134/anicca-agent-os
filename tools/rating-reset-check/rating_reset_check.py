#!/usr/bin/env python3
"""rating-reset-check: deterministic gate for the App Store ratings-reset
decision on a new version. Stdlib only, offline, free.
Sources (read in full 2026-11-23):
- Apple App Store Connect Help, reset overview rating (as quoted in full by
  AppRanker, https://appranker.net/blog/reset-app-store-rating): the reset is
  chosen per version and takes effect when that version is RELEASED, in ALL
  regions simultaneously; written reviews are NOT reset and stay visible; a
  "recently reset" message shows on the product page; a new rating appears
  only once enough users have rated the new version (Apple publishes no
  threshold); once released it CANNOT be restored; universal apps reset only
  the platform version reset; app bundles cannot be reset; Admin or App
  Manager role required. Apple's own ratings guidance recommends using it
  "sparingly" because "having few ratings may discourage potential users
  from downloading your app."
- ReplyArgus decision framework (read in full)
  https://www.replyargus.com/blog/keep-or-reset-app-store-rating-new-version
  Reset clears BOTH the average AND the rating count; the count is social
  proof that converts (Apptentive: 3 stars -> 4 stars lifts conversion
  ~89%). One-line test: reset only if the lifetime average is anchored below
  what today's app deserves, recent good ratings genuinely cannot move it,
  and a believable count can be rebuilt within weeks. Cheaper lever first:
  replying to reviewers makes them ~6x more likely to raise their rating
  (Hassan et al., 4.5M reviews: 4.4% vs 0.7%); ship and stabilise the fix
  FIRST, prime the prompt, then reset on a later release. Google Play has
  no reset: its public rating is recency-weighted and heals itself.
Delimitation: review-budget-check / review-prompt-check own the prompt,
review-response surfaces own replies, phased-release-check owns rollout.
This gate owns only the per-release reset DECISION and its evidence.
Exit 0 = PASS, 1 = FAIL. Input JSON keys are the check names (booleans).
"""
import json, sys
CHECKS = [
    ("decision_recorded_per_release", "RR-0 no per-release ratings decision is recorded (keep vs reset must be an explicit recorded choice on every version submission; an untouched toggle is a decision nobody made and nobody can defend)"),
    ("default_is_keep", "RR-0 the default is not KEEP (Apple recommends using the reset sparingly; the burden of proof sits on resetting, never on keeping accumulated ratings)"),
    ("irreversibility_acknowledged", "RR-0 the decision record does not acknowledge irreversibility (once the version releases, the previous rating cannot be restored, in all territories at once; a one-way door needs that fact on the page)"),
    ("current_state_evidenced_per_app", "RR-1 the current lifetime average AND rating count per app (and main territories) were not read from App Store Connect before deciding (deciding from memory of a star number, without the count being discarded, is deciding blind)"),
    ("recent_vs_lifetime_gap_measured", "RR-1 recent ratings since the fix were not averaged separately from the lifetime average (if recent ratings are no better, a reset only hides the problem for a few weeks and rebuilds the same number)"),
    ("anchoring_math_done", "RR-1 the anchoring math was not done: how many fresh 5-star ratings recovery-in-place would need, on what timeline (a reset is justified only when that dilution is genuinely impossible in a reasonable time)"),
    ("root_cause_fixed_and_stable", "RR-1 the root cause behind the low ratings is not verifiably fixed and stable in a live version (resetting onto an unfixed problem re-earns the same average, now with zero count as well)"),
    ("count_loss_priced", "RR-2 the rating COUNT being discarded was not priced as an asset (the count is social proof that converts on its own; 4.2 stars on 3,000 ratings can out-convert a naked 5.0 on 6)"),
    ("all_territories_loss_accepted", "RR-2 the all-territories effect was not faced (the reset cannot be done for one storefront: strong territories are wiped together with the weak one)"),
    ("empty_window_planned", "RR-2 there is no plan for the no-rating window (after a reset the page shows a 'recently reset' notice and no stars until enough new ratings arrive, and Apple publishes no threshold; that window suppresses installs)"),
    ("reply_first_done", "RR-3 visible negative reviews about the old problem were not replied to first (written reviews SURVIVE a reset and become the first thing read under an empty rating; replies also convert: reviewers are ~6x more likely to raise a rating after a developer response)"),
    ("prompt_at_success_moment_ready", "RR-3 no review prompt firing at a success moment is live in the resetting version (without refill inflow the meter stays empty; the prompt must be primed BEFORE the reset lands, not added after)"),
    ("fix_not_the_reset_version", "RR-3 the reset is attached to the very version that ships the fix (the framework's order is: ship the fix, confirm crashes/reviews have settled, THEN reset on a later release; resetting on the fix itself bets the count on an unproven build)"),
    ("refill_volume_within_weeks", "RR-4 refill volume was not evidenced: install/rating inflow cannot rebuild a believable count within a few weeks (low-traffic apps that reset sit at 'not enough ratings' for a long, conversion-killing stretch)"),
    ("manual_release_timing", "RR-4 the resetting version is not on manual release timed to a monitored day (the reset lands at release, not at approval; an automatic release can start the empty window while nobody is watching)"),
    ("decision_logged_with_followup", "RR-4 the decision, its evidence and a dated follow-up read (new average/count after the window) are not logged (an irreversible choice with no outcome read can never be learned from)"),
    ("no_reset_to_hide_unfixed", "RR-5 a reset is being used to hide complaints the release does not actually fix (pricing, business-model or still-present bugs: the average returns and the burned count does not; outside story must match the inside product)"),
    ("google_play_difference_known", "RR-5 the plan assumes a Play-side equivalent exists (Google Play has NO reset and needs none: its public rating is recency-weighted; the Android side of the same turnaround is ship-the-fix plus fresh prompt inflow)"),
]
def check(d):
    return [m for k, m in CHECKS if not d.get(k)]
def main():
    d = json.load(open(sys.argv[1]))
    fails = check(d)
    for f in fails: print("FAIL", f)
    print(f"RESULT: {'PASS' if not fails else 'FAIL'} ({len(CHECKS)-len(fails)}/{len(CHECKS)} checks passed, {len(fails)} fails)")
    sys.exit(0 if not fails else 1)
if __name__ == "__main__":
    main()
