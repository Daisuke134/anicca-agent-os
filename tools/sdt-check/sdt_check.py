#!/usr/bin/env python3
"""sdt-check: gate for supporting basic psychological needs.
Self-Determination Theory (Ryan & Deci 2000, Am Psychol 55:68-78 and
Psychol Inq 11:227-268): motivation, performance and well-being depend
on satisfying three innate needs - autonomy, competence, relatedness.
Contexts that support the needs facilitate intrinsic motivation and
internalisation of extrinsic motivation; contexts that thwart them
diminish motivation and well-being. Ng et al. (2012) meta-analysis of
184 health datasets found need satisfaction and autonomous motivation
related to beneficial health outcomes. Ntoumanis et al. (2020) meta-
analysis of SDT health interventions found small-to-medium, hetero-
geneous changes, with increases in need support and autonomous (not
controlled) motivation associated with positive behaviour change.
Distinct from self-efficacy-check (belief in capability for a task),
anchor/ifthen (prompts/plans) and default-check (preselection): this
gate owns (1) recording and separately measuring the three needs,
(2) autonomy support (real choice, rationale, no penalty for decline),
(3) competence support (optimal challenge, informational feedback),
(4) relatedness without guilt/comparison/faking, and (5) never using
controlling rewards/language that undermine intrinsic motivation.
Stdlib only, offline, free. Exit 0=PASS, 1=FAIL.
"""
import json, sys
CHECKS=[
 ("needs_surfaces_recorded_per_app","SD-0 no surface (onboarding, notification, home, paywall, community) is recorded per app with which of autonomy/competence/relatedness it supports or thwarts, so need support cannot be audited"),
 ("three_needs_measured_separately","SD-0 autonomy, competence and relatedness are not measured separately; a single engagement or satisfaction score cannot show which need is satisfied or thwarted"),
 ("autonomous_vs_controlled_motivation_distinguished","SD-0 autonomous motivation (interest/value) is not distinguished from controlled motivation (reward, guilt, deadline, shame); SDT predicts different persistence and well-being for the two"),
 ("meaningful_choice_not_cosmetic","SD-1 users are not offered meaningful choice over goals, timing, content or method - cosmetic choice (colour, order of forced steps) does not support autonomy"),
 ("rationale_given_for_requests","SD-1 requests (notifications, practice, purchase) are made without a meaningful rationale the user can endorse; unexplained demands are experienced as controlling"),
 ("decline_pause_without_penalty","SD-1 declining, pausing or skipping carries a penalty, guilt copy, lost streak punishment or repeated nagging, so continued use is controlled rather than autonomous"),
 ("challenge_graded_optimal_not_trivial_or_overwhelming","SD-2 tasks are not graded to optimal challenge for current ability; trivial tasks bore and overwhelming tasks thwart competence, both undermine intrinsic motivation"),
 ("informational_feedback_specific_and_noncontrolling","SD-2 feedback is evaluative/controlling (grades, rankings, 'you failed') rather than informational and specific about effectance, which SDT shows undermines intrinsic motivation"),
 ("effectance_progress_visible_without_score_pressure","SD-2 users cannot see the real effect of their actions (progress from their own performance) without that visibility becoming score pressure or social comparison"),
 ("relatedness_from_genuine_care_and_belonging","SD-3 relatedness is not supported by genuine care, respect and belonging; users are treated as conversion targets, which does not satisfy the relatedness need"),
 ("relatedness_not_guilt_comparison_or_social_pressure","SD-3 relatedness is built on guilt, comparison, leaderboards or social pressure ('others are ahead of you'), which thwarts autonomy while mimicking connection"),
 ("human_or_community_connection_not_faked","SD-3 a fake human/community connection is presented (invented members, fake testimonials, simulated peers) as if real relatedness; discovered faking destroys trust and the need it claimed to serve"),
 ("tangible_rewards_not_expected_contingent_on_engagement","SD-4 expected tangible rewards are contingent on engaging/completing, which the Deci/Ryan literature shows undermines intrinsic motivation for interesting tasks"),
 ("language_noncontrolling_no_must_shame_deadline_pressure","SD-4 copy uses controlling language (must, should-or-else, shame, artificial deadline pressure) rather than autonomy-supportive language offering choice and rationale"),
 ("need_thwarting_surfaces_audited","SD-4 surfaces that thwart a need (forced timing with no opt-out, overwhelming first task, public failure) are not audited and removed/redesigned; unexamined thwarting compounds daily"),
 ("primary_numbers_quoted_with_design","SD-5 SDT effects are quoted without their design (Ryan & Deci 2000 theory papers; Ng et al. 2012, 184 datasets, correlational meta-analysis; Ntoumanis et al. 2020 intervention meta-analysis) - bare claims strip their conditions"),
 ("expectations_discounted_small_medium_heterogeneous","SD-5 expectations are set above the evidence: Ntoumanis et al. (2020) found small-to-medium, heterogeneous effects, and Ng et al. (2012) relations are largely correlational, not guaranteed app outcomes"),
 ("revenue_claim_tied_to_autonomous_motivation_chain","SD-5 any revenue/retention claim is not tied to the source chain - need support -> autonomous motivation -> persistence - instead of asserting SDT directly causes purchases the studies did not show"),
]
def main(p):
    s=json.load(open(p)); fails=[m for k,m in CHECKS if s.get(k) is not True]
    for f in fails: print("FAIL",f)
    print(f"RESULT {'PASS' if not fails else 'FAIL'} pass={len(CHECKS)-len(fails)}/{len(CHECKS)} fails={len(fails)}")
    return 0 if not fails else 1
if __name__=="__main__":
    if len(sys.argv)!=2: print("usage: sdt_check.py <state.json>"); sys.exit(2)
    sys.exit(main(sys.argv[1]))
