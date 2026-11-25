#!/usr/bin/env python3
"""flow-navigation-check: gate for onboarding NAVIGATION mechanics -
progress display, back/skip, chunking, resume and recovery.
Stdlib only, offline, free. Exit 0=PASS, 1=FAIL.
Sources (read in full 2026-11-24):
- Digia, "Mobile Onboarding UX: Reduce Drop-Off and Boost Activation"
  (2026-05-30) https://www.digia.tech/post/mobile-onboarding-ux-reduce-dropoff/
  Drop-off clusters at account walls, early permission clusters and
  premature information collection - all ask before giving. Progress
  indicators (78% of products) help when the flow is short and steps
  feel even; they hurt when they reveal an unexpectedly long flow
  ("Step 2 of 9"); for longer flows show progress WITHIN phases, not
  a raw total (UXPin guidance cited: aim 3-7 steps). A stalled or
  slow-filling bar is worse than none. Chunking: 2-4 meaningful
  inputs per screen, thematic groups labelled; multi-step animated
  completion +22%. Skip: visible for tours/non-essential steps
  (NNGroup: minimise mandatory onboarding); "Maybe later" beats
  "Skip" for steps to complete eventually; a hidden/low-contrast
  skip makes users feel tricked. Personalisation steps: not
  skippable, but explain precisely what the personalisation does.
  Recovery: know exactly where the user stopped; resume via deep
  link at the exact step with inputs preserved (restarting kills
  re-engagement); nudge specific to the drop point, first within
  24h, second at 48-72h in a different tone; offer lighter re-entry
  when the drop was at a high-friction step.
- CMM summary of Adapty State of Onboarding 2026 (2026-11-19)
  https://www.cmm-tech.com/blog/adapty-state-of-onboarding-2026-funnel/
  First screen loses 10.2% of sessions, 5x any later screen; from
  screen 3 each screen loses <=1.5%. US completes least (70.0% vs
  79.4% overall) yet pays most (2.06% of opens) - completion alone
  is a weak goal; read revenue per open.
Separation: onboarding-length-check owns flow length;
onboarding-adaptation-check owns in-flow branching;
answer-persistence-check owns saving/reusing answers;
notif-permission-check owns permission opt-in mechanics. This gate
owns only navigation: map/drop-off reading, progress form, back and
skip, chunking, resume and recovery.
"""
import json, sys
CHECKS=[
 ("flow_map_recorded","FN-0 no recorded flow map (every screen, its phase and its ask; a flow nobody has mapped cannot be navigated or debugged)"),
 ("per_screen_dropoff_measured","FN-0 per-screen drop-off is not measured (Digia: drop-off clusters at predictable screens; without per-screen loss the cluster is invisible)"),
 ("first_screen_loss_read_separately","FN-0 first-screen loss is not read separately (Adapty: screen 1 loses 10.2% of sessions, 5x any later screen; averaging it into the funnel hides the biggest leak)"),
 ("progress_form_matches_length","FN-1 progress form does not match flow length (raw total count only for short flows of about 5 or fewer; longer flows show progress within labelled phases - Digia/UXPin: revealing 'Step 2 of 9' raises abandonment)"),
 ("progress_indicator_truthful","FN-1 the progress indicator is not verified truthful (it must advance with real progress and never stall, regress or fabricate; a bar that communicates 'you have barely started' is worse than none)"),
 ("effort_ordering_decided","FN-1 no recorded effort-ordering decision (quick steps first, demanding input late - Digia: reaching step 4 of 5 before anything demanding creates completion pressure that works in your favour)"),
 ("back_preserves_answers","FN-2 back navigation does not preserve entered answers (forcing re-entry on a back tap punishes the exact exploration a long quiz invites)"),
 ("skip_visible_on_nonessential","FN-2 no visible skip on tour/non-essential screens (NNGroup via Digia: minimise mandatory onboarding; a hidden or low-contrast skip makes users feel tricked and damages trust before the first session)"),
 ("skip_copy_and_personalisation_rule","FN-2 no recorded skip-copy/personalisation rule ('Maybe later' for steps to complete eventually, 'Skip' for tours; personalisation steps are not skippable but must explain precisely what the personalisation does)"),
 ("chunking_two_to_four_inputs","FN-3 data-collection screens are not chunked to roughly 2-4 meaningful inputs (Digia: a 15-field screen and a 10-step one-field flow are both friction; grouped-but-not-dense is the target)"),
 ("phases_grouped_and_labelled","FN-3 steps are not grouped into labelled thematic phases (grouping lets a long flow show phase progress without exposing a daunting raw total)"),
 ("no_ask_wall_before_first_value","FN-3 an ask wall (account creation, stacked permissions, premature information collection) still sits before the first value moment (Digia: all three clusters share one cause - asking for commitment before demonstrating value)"),
 ("stop_point_recorded_per_user","FN-4 the exact stop point is not recorded per user (recovery starts with knowing where this user stopped; a step-4-of-5 drop and an account-wall drop are different users)"),
 ("resume_exact_step_inputs_preserved","FN-4 abandonment does not resume at the exact step with prior inputs preserved (Digia: asking a user who finished 3 steps to start over is a separate friction point that kills re-engagement)"),
 ("recovery_message_specific_and_timed","FN-4 no drop-point-specific recovery message on a recorded schedule (first nudge within 24h referencing the actual step, second at 48-72h in a different tone; a generic 'we miss you' at day 3 is a hope, not a recovery pattern)"),
 ("completion_read_with_revenue_per_open","FN-5 completion is read alone, without revenue per onboarding open (Adapty via CMM: the US completes least and pays most; completion-only reads optimise toward the wrong country-shaped answer)"),
 ("drop_clusters_reviewed_on_cadence","FN-5 drop-off clusters are not reviewed on a recorded cadence against the three known clusters (account wall / permission cluster / premature information collection)"),
 ("lighter_reentry_decided_for_high_friction","FN-5 no recorded decision on lighter re-entry for high-friction drops (letting a user who dropped at verification/payment/profile reach a limited version first creates stronger return motivation than any message)"),
]
def main(p):
    s=json.load(open(p)); fails=[m for k,m in CHECKS if s.get(k) is not True]
    for f in fails: print("FAIL",f)
    print(f"RESULT {'PASS' if not fails else 'FAIL'} pass={len(CHECKS)-len(fails)}/{len(CHECKS)} fails={len(fails)}")
    return 0 if not fails else 1
if __name__=="__main__":
    if len(sys.argv)!=2: print("usage: flow_navigation_check.py <state.json>"); sys.exit(2)
    sys.exit(main(sys.argv[1]))
