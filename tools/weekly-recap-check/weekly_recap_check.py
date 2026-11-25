#!/usr/bin/env python3
"""weekly-recap-check: gate for the WEEKLY VALUE RECAP surface - a recurring
in-app recap built from the user's own logged core action, shown inside the
plan-specific activation window and again before the first renewal, that
celebrates real progress against the user's stated goal and ends in one
next step. Stdlib only, offline, free. Exit 0=PASS, 1=FAIL.
Sources (read in full 2026-11-24):
- RevenueCat, "Curse of the first renewal" (State of Subscription Apps 2026
  data) https://www.revenuecat.com/blog/growth/first-renewal-churn
  First renewal is where most subscribers are lost (weekly drop 42-65%,
  monthly 39-58%, annual 60-77%). Activation windows are NOT the plan
  length: weekly = first 5 days, monthly = first 2 weeks, annual = first
  month (embedding to ~Day 90). Monthly Days 22-30 are pre-renewal
  reinforcement: "positive reinforcement, progress reports, value
  summaries, and achievement highlights" (Loom shows meetings skipped /
  hours saved); never hide the upcoming charge. Messages must be
  value-oriented (celebrate what they did / show what is next), never
  generic reminders. Reverse-engineer the leading indicator of renewal
  from subscribers who stay, segment by those actions, drive that one
  behaviour. Highly active users: acknowledge, do not push them to do more.
  Days 8-21 (monthly) are hesitation removal, not silence.
- web2wave, "App Engagement Strategies for Subscription Apps" (2026-11-12)
  https://www.web2wave.com/post/app-engagement-strategies
  One core action per product, tracked instead of generic session counts;
  core-action frequency per week and Day 1/7/30 cohort retention are the
  reads. "Streaks, milestones and weekly summaries work when they reflect
  real effort. They backfire when a missed day feels punishing" - offer a
  recovery path. Pre-renewal note reminds subscribers what they used.
  In-app prompts must be tied to behaviour and not interrupt the core
  action. Change one thing at a time; judge on subscriber retention and
  refunds, not conversion or opens alone.
Separation: second-session-check owns the session-1 -> session-2 bridge;
streak-check owns streak mechanics and the first-renewal predictor hunt in
daily-return design; post-purchase gates own the moment right after payment;
summary-check owns iOS Scheduled Summary delivery. This gate owns only the
recurring value recap and its timing against the activation window.
NOT adopted: arbitrary / unverifiable recap numbers (the source itself
calls Loom-style percentile numbers "completely arbitrary") - every number
in our recap must trace to the user's own logged events.
"""
import json, sys
CHECKS=[
 ("recap_surface_recorded","WR-0 no weekly value recap surface is recorded per app and plan (without a recorded surface there is nothing to time, personalise or read)"),
 ("recap_timing_inside_activation_window","WR-0 recap timing is not placed inside the plan's activation window (weekly: by Day 4-5; monthly: Week 1 plus pre-renewal; annual: Month 1 - the window is shorter than the plan length, RevenueCat)"),
 ("recap_built_from_logged_core_action","WR-0 the recap is not built from the user's logged core action (one core action per product, web2wave; generic tips or session counts are not a value recap)"),
 ("recap_numbers_traceable_to_events","WR-1 recap numbers are not all traceable to the user's own logged events (arbitrary percentiles / invented savings are unverifiable claims, banned even though the source shows the form)"),
 ("recap_shows_goal_progress","WR-1 the recap does not show progress against the user's stated goal (a count with no goal context does not tell the user the value outweighed the cost)"),
 ("recap_celebrates_done_not_guilt","WR-1 the recap is not value-oriented celebration of what was done (guilt / shame for missed days backfires - web2wave; generic 'please come back' reminders are not value, RevenueCat)"),
 ("zero_activity_branch_distinct","WR-2 users with zero core actions do not get a distinct branch (an empty recap proves nothing; the zero branch must drive the first core action instead)"),
 ("recap_ends_single_next_step","WR-2 the recap does not end in one single next step / next core action (a recap that only reports leaves the renewal-driving behaviour unprompted)"),
 ("hesitation_removal_path","WR-2 there is no hesitation-removal path for low-activity users (wrong fit / time / unmet expectation - RevenueCat Days 8-21 stage; silence in Weeks 2-3 is the common failure)"),
 ("recap_not_interrupting_core_action","WR-3 the recap can interrupt the core action (in-app prompts must be tied to behaviour and shown at a boundary, never mid-action - web2wave)"),
 ("recap_frequency_tapers_and_adjusts","WR-3 recap/message frequency does not taper and adjust (heavy at the start of the window, never falling off a cliff, never spam; active users are acknowledged, not pushed to do more)"),
 ("pre_renewal_recap_before_charge","WR-3 no pre-renewal recap lands before the first charge with the charge visible (hiding the charge is dark UX; Days 22-30 monthly are for progress reports and value summaries - RevenueCat)"),
 ("recap_echoes_stated_goal_language","WR-4 the recap does not echo the user's own stated goal / onboarding answers in its language (a recap in the app's generic words is not the personalised reinforcement the sources describe)"),
 ("active_user_acknowledged_not_pushed","WR-4 highly active users are not acknowledged rather than pushed (RevenueCat: if they are highly active, acknowledge it rather than pushing them to do more)"),
 ("recap_persists_in_app","WR-4 the recap does not persist as an in-app surface (a push/email-only recap disappears; the user must be able to re-open their progress in the app)"),
 ("recap_read_by_plan_and_activity_cohort","WR-5 recap results are not read by plan duration and activity cohort (weekly/monthly/annual windows differ; a blended read hides which window is broken)"),
 ("recap_judged_on_renewal_not_opens","WR-5 the recap is not judged on first-renewal rate and core-action repeat (opens / clicks / conversion alone can rise while renewals and refunds worsen)"),
 ("renewal_predictor_behavior_named_and_driven","WR-5 the leading indicator of renewal is not named from renewers vs first-renewal churners, and the recap does not drive that one behaviour (RevenueCat: reverse-engineer it from subscribers who stay)"),
]
def main(p):
    s=json.load(open(p)); fails=[m for k,m in CHECKS if s.get(k) is not True]
    for f in fails: print("FAIL",f)
    print(f"RESULT {'PASS' if not fails else 'FAIL'} pass={len(CHECKS)-len(fails)}/{len(CHECKS)} fails={len(fails)}")
    return 0 if not fails else 1
if __name__=="__main__":
    if len(sys.argv)!=2: print("usage: weekly_recap_check.py <state.json>"); sys.exit(2)
    sys.exit(main(sys.argv[1]))
