#!/usr/bin/env python3
"""temptation-bundle-check: gate for temptation bundling (pairing an
instantly gratifying 'want' that is only available during a delayed-benefit
'should' behaviour) in a behaviour app - a recorded want/should pairing
chosen by the user, a real restriction (not encouragement alone), a
simultaneous pairing, a plan for the measured decay and for restarts
after breaks, user control of the restriction, and reads that claim the
scaled effect size, not the first-week headline. Stdlib only, offline, free.
Exit 0=PASS, 1=FAIL.
Sources (read 2026-11-24):
- Milkman, Minson & Volpp (2014), Management Science 60(2):283-299,
  "Holding the Hunger Games Hostage at the Gym": N=226 university gym
  members, 9 weeks. Full treatment (tempting audio novels loaded on an
  iPod locked at the gym) initially visited 51% more than control;
  intermediate treatment (same novels on own device, encouraged to
  restrict listening to the gym) initially +29%. Effects declined over
  time, particularly after the Thanksgiving break; over the first seven
  weeks visits averaged 7.8 (full) vs 6.5 (intermediate) vs 6.1
  (control). After the study 61% opted to PAY for gym-only access -
  demand for the restriction itself. Busiest participants benefited most.
- Kirgios, Mandel, Park, Milkman, Gromet, Kay & Duckworth (2021),
  OBHDP 161(S):20-35, "Teaching temptation bundling to boost exercise":
  N=6,792 in a 4-week programme (24 Hour Fitness StepUp). A free
  audiobook + encouragement to bundle raised the likelihood of a weekly
  workout by 10-14% and average weekly workouts by 10-12%, during and
  up to 17 weeks post-intervention. Encouragement added only a modest
  effect over the audiobook alone (the gift itself leaks the strategy;
  only ~14% downloaded it in the megastudy reporting).
Separation: ifthen-check owns the if-then plan formed by the user;
freshstart-check owns landmark timing; commitment-check owns paid /
long commitments. This gate owns only the bundle layer: which want is
paired with which should, whether access to the want is actually
restricted to the should context, and how the lift and its decay are read.
NOT adopted: quoting the 51% first-week figure (N=226) as the expected
effect (the scaled estimate is 10-14%), claiming habit formation or
automaticity (no bundling trial shows it; the 2014 effect faded after a
break), and guilt/shame framing of the want (the want is a chosen treat,
not a vice to be punished).
"""
import json, sys
CHECKS=[
 ("want_should_pairs_recorded","TB-0 no want/should pairing is recorded per app (without an explicit pairing - this want, only during this should - there is no bundle, only unrelated content next to a task)"),
 ("want_chosen_by_user_and_genuinely_tempting","TB-0 the want is not chosen by the user from options pre-tested as genuinely tempting to them (Milkman 2014: participants chose 4 novels from 82 pre-tested as highly tempting; an assigned 'treat' the person does not want cannot pull a should)"),
 ("should_has_delayed_benefit_and_is_avoided","TB-0 the paired behaviour is not a delayed-benefit 'should' the person avoids (bundling solves a want/should conflict; pairing a want with an already-enjoyed behaviour spends the treat for nothing)"),
 ("want_restricted_to_should_context","TB-1 access to the want is not restricted to the should context (the bundle is the restriction: gym-only access in Milkman 2014; a want available everywhere at any time exerts no pull toward the should)"),
 ("restriction_is_enforced_not_encouragement_only","TB-1 the restriction is encouragement only, with no enforcement (2014: locked access +51% initially vs encouraged-only +29%, and the encouraged group's advantage was not reliable over seven weeks; Kirgios 2021: encouragement over the gift alone was only modest)"),
 ("pairing_is_simultaneous_with_should","TB-1 the want is delivered after the should as a sequential reward, not simultaneously during it (bundling makes the should itself instantly gratifying while it happens; a post-hoc reward is a different, contingency-management design)"),
 ("want_does_not_block_should","TB-2 the want consumes the attention or capacity the should needs (a gripping plot during a task needing full attention turns the bundle into a distraction; the 2014 pairing worked because listening and exercising are compatible)"),
 ("novelty_decay_plan_exists","TB-2 there is no plan for the want going stale (the 2014 effect declined over the nine weeks as novelty wore off; a fixed bundle with no rotation or refresh reads its own decay as product failure)"),
 ("restart_after_break_plan_exists","TB-2 there is no restart plan for after breaks (the 2014 gains dropped sharply after the Thanksgiving closure broke the routine; bundles die at holidays unless a restart is designed in advance)"),
 ("user_opts_in_to_restriction","TB-3 the restriction is imposed without the user opting in (61% of 2014 participants chose to pay for the restriction afterwards - the demand is for a self-chosen commitment device, not for a lock imposed on them)"),
 ("user_can_modify_or_remove_restriction","TB-3 the user cannot modify or remove the restriction (a lock the person cannot exit is a dark pattern of control, not a commitment device they own; the 2014 device was a paid opt-in they could stop buying)"),
 ("want_framed_without_guilt_or_shame","TB-3 the want is framed with guilt or shame (the source frames wants as instantly gratifying but guilt-inducing - the design removes the guilt by earning the want, it does not amplify shame to drive the should)"),
 ("busiest_users_prioritised","TB-4 the bundle is not offered first to the busiest / least-available users (Milkman 2014: bundling particularly benefited the busiest participants - a one-SD decrease in availability raised the initial treatment effect by 0.21 visits/week)"),
 ("initiation_and_frequency_measured_not_habit_claimed","TB-4 habit formation or automaticity is claimed from bundling (no bundling trial shows automaticity; the 2014 effect faded after a break - the honest read is visit frequency while the bundle is live)"),
 ("bundle_cohort_read_separately","TB-4 bundlers are not read as a separate cohort (mixing bundlers with non-bundlers hides both the initiation lift and the decay curve the rotation and restart plans are meant to fix)"),
 ("scaled_effect_size_used_for_expectations","TB-5 expectations are set from the 51% first-week headline instead of the scaled estimate (Kirgios 2021, N=6,792: +10-14% likelihood of a weekly workout, up to 17 weeks; the 51% is week one of N=226)"),
 ("encouragement_marginal_effect_noted","TB-5 the design assumes teaching/encouraging bundling adds a large effect on top of providing the want (Kirgios 2021: the marginal effect of encouragement over the audiobook alone was modest, because providing the want leaks the strategy)"),
 ("effect_sizes_quoted_from_primary_source","TB-5 effect sizes are not quoted from the primary sources (51%/29% initial, 7.8 vs 6.1 visits over seven weeks, 61% paid for restriction - Milkman 2014; 10-14% at scale - Kirgios 2021; rounded retellings turn a bounded effect into a promise)"),
]
def main(p):
    s=json.load(open(p)); fails=[m for k,m in CHECKS if s.get(k) is not True]
    for f in fails: print("FAIL",f)
    print(f"RESULT {'PASS' if not fails else 'FAIL'} pass={len(CHECKS)-len(fails)}/{len(CHECKS)} fails={len(fails)}")
    return 0 if not fails else 1
if __name__=="__main__":
    if len(sys.argv)!=2: print("usage: temptation_bundle_check.py <state.json>"); sys.exit(2)
    sys.exit(main(sys.argv[1]))
