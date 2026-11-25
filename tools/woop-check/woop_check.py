#!/usr/bin/env python3
"""woop-check: gate for mental contrasting with implementation intentions (WOOP/MCII).
Oettingen fantasy-realisation: imagining a desired future alone (positive fantasy)
reduces follow-through; mental contrasting (future vs present obstacle) energises
commitment when expectations are favourable and supports disengagement when they
are not. WOOP = Wish, Outcome, Obstacle, Plan (if-then). Wang, Wang & Gai (2021)
meta-analysis: 21 articles / 24 studies / 15,907 participants, g=0.336 (95% CI
0.229-0.443), I2=59.3%, publication bias signal (Egger t=5.46), trim-and-fill
imputing 8 studies lowers the estimate; delivery moderator experimenter-led
g=0.465 vs document g=0.277. Health meta-analysis (Cross & Sheffield 2017):
g=0.28 at <=4 weeks, MC alone similar to MCII in that subset.
Distinct from ifthen-check (owns the if-then plan itself): this gate owns the
contrast that precedes it - wish feasibility, vivid best outcome, the internal
main obstacle in present reality, expectation assessment, and honourable
disengagement from infeasible wishes. Stdlib only, offline, free. Exit 0=PASS, 1=FAIL.
"""
import json, sys
CHECKS=[
 ("woop_surfaces_recorded_per_app","WP-0 no surface (onboarding, goal-setting, notification follow-up) is recorded per app as offering or not offering a full WOOP sequence, so mental contrasting cannot be audited"),
 ("wish_user_chosen_and_feasible_checked","WP-0 the wish is not user-chosen and checked for feasibility; an assigned or impossible wish cannot be contrasted honestly and produces fantasy or resentment, not commitment"),
 ("one_wish_per_woop","WP-0 a WOOP exercise mixes several wishes; the evidence uses one personally important wish per exercise, so obstacle and plan stay specific"),
 ("best_outcome_elaborated_vividly","WP-1 the best outcome is not elaborated vividly in the user's own words/events; a generic affirmation line is not the outcome step of mental contrasting"),
 ("outcome_contrasted_not_fantasy_only","WP-1 the outcome is presented fantasy-only (positive visualisation/affirmation without contrasting present reality); Oettingen's studies show fantasy alone can reduce effort and follow-through"),
 ("expectation_of_success_assessed","WP-1 expectation of success is not assessed; mental contrasting energises feasible goals and should loosen infeasible ones - without expectation the same push is applied to both"),
 ("main_obstacle_internal_and_specific","WP-2 the main obstacle is not identified as internal and specific (habit, feeling, behaviour in the user); vague or purely external obstacles cannot be planned around"),
 ("obstacle_in_present_reality","WP-2 the obstacle is not located in present reality (what is true now that stands in the way); contrasting only future-vs-future is not mental contrasting"),
 ("obstacle_linked_to_plan_cue","WP-2 the obstacle is not the cue the plan responds to; an unrelated if-then plan leaves the actual blocker unaddressed"),
 ("plan_ifthen_specific_and_feasible","WP-3 the plan is not a specific, feasible if-then response to the obstacle moment (delegated to ifthen-check for form, but its link to this obstacle is owned here)"),
 ("woop_written_or_rehearsed_externalised","WP-3 the WOOP is not written/rehearsed/externalised; a fleeting in-app prompt with no retained WOOP the user can revisit loses the commitment the exercise creates"),
 ("commitment_measured_after_woop","WP-3 commitment after the exercise is not measured; mental contrasting's proximal outcome is energised commitment, and behaviour claims without it skip the mechanism"),
 ("disengagement_from_infeasible_allowed_without_shame","WP-4 a user whose expectation is low cannot disengage/revise the wish without shame, penalty or nagging; forcing pursuit of infeasible wishes is the opposite of the evidence"),
 ("followthrough_measured_separate_cohort","WP-4 follow-through is not measured for WOOP users as a separate cohort over weeks; same-day taps cannot show goal attainment"),
 ("obstacle_and_wish_revised_when_reality_changes","WP-4 there is no revision path when the obstacle or wish changes; a stale WOOP keeps planning around a blocker that no longer exists"),
 ("primary_numbers_quoted_with_design","WP-5 MCII effects are quoted without design (Wang et al. 2021: 24 studies, 15,907 participants, g=0.336, CI 0.229-0.443) - bare claims strip their conditions"),
 ("expectations_discounted_for_publication_bias_and_delivery","WP-5 expectations are set above the evidence: publication-bias signals and trim-and-fill lower the estimate, and document/self-guided delivery (g=0.277) is weaker than experimenter-led (g=0.465)"),
 ("revenue_claim_tied_to_goal_attainment_chain","WP-5 any revenue/retention claim is not tied to the source chain - contrasting -> commitment/expectation-appropriate pursuit -> goal attainment - instead of asserting WOOP directly causes purchases"),
]
def main(p):
    s=json.load(open(p)); fails=[m for k,m in CHECKS if s.get(k) is not True]
    for f in fails: print("FAIL",f)
    print(f"RESULT {'PASS' if not fails else 'FAIL'} pass={len(CHECKS)-len(fails)}/{len(CHECKS)} fails={len(fails)}")
    return 0 if not fails else 1
if __name__=="__main__":
    if len(sys.argv)!=2: print("usage: woop_check.py <state.json>"); sys.exit(2)
    sys.exit(main(sys.argv[1]))
