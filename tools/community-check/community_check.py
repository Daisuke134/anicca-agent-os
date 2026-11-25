#!/usr/bin/env python3
"""community-check: deterministic gate for in-app community as a retention lever.
Stdlib only, offline, free. Source (read in full 2026-11-23):
- social.plus, "How does an in-app community improve app retention?" (2026-10-16)
  https://www.social.plus/answers/how-an-in-app-community-improves-app-retention
  Mechanisms: return triggers created by other users; group identity (Ren et al.,
  MIS Quarterly 2012, 6-month field experiment, 4,818 MovieLens users: group-identity
  features +44% visit frequency vs control, individual-bond +11%; newcomers in the
  identity condition +56%, old-timers +10%); early feedback (Burke/Marlow/Lento:
  newcomers who received feedback shared more); accumulated history raises switching
  cost. Vendor platform data: 10-35% retention lift (cross-app, secondary).
  Failure modes: empty community (first post unanswered), no natural repeat reason,
  unmanaged safety, cadence fading. Measurement honesty: never compare joiners vs
  non-joiners naively (self-selection); use holdout, matched cohorts, or staggered
  rollout; judge at week 4 and month 3, not in novelty days.
Delimitation: embedded-virality-check owns output->non-user exposure; referral-check
owns incentivised referral; retention-check owns general retention. This gate owns
the in-app community decision, its return-trigger/identity/feedback design, its
liveness and safety preconditions, and the causal honesty of its retention claim.
Exit 0 = PASS, 1 = FAIL. Input JSON keys are the check names (booleans).
"""
import json, sys
CHECKS = [
    ("community_decision_recorded", "CM-0 no recorded build / do-not-build decision for an in-app community (an undecided community is an unowned surface; record the decision and its evidence either way)"),
    ("natural_repeat_reason_exists", "CM-0 the product has no natural reason for repeat visits or no ongoing shared goal (a once-a-year product gains little from a daily feed; community is not a universal fix)"),
    ("newcomer_first_weeks_focus", "CM-0 design effort is not concentrated on newcomers' first weeks (in the controlled experiment newcomers moved +56% vs +10% for old-timers; that is where the lever pays back first)"),
    ("group_activity_shown_prominently", "CM-1 group activity is not shown prominently (identity-based features - group profiles, recent group activity - moved visits most, +44% vs control)"),
    ("return_triggers_from_other_users", "CM-1 return reasons do not come from other users' activity (replies, new posts, group activity the user already cares about; a generic reminder is not a community trigger)"),
    ("group_identity_prioritised_over_bonds", "CM-1 group identity is not prioritised over individual bonds (identity features outperformed bond features roughly 4-to-1 in the experiment, 44% vs 11%)"),
    ("first_post_response_guaranteed", "CM-2 a newcomer's first post is not guaranteed a fast, human response (an unanswered first post teaches the newcomer that nobody is there)"),
    ("early_feedback_loop_tracked", "CM-2 feedback on early contributions is not tracked (newcomers who received feedback went on to contribute more; without tracking the loop is invisible)"),
    ("reading_participation_supported", "CM-2 reading is not treated as real participation (users who never post still benefit when the community gives them something worth reading; lurkers receive triggers too)"),
    ("seeding_plan_before_launch", "CM-3 there is no seeding plan before launch (early activity must be seeded and responded to; an empty room at arrival kills the lever)"),
    ("cadence_calendar_planned", "CM-3 no cadence calendar is planned before launch (a launch burst followed by silence returns retention to its old baseline)"),
    ("moderation_is_precondition", "CM-3 moderation and safety are not in place as a precondition (harassment, spam and scams push the users who matter most to leave first; moderation is not an add-on)"),
    ("causal_design_holdout_or_matched", "CM-4 the retention claim does not rest on a holdout, matched cohorts, or a staggered rollout (comparing joiners with non-joiners mixes cause and effect through self-selection)"),
    ("judged_at_week4_and_month3", "CM-4 the effect is not judged at week 4 and again at month 3 (novelty inflates the first days; the field research ran six months)"),
    ("self_selection_bias_acknowledged", "CM-4 self-selection bias is not acknowledged in the community reporting (engaged users join anything; an unqualified lift number overstates the case)"),
    ("history_accumulates_inside_app", "CM-5 user history (profile, posts, roles, relationships) does not accumulate inside the app (history that lives elsewhere builds no attachment and no switching cost here)"),
    ("no_fabricated_members_or_activity", "CM-5 the community relies on fabricated members, posts or activity counts (fake liveness is a lie under the house rule; seeded real activity by the team, labelled as such, is different)"),
    ("outside_equals_inside_community", "CM-5 marketing shows a community that is not actually live and active inside the app (what is shown outside must exist inside)"),
]
def check(d):
    return [m for k, m in CHECKS if not d.get(k)]
def main():
    d = json.load(open(sys.argv[1]))
    fails = check(d)
    for f in fails: print("FAIL", f)
    print(f"RESULT: {'PASS' if not fails else 'FAIL'} ({len(CHECKS)-len(fails)}/{len(CHECKS)} checks passed, {len(fails)} fails)")
    sys.exit(0 if not fails else 1)
if __name__ == "__main__": main()
