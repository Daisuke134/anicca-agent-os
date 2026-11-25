#!/usr/bin/env python3
"""goal-gradient-check: gate for designing effort around distance-to-goal.
Effort rises as perceived distance to a goal falls (Hull 1932/1934;
Kivetz, Urminsky & Zheng 2006, JMR 43:39-58). Distinct from endowed-
progress-check, which owns the truthfulness of a granted starting
position: this gate owns (1) framing distance as proportion remaining,
(2) segmenting long goals so a near finish always exists, (3) measuring
acceleration (effort per unit time by distance band), not cumulative
totals, and (4) the post-reward reset - effort collapses after a reward,
hardest among the strongest accelerators, so re-engagement must be
designed before the goal completes. Stdlib only, offline, free.
Exit 0=PASS, 1=FAIL.
Sources (read 2026-11-24):
- Kivetz et al. (2006) abstract + Columbia summary: cafe buy-10-get-1
  members bought more frequently as they neared the free coffee
  (interpurch. times fell ~20% / 0.7 days across the program); song
  raters visited more, rated more per visit, persisted longer near the
  threshold; a 12-stamp card with 2 bonus stamps completed the same 10
  purchases faster (median 10 vs 15 days in Columbia summary); stronger
  acceleration predicted retention and faster reengagement; after the
  first reward engagement dropped, then re-accelerated toward the 2nd.
NOT adopted: fake progress (owned/banned by endowed-progress), hiding
remaining distance, moving the finish line, quoting -20% as a promise.
"""
import json, sys
CHECKS=[
 ("goal_surfaces_recorded_per_app","GG-0 no goal-bearing surface (first-week plan, streak, collection, savings-style target) is recorded per app, so distance-to-goal cannot be audited"),
 ("distance_shown_as_remaining_and_proportion","GG-0 distance is shown only as raw counts done, not as remaining amount and proportion of original distance remaining (Kivetz model: effort is a function of proportion remaining, not absolute steps)"),
 ("goal_distance_truthful_no_moving_finish","GG-0 the finish line can move or remaining distance can be hidden/renumbered mid-goal (perceived distance only motivates when it is true; a moved goal destroys the gradient and trust)"),
 ("long_goals_segmented_into_near_subgoals","GG-1 a long goal has no near subgoal, so most users spend most of the journey in the flat far-from-goal zone where the gradient predicts least effort"),
 ("near_finish_zone_explicitly_designed","GG-1 the final stretch (last ~20-30% of distance) is not explicitly designed (prompts, next-action clarity and feedback intensify truthfully near completion instead of staying uniform)"),
 ("next_action_visible_at_every_distance","GG-1 at some distance the user sees progress but not the single next action that reduces it (distance information without an action does not convert acceleration into effort)"),
 ("acceleration_measured_by_distance_band","GG-2 effort is measured only as cumulative totals, not as rate (actions per day / interpurchase-style interval) by distance band, so acceleration toward the goal is unobservable"),
 ("post_reward_reset_anticipated","GG-2 no design exists for the post-reward drop (Kivetz: engagement fell after the first reward before re-accelerating; an undesigned reset reads the collapse as churn)"),
 ("next_goal_seeded_before_completion","GG-2 the next goal / next cycle is not seeded before the current goal completes, leaving a gap at exactly the moment effort collapses"),
 ("strongest_accelerators_reengaged_first","GG-2 re-engagement does not prioritise the strongest accelerators (they predict fastest reengagement in the source, and also collapse hardest - they are the highest-value, highest-risk cohort)"),
 ("segment_effects_read_separately","GG-3 far, middle and near cohorts are pooled into one average (pooling hides the gradient itself: the effect is a slope across distance, not a level)"),
 ("no_fake_progress_or_illusory_distance","GG-3 perceived distance is shrunk by illusion (renumbering, inflated stamps, decorative bars) rather than by real segmentation or truthful granted progress owned by endowed-progress-check"),
 ("completion_time_not_promise","GG-4 a median completion time (e.g. 10 vs 15 days, cafe card) is quoted as a promise for this app (it is one program, one category, 2006 field data - an expectation to test, not a guarantee)"),
 ("primary_numbers_quoted_with_design","GG-4 the ~20% / 0.7-day interpurchase fall is quoted without its design (one cafe buy-10-get-1 program in Kivetz et al. 2006, alongside song-rating data - bare numbers strip their conditions)"),
 ("expectations_discounted_for_single_domain","GG-4 expectations are set at the source effect size without discounting for a single-domain, pre-app-era evidence base"),
 ("gradient_not_used_as_pressure_dark_pattern","GG-5 near-goal urgency is manufactured with fake deadlines, loss threats or shame to exploit acceleration (the gradient is an effort pattern to serve, not pressure to weaponise; cf. banned Prayer Lock dark patterns)"),
 ("effort_can_pause_without_distance_penalty","GG-5 pausing or missing a day increases displayed distance or erases progress (penalising rest converts the gradient into a threat and punishes exactly the resumption the design needs)"),
 ("revenue_claim_tied_to_retention_read","GG-5 any revenue claim from goal design is not tied to the source's actual chain - acceleration predicts retention and faster reengagement - instead of asserting direct purchase causation the study did not show"),
]
def main(p):
    s=json.load(open(p)); fails=[m for k,m in CHECKS if s.get(k) is not True]
    for f in fails: print("FAIL",f)
    print(f"RESULT {'PASS' if not fails else 'FAIL'} pass={len(CHECKS)-len(fails)}/{len(CHECKS)} fails={len(fails)}")
    return 0 if not fails else 1
if __name__=="__main__":
    if len(sys.argv)!=2: print("usage: goal_gradient_check.py <state.json>"); sys.exit(2)
    sys.exit(main(sys.argv[1]))
