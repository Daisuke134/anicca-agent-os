#!/usr/bin/env python3
"""phased-release-check: deterministic gate for the PHASED RELEASE surface.
Stdlib only, offline, free.
Source (read 2026-11-16): Apple App Store Connect Help, Release a version update in phases
https://developer.apple.com/help/app-store-connect/update-your-app/release-a-version-update-in-phases/
- Update (not first version) released gradually over 7 days to a random sample of users with automatic updates on eligible devices, no notification: Day1 1%, 2 2%, 3 5%, 4 10%, 5 20%, 6 50%, 7 100%.
- Anyone can manually download at any time, so phased release does not gate manual updaters or new downloads.
- Pause up to 30 days total, unlimited number of pauses; resume picks up on the day it was left off. Release to All Users ends the schedule early.
- Removing app from sale (incl. membership lapse) stops phased release permanently for that version; reinstatement makes it available to all immediately.
- Pause is not a rollback: users already updated keep the build.
- PR-6 (added 2026-11-22, sources read that day): Extenify phased-release guide
  https://extenify.app/blog/app-store-phased-release and AppGrowthKit day-by-day
  https://appgrowthkit.com/blog/app-store-phased-release/
  Day bands: 1-2 crash/sign-in/purchase/first reviews; 3-4 low-star share, support,
  server errors by version; 5-6 rating trend, new-version retention, review-theme spike;
  day 7 vs previous-version baseline. Early reviews are biased (manual updaters dominate
  days 1-2): a cluster naming the same broken behaviour = investigate now; a small-sample
  star dip = noise until days 3-4. Pause rules decided before release: core-flow failure
  or crash-free clearly below previous version = pause immediately; 1-2 star share
  >=15pp above the prior 30 days with >=20 reviews on each side = pause and investigate;
  intentional-change complaints with flat crash/error = keep going; Release to All early
  only after flat signals for several days at >=10%. ASC API exposes phasedReleaseState,
  currentDayNumber, totalPauseDuration, startDate and per-version customerReviews.
  Listing copy (What's New/screenshots) is live from day 1 -- phased release stages only
  the automatic-update binary; promotional text does not hide the new build. Users are
  never told they are in a sample: replies name the version and the behaviour, never a
  percentage bucket, and support is told which version was paused. Stop rules and
  server-side switches are written before submission (a pause cannot help users who
  already have the build).
Exit 0=PASS, 1=FAIL, 2=PARTIAL (new optional section unrecorded).
"""
import json, sys
def check(d):
    f=[]; w=[]
    dec=d.get("decision") or {}
    if not dec.get("phased_choice_recorded_per_version"): f.append("PR-0 no per-version phased-release choice is recorded (phased/staged appears 0 times in the Anicca iOS subtree; every release decision is undocumented, so whether a version went to 100% at once or ramped is unknowable after the fact)")
    if not dec.get("schedule_known_1_2_5_10_20_50_100"): f.append("PR-0 the fixed 7-day schedule (1/2/5/10/20/50/100%) is nowhere recorded (the team cannot plan daily checkpoints against percentages it has not written down)")
    if not dec.get("pause_owner_with_required_role"): f.append("PR-0 no pause owner holding Account Holder/Admin/App Manager role is named (when a bad build is ramping at 02:00, nobody is designated or even able to pause it)")
    sco=d.get("scope") or {}
    if not sco.get("not_first_version_acknowledged"): f.append("PR-1 first-version ineligibility is not recorded (phased release is update-only; treating it as available for a first release would fail at submission time)")
    if not sco.get("auto_update_only_and_manual_bypass_understood"): f.append("PR-1 auto-update-only scope and manual-download bypass are not recorded (anyone can download manually from day 1, so a phased ramp does not contain a bad build's total reach -- support and comms planned as if it does would be wrong)")
    if not sco.get("removal_from_sale_cancels_recorded"): f.append("PR-1 removal-from-sale cancellation is not recorded (removing the app or a membership lapse ends phased release for that version permanently and reinstatement exposes it to all users at once)")
    mon=d.get("monitoring") or {}
    if not mon.get("daily_checkpoint_metrics_defined"): f.append("PR-2 no daily checkpoint metrics are defined for the ramp days (crash-free, review sentiment, funnel/purchase deltas per percentage step are not listed, so each day passes without a go/pause decision)")
    if not mon.get("crash_signal_live"): f.append("PR-2 no live crash signal exists to watch during the ramp (error reporting is absent per the Error Reporting Gate, FAIL 20; a crashing 1% cohort is invisible until reviews arrive)")
    if not mon.get("pause_thresholds_predefined"): f.append("PR-2 no pre-defined pause thresholds exist (without a number decided in advance, pausing becomes a debate held while the ramp auto-advances from 20% to 50% to 100%)")
    pau=d.get("pause_resume") or {}
    if not pau.get("pause_budget_30d_tracked"): f.append("PR-3 the 30-day total pause budget is not tracked anywhere (pauses spent are unrecorded, so remaining budget -- the only brake available -- is unknown)")
    if not pau.get("resume_and_release_to_all_criteria"): f.append("PR-3 no criteria are recorded for resume vs Release to All Users (resume picks up on the paused day and Release to All abandons the schedule; choosing between them ad hoc loses the ramp's protection)")
    fix=d.get("fix_forward") or {}
    if not fix.get("no_rollback_understood"): f.append("PR-4 no-rollback reality is not recorded (paused users keep the bad build; a plan that assumes recall leaves the already-updated cohort stranded)")
    if not fix.get("expedited_fix_build_path_recorded"): f.append("PR-4 no expedited fix-build path is recorded (the only remedy for the updated cohort is a new version through review; without a pre-agreed expedite path the cohort waits the full cycle)")
    mea=d.get("measurement") or {}
    if not mea.get("asc_state_readback_per_version"): f.append("PR-5 no App Store Connect phased-state readback is recorded per version (current percentage / paused state has never been read back and logged, so ramp state is asserted, not measured)")
    if not mea.get("version_distribution_measured"): f.append("PR-5 installed-version distribution is not measured (cannot size the updated cohort when deciding to pause)")
    if not mea.get("completion_recorded"): f.append("PR-5 no completion record exists (no version has a logged ramp completion at 100% with its pause history, so the practice has no track record to improve)")
    rw=d.get("rollout_watch")
    if rw is None:
        w.append("PR-6 rollout_watch is unrecorded (unknown, not a pass -- day-band signal plan, early-review bias handling, quantified pause rules, API state read, listing-as-live, reply/support discipline and pre-written server-side switches are all unmeasured)")
    else:
        if not rw.get("day_band_signal_plan_recorded"): f.append("PR-6 no day-band signal plan is recorded (days 1-2 crash/sign-in/purchase/first reviews, 3-4 low-star share/support/server errors by version, 5-6 rating trend/retention/theme spike, day 7 vs previous-version baseline -- watching the same numbers every day misses the regression each band exists to catch)")
        if not rw.get("signals_compared_to_previous_version"): f.append("PR-6 signals are not compared against the previous version over the same window (crash-free and error rates are judged against zero or last week instead of the build being replaced, so a relative regression reads as normal)")
        if not rw.get("early_review_bias_handled"): f.append("PR-6 early-review bias is not handled (manual updaters dominate days 1-2: a cluster naming the same broken behaviour must trigger immediate investigation, while a small-sample star dip is noise until days 3-4 confirm it -- treating early reviews as a random-sample verdict both over- and under-reacts)")
        if not rw.get("pause_rules_quantified_before_release"): f.append("PR-6 pause rules are not quantified before release day (core-flow failure or crash-free clearly below previous version = pause immediately; 1-2 star share >=15pp above prior 30 days with >=20 reviews each side = pause and investigate -- unquantified rules become a debate while the ramp auto-advances)")
        if not rw.get("keep_going_and_release_all_criteria_recorded"): f.append("PR-6 keep-going / early Release to All criteria are not recorded (intentional-change complaints with flat crash/error numbers = keep going; early release to all only after flat signals for several days at >=10% -- without the positive criteria, caution and impatience decide instead)")
        if not rw.get("api_state_read_daily"): f.append("PR-6 phased state is not read daily via the ASC API fields (phasedReleaseState, currentDayNumber, totalPauseDuration, startDate) plus per-version customerReviews (a UI glance is not a logged daily read, and totalPauseDuration is the only reliable pause-budget ledger)")
        if not rw.get("listing_treated_as_live_day1"): f.append("PR-6 the listing is not treated as live from day 1 (phased release stages only the automatic-update binary -- What's New and screenshots are public on day 1 to manual updaters and new downloaders, and promotional text cannot hide the new build)")
        if not rw.get("reply_and_support_discipline_recorded"): f.append("PR-6 reply/support discipline is not recorded (users are never told they are in a sample -- replies name the version and the shipped behaviour, never a percentage bucket -- and support is told exactly which version was paused so it does not promise a halted build)")
        if not rw.get("server_side_switches_written_before_submit"): f.append("PR-6 stop rules and server-side switches are not written before submission (a pause cannot help users who already have the build; a pre-written server-side switch is the only lever that reaches that cohort without a new reviewed version)")
    return f,w
if __name__=="__main__":
    data=json.load(open(sys.argv[1])); fails,warns=check(data)
    if fails:
        print(f"FAIL ({len(fails)}):")
        [print(" -",x) for x in fails]
        [print(" ~ warn:",x) for x in warns]; sys.exit(1)
    if warns:
        print(f"PARTIAL ({len(warns)} unknown):")
        [print(" ~ warn:",x) for x in warns]; sys.exit(2)
    print("PASS")
