#!/usr/bin/env python3
"""onboarding-handoff-check — Onboarding Handoff Gate (OH-1..OH-12).
Source (read in full 2026-11-21):
- Adapty, State of Onboarding 2026 (data Nov 2025-Oct 2026, App Store)
  https://adapty.io/state-of-onboarding/report/
  91% of openers finish eventually (median app); completion per open 79.4%
  (US 70.0%, fewest). First screen loses 10.2% of sessions, 5x any later
  screen; from screen 3 each screen loses <=1.5%. First screen is the ad's
  handoff: it must confirm what the creative promised. Median flow = 5
  screens / 14 seconds; 21+ screens = 172s, completion 62.8% vs 89.7% for
  1-5 screens, BUT paid per open 2.33% vs 1.20% and revenue per open $1.39
  vs $0.36 — length is judged by revenue per open, not completion (report
  flags this as not causal). Finishers start trials at 14x leavers
  (5.47% vs 0.24%) and pay at 2.00% vs 0.09% (correlation, not cause);
  94.7% of finishers see a paywall within a day vs 1.2% of leavers.
  Only 19.2% of apps save onboarding answers as user attributes (large
  apps 40.9% vs small 15.0%); unsaved answers mean a one-size paywall.
  52% of top apps personalize; 33% of quiz apps show no plan screen and
  no answer playback; only 9% of paywalls show the user's name, goal or
  target date. Personalization lifted ARPU 13-35% (State of Paywalls,
  cited). Median revenue per onboarding open $0.37; median paid per open
  1.75% within 30 days. Only 23.5% of apps ran an onboarding A/B test in
  the year (large 68.2%, median 11 variations); only 1 in 6 tests finds
  a clear winner on PAID conversion (3 in 4 on completion); median
  variation collects only 43 paid conversions — 'no winner' usually
  means not enough data yet.
Distinct from onboarding-check (flow shape: duration, quiz count, proof
screen, paywall position, day-2 push) and onboarding-adaptation-check:
this gate is ONLY about the handoff — what the first screen confirms,
whether answers survive into the product and the paywall, and whether
the flow is measured and judged on money (revenue per open, paid
conversion, trial quality) rather than on completion alone.
Free: Python stdlib only. Input: JSON state. Exit 0 = PASS, 1 = FAIL."""
import json, sys
CHECKS = [
 ("OH-1","first_screen_confirms_creative_promise","First screen confirms what the creative / store listing promised (the first screen is the ad's handoff; it loses 10.2% of sessions, 5x any later screen)"),
 ("OH-2","per_screen_dropoff_measured","Drop-off is measured per screen with screen 1 separated (after screen 3 each screen loses <=1.5%; an aggregate completion rate cannot locate the loss)"),
 ("OH-3","answers_saved_as_attributes","Onboarding answers are saved as user attributes (only 19.2% of apps do; unsaved answers cannot personalize anything downstream)"),
 ("OH-4","answers_played_back_visibly","Answers are played back visibly — a plan-building screen or a screen/result that shows what the answers changed (33% of quiz apps show neither; users answer and see nothing change)"),
 ("OH-5","answers_used_on_paywall","The paywall itself uses the answers — name, goal or target date in the headline or on the plan card (only 9% of paywalls do; personalization lifted ARPU 13-35%)"),
 ("OH-6","finisher_vs_leaver_paywall_reach_measured","Finisher vs leaver paywall reach is measured (benchmark: 94.7% of finishers see a paywall within a day vs 1.2% of leavers; finishing only matters if the handoff to the paywall actually happens)"),
 ("OH-7","completion_judged_with_paid_conversion","Completion is judged alongside paid conversion per open, never alone (categories with the lowest completion sell the most; high completion alone brings no revenue)"),
 ("OH-8","revenue_per_open_tracked","Gross revenue per onboarding open is tracked (median $0.37; US $0.56; it is the single number that prices an onboarding open)"),
 ("OH-9","length_judged_by_revenue_per_open","Flow length is judged by revenue per open and paid per open, not by completion (21+ screens: completion 62.8% vs 89.7%, but revenue per open $1.39 vs $0.36 — and the report's not-causal caveat is kept with the number)"),
 ("OH-10","trial_quality_tracked_with_volume","Trial quality (trial-to-paid, day-1 cancellation) is tracked alongside trial starts, split by flow (long flows start fewer trials, 2.1-2.8% vs 4.95%, but convert ~30% vs 19.7%)"),
 ("OH-11","every_question_used_later","Every onboarding question is used later (saved, played back, or on the paywall) — questions with no downstream use are cut (long flows lose users mid-flow, up to 19.3%)"),
 ("OH-12","tests_sized_for_paid_conversion","Onboarding A/B tests are sized for paid conversion — few variations at once, run long enough (only 1 in 6 tests finds a paid winner; median variation has 43 paid conversions, so 'no winner' is treated as 'not enough data yet', not as a verdict)"),
]
def main(path):
    s=json.load(open(path)); fails=[]
    for gid,key,desc in CHECKS:
        ok = s.get(key) is True
        print(f"{'PASS' if ok else 'FAIL'} {gid} {desc}")
        if not ok: fails.append(gid)
    total=len(CHECKS); passed=total-len(fails)
    print(f"TOTAL {'PASS' if not fails else 'FAIL'} {passed}/{total}")
    return 0 if not fails else 1
if __name__=="__main__":
    sys.exit(main(sys.argv[1]))
