#!/usr/bin/env python3
"""endowed-progress-check: gate for endowed progress (presenting a goal as
already begun by crediting initial steps, so the same remaining work reads
as partway-done rather than not-yet-started) in a behaviour app - the
credited steps must be real actions or a genuinely gifted head start with
a stated reason, the remaining work must be identical, the printed goal
must stay credible, the currency of progress must not change, credited
progress must never be taken back, and expectations must be discounted
from the single field study rather than forecast at its headline lift.
Stdlib only, offline, free. Exit 0=PASS, 1=FAIL.
Sources (read 2026-11-24):
- Nunes & Dreze (2006), Journal of Consumer Research 32(4):504-512,
  "The Endowed Progress Effect: How Artificial Advancement Increases
  Effort", doi:10.1086/500480. Field experiment at a car wash, April 2004:
  300 loyalty cards randomly distributed; half needed 8 stamps starting
  blank (0/8), half needed 10 stamps with 2 already affixed (2/10 = 20%
  progress) - both required exactly 8 more paid washes for the same free
  wash. Completion over the tracked period: 34% endowed vs 19% blank,
  and endowed customers also completed faster. The abstract attributes
  the effect to perceptions of progress, NOT to a desire to avoid wasting
  the endowed progress (it is not sunk cost), and names two moderators:
  the reason offered for the endowment and the currency in which
  progress is recorded. The 2/10 = 20% ratio is the only endowment ratio
  with a field result behind it.
- Kivetz, Urminsky & Zheng (2006), Journal of Marketing Research 43(1):
  39-58 (goal gradient, adjacent): effort accelerates as perceived
  distance to the goal shrinks; in their cafe study bonus stamps cut
  completion time from 15.6 to 12.7 days (secondary reporting).
Separation: streak-representation-check owns how a running streak is
displayed; ifthen-check owns the user's if-then plan; freshstart-check
owns landmark timing. This gate owns only the starting position: what
initial progress is credited, whether it is truthful, and how the
completion lift is read.
NOT adopted: fabricating progress that never occurred (a bar starting at
20% for nothing is a false state, and the company's rule is that what is
shown outside must exist inside), inflating the printed goal until it
looks unreachable, taking credited progress back or slowing the bar near
the end, and forecasting the published 1.789x relative lift (34/19) as
the expected effect - it is one field study, one category, one purchase
cycle, with no registered replication.
"""
import json, sys
CHECKS=[
 ("progress_surfaces_recorded_per_app","EP-0 no progress surface (onboarding plan, first-week journey, milestone track) is recorded per app, so there is nowhere an endowed starting position could be applied or audited"),
 ("remaining_work_identical_with_and_without_endowment","EP-0 the endowed design quietly changes the real remaining work (Nunes & Dreze 2006: both arms required exactly 8 more washes; if the credited steps also cut real work it is a discount, not an endowment, and the two effects cannot be told apart)"),
 ("endowment_ratio_near_tested_20_percent","EP-0 the endowed share departs from the only field-tested ratio without a recorded reason (2006: 2 of 10 = 20%; no published optimum exists, so a larger share is an untested invention, not a copy)"),
 ("endowed_steps_are_real_or_genuinely_gifted","EP-1 the credited steps are neither real actions the user actually took nor a genuinely gifted head start (a bar that starts at 20% for nothing is a fabricated state; the honest test is whether the user, shown exactly what the credited steps were, would agree they happened or were gifted)"),
 ("reason_for_endowment_stated_to_user","EP-1 no reason for the endowment is stated (the 2006 abstract names the reason offered as a moderator of the effect; in the field study customers were told the free stamps were part of a promotion - an unexplained head start is not the intervention that was tested)"),
 ("user_can_name_the_endowed_steps","EP-1 the user cannot name what the credited steps were (if the first reaction to the progress display is 'what did I do?', the product has printed a number, not endowed progress)"),
 ("printed_goal_still_looks_reachable","EP-2 the printed goal was inflated to make the endowed fraction prettier until the endpoint looks unreachable (perceived progress only helps if the endpoint reads as attainable; a 40-step track with 8 gifted suppresses the effect it was meant to buy)"),
 ("progress_currency_consistent_throughout","EP-2 the currency in which progress is recorded changes mid-track (the 2006 abstract names the currency of progress as a moderator; steps that become minutes that become points make the starting position unreadable)"),
 ("credited_progress_never_taken_back_or_slowed","EP-2 credited progress can be taken back, reset, or made slower near the end (progress that is withdrawn is noticed quickly and destroys the credibility of every other number in the product)"),
 ("endowment_applied_at_the_start","EP-3 the endowment is applied near the finish instead of at the start (endowed progress changes whether people begin - it moves them from not-begun to begun, where abandonment concentrates; acceleration near the finish is the goal gradient's job, a different mechanism)"),
 ("low_completion_surfaces_targeted_first","EP-3 the endowment is not aimed first at surfaces where completion is low and drop-off sits at step zero (a multiplicative lift has little room where the base rate is already high)"),
 ("onboarding_answers_credited_as_real_progress","EP-3 real work the user already did before the track starts (onboarding answers given, account created, first session completed) is not credited as the endowed steps (in an app the truthful endowment already exists: the user has genuinely begun during onboarding, and showing 0% after that work is the app's own false zero)"),
 ("completion_and_time_to_complete_both_read","EP-4 only completion is read, not time to complete (2006: the endowed group both completed more AND completed faster; reading one without the other misses half the tested effect)"),
 ("endowed_cohort_read_separately","EP-4 endowed and non-endowed users are not read as separate cohorts (mixing them hides whether the lift is at initiation, which is the only place this mechanism claims to act)"),
 ("mechanism_read_as_perceived_progress_not_sunk_cost","EP-4 the effect is explained or designed as sunk cost / not wanting to waste the head start (the 2006 abstract attributes the effect to perceptions of progress rather than a desire to avoid wasting the endowed progress; designing for loss of the gift designs the wrong mechanism)"),
 ("expectations_discounted_below_published_lift","EP-5 expectations are set at the published 1.789x relative lift (34% vs 19% is one field study, N=300, one category, one purchase cycle; transferring it undiscounted into a forecast is a promise the source does not make)"),
 ("primary_numbers_quoted_with_design","EP-5 effect sizes are quoted without the design that produced them (300 cards, 150 per arm, 8 identical remaining washes, 34% vs 19% over the tracked period - a bare '82% higher completion' strips the number of its conditions)"),
 ("replication_limits_noted","EP-5 the limits are not recorded (no registered replication of the car-wash result; adjacent goal-gradient evidence exists, but the endowed-progress magnitude rests on the 2006 studies)"),
]
def main(p):
    s=json.load(open(p)); fails=[m for k,m in CHECKS if s.get(k) is not True]
    for f in fails: print("FAIL",f)
    print(f"RESULT {'PASS' if not fails else 'FAIL'} pass={len(CHECKS)-len(fails)}/{len(CHECKS)} fails={len(fails)}")
    return 0 if not fails else 1
if __name__=="__main__":
    if len(sys.argv)!=2: print("usage: endowed_progress_check.py <state.json>"); sys.exit(2)
    sys.exit(main(sys.argv[1]))
