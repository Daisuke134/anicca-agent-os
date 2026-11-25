#!/usr/bin/env python3
"""second-session-check: gate for the BRIDGE from session 1 to session 2 -
the critical activation metric (2 sessions in week 1), a short/valuable/fun
first session, a 3-part celebration, commitment captured at the motivation
peak, and an exact one-tap preview of the second session.
Stdlib only, offline, free. Exit 0=PASS, 1=FAIL.
Source (read in full 2026-11-24):
- Adapty blog (Selcuk Aciner, Wellspent co-founder; the Wellspent SDK pitch
  at the end is vendor content and is NOT adopted),
  "How to reduce early churn and activate the second session"
  https://adapty-pt2.vercel.app/blog/how-to-reduce-early-churn
  4 of 5 product leaders (50+ interviewed, early 2025): "2 sessions completed
  within the first week" is the critical activation metric; 77% of users
  churn by Day 3. The bridge starts INSIDE session 1. Brilliant's form:
  (1) first session short/valuable/fun (measured 2min14s; watch 1st-lesson
  start rate - simplify home if <60% - and completion rate, aim >60%);
  (2) obsessive 3-part celebration at completion (praise+haptic / recap that
  makes progress visible / streak counter nudging the next mini-milestone),
  ~20 seconds, identity goals beat outcome goals; (3) commitment captured at
  that high: a streak-goal with incremental 3/7/14-day milestones (goal
  gradient), tapped as an explicit commitment; (4) notification permission
  asked right after commitment, framed as help, at the peak - not cold;
  (5) preview the second session: the EXACT next unit, named, startable in
  one tap (Zeigarnik open loop; decision fatigue is the killer). Benchmark
  stated there: >50% of first-session completions should reach session 2.
Separation: motivation-peak-check owns order/timing BEFORE the first
paywall; flow-navigation-check owns in-flow navigation; notif permission
gates own permission policy generally; streak gates own streak mechanics
after a break. This gate owns only the session-1 -> session-2 bridge.
NOT adopted: locking distracting apps until a session is done (Wellspent
SDK pitch in the source) - coercive, third-party SDK, not the winner form
copied here.
"""
import json, sys
CHECKS=[
 ("second_session_activation_metric_defined","SSB-0 the critical activation metric is not defined as 2 sessions completed within the first week (installs / trial starts alone are not activation; 4 of 5 product leaders in the source use the 2-session metric)"),
 ("death_valley_cohort_measured","SSB-0 the Day-0..3 death-valley cohort is not measured separately (77% churn by Day 3 in the source; an aggregate retention number hides where the bridge breaks)"),
 ("first_session_triangle_balanced","SSB-0 the first session has no recorded short/valuable/fun balance with a duration target and start/completion reads (source form: ~2-3 min to first completion; simplify the first home if start rate <60%, aim completion >60%)"),
 ("celebration_three_part_present","SSB-1 completion has no 3-part celebration (praise+haptic / recap making progress visible / streak-or-next-milestone counter) - a silent completion wastes the motivation peak the bridge is built on"),
 ("celebration_at_completion_moment","SSB-1 any celebration is not at the completion moment (delayed or generic praise does not create the high that commitment capture depends on)"),
 ("identity_goal_framing","SSB-1 goals are framed as outcomes only, not identity (source: identity-based goals - become a problem-solver - trigger behaviour change stronger than outcome goals - reach a 3-day streak)"),
 ("commitment_captured_at_peak","SSB-2 no explicit commitment (streak-goal or equivalent) is captured at the post-completion high (asking cold at install, or never asking, both miss the one moment the user is most likely to say yes)"),
 ("milestone_ladder_incremental","SSB-2 the commitment has no incremental milestone ladder (source form: 3 / 7 / 14 days broken into named steps - goal-gradient effect; a single distant goal does not pull)"),
 ("notification_permission_after_commitment","SSB-2 notification permission is not asked right after commitment, framed as help reaching that commitment (cold launch-cluster asks are owned by the permission gates; here the bridge placement itself is missing)"),
 ("second_session_previewed_exact","SSB-3 the exact second session is not previewed before the user leaves (named next unit/content, not a generic 'come back tomorrow' - the open loop must be specific)"),
 ("one_tap_start_next","SSB-3 the previewed second session cannot be started in one tap (every extra tap/screen is activation energy spent against the return)"),
 ("next_step_single_clear_cta","SSB-3 the end of session 1 does not end with one crystal-clear next step (decision fatigue - 'what am I supposed to do now?' - is named in the source as the #1 killer of habit formation)"),
 ("return_landing_continues","SSB-4 a returning user does not land on continuation (they repeat the day-1 home / onboarding, or face an empty or reset state - the return must pick up where they left off)"),
 ("progress_visible_on_return","SSB-4 progress is not visible on return without the user asking (streak / recap / history shown unprompted is the proof that time spent is adding up)"),
 ("no_reblock_before_second_value","SSB-4 the second session is re-blocked before its value (re-onboarding, account wall or a paywall re-block before the second value moment burns the bridge the first session built)"),
 ("first_to_second_conversion_read","SSB-5 first-to-second session conversion is not read as its own number (source benchmark: >50% of first-session completions reaching session 2; without the read the bridge cannot be sized or fixed)"),
 ("second_session_read_by_cohort","SSB-5 the second-session read is not split by cohort (source/goal/first-session-completed vs not - an aggregate hides which bridge is broken)"),
 ("bridge_built_inside_first_session","SSB-5 the bridge relies only on post-exit pushes/campaigns (the source is explicit: the bridge starts within the first session; post-exit reminders alone are not a bridge)"),
]
def main(p):
    s=json.load(open(p)); fails=[m for k,m in CHECKS if s.get(k) is not True]
    for f in fails: print("FAIL",f)
    print(f"RESULT {'PASS' if not fails else 'FAIL'} pass={len(CHECKS)-len(fails)}/{len(CHECKS)} fails={len(fails)}")
    return 0 if not fails else 1
if __name__=="__main__":
    if len(sys.argv)!=2: print("usage: second_session_check.py <state.json>"); sys.exit(2)
    sys.exit(main(sys.argv[1]))
