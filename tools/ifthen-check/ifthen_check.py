#!/usr/bin/env python3
"""ifthen-check: gate for implementation intentions (if-then plans) in a
behaviour app - a strong goal first, a concrete cue linked to a concrete
immediately-startable action in conditional format, written and rehearsed,
reminded in advance and distributed (not massed), revisable when the goal
changes, and judged against the publication-bias-corrected effect, not the
headline one. Stdlib only, offline, free. Exit 0=PASS, 1=FAIL.
Sources (read in full 2026-11-24):
- neur.ro evidence review of Gollwitzer (1999), Gollwitzer & Sheeran (2006)
  and Sheeran, Listrom & Gollwitzer (2024)
  https://neur.ro/en/implementation-intentions/
  2006: 94 tests, goal attainment d=0.65 (initiation d=0.61, shielding
  d=0.77 in the NCI summary). 2024: 642 tests, simple average d=0.36,
  robust-Bayesian publication-bias correction d=0.15 (0.08-0.22) - robust
  but small and highly variable. Effects larger with conditional if-then
  format, strong goal intention, rehearsal and commitment. No effect
  without a real goal (plan effect disappears when the goal is dropped).
- Pirolli et al., JMIR preprint 8217 (mHealth, N=64, 28 days)
  https://preprints.jmir.org/preprint/8217
  Reminders for the plan raised daily goal success OR=7.52 (p<.001);
  frequency x distribution interaction as ACT-R predicts (distributed
  beats massed); time since acknowledging a reminder was significant -
  recall at the moment matters.
- Prestwich et al. / Interacting with Computers 2019 (plan reminders):
  plan reminders sent IN ADVANCE improve compliance and plan recall,
  not necessarily automaticity; generic reminders create dependency.
Separation: commitment-check owns Apple's 12-month billing commitment;
contextual-trigger-check owns notification timing/context; answer-
persistence owns storing onboarding answers. This gate owns only the
if-then plan itself: its formation, format, reminder and revision.
NOT adopted: quoting d=0.65 as an expected or marketed effect (the
corrected estimate is d=0.15), and stacking many simultaneous plans.
"""
import json, sys
CHECKS=[
 ("per_app_ifthen_surface_recorded","II-0 no per-app record of whether an if-then plan surface exists (without a record there is no formation, reminder or read to judge)"),
 ("goal_intention_recorded_before_plan","II-0 the goal intention is not recorded before the plan is formed (an implementation intention serves a goal; it does not replace or create it - Gollwitzer 1999)"),
 ("plan_linked_to_single_named_goal","II-0 the plan is not linked to one named goal (a floating plan with no goal has no measured effect; when the goal was dropped in Seehausen et al. the plan effect disappeared within 48h)"),
 ("conditional_ifthen_format_used","II-1 the plan is not in conditional if-then format (effects were larger with a conditional format than with a plain 'I will do X tomorrow' intention - Sheeran et al. 2024)"),
 ("cue_concrete_and_recognisable","II-1 the if-cue is not a concrete recognisable situation (a time, place or routine event the person will notice at the right moment; a vague cue cannot become easier to notice - the first supported mechanism)"),
 ("action_concrete_observable_immediately_startable","II-1 the then-action is not concrete, observable and immediately startable (the second supported mechanism is an automated response; an action that needs further decisions at the cue does not automate)"),
 ("plan_written_externalised","II-2 the plan is not written / externalised (the strongest studies commit the plan to a visible external form; a silent in-head decision weakens the cue-response link)"),
 ("plan_rehearsed_at_formation","II-2 the plan is not rehearsed at formation (effects were larger when plans were rehearsed / fixed in mind - Sheeran et al. 2024)"),
 ("commitment_to_plan_recorded","II-2 commitment to the plan is not recorded (stronger commitment to the plan produced larger effects - Gollwitzer 1999)"),
 ("plan_reminder_sent_in_advance_of_cue","II-3 no plan reminder is sent in advance of the cue (plan reminders in advance improve compliance and recall; a reminder at or after the moment is a generic nag, and generic reminders breed dependency)"),
 ("reminders_distributed_not_massed","II-3 plan reminders are massed rather than distributed (Pirolli mHealth: frequency x distribution interaction as ACT-R predicts - distributed reminders sustain the cue-response link, massed ones decay)"),
 ("plan_recall_checked","II-3 plan recall is not checked (Pirolli: time since acknowledging a reminder was highly significant; the 2025 driver follow-up found benefit only where recall was accurate - an unremembered plan cannot fire)"),
 ("plan_editable_and_replaced_when_goal_changes","II-4 the plan cannot be edited / replaced when the goal or routine changes (a fixed plan for a dropped goal is dead weight and its rigidity blocks suitable alternatives - Gollwitzer 1999)"),
 ("failed_cue_reviewed_not_just_repeated","II-4 a cue that repeatedly fails to fire is not reviewed (re-sending the same plan louder treats a cue-design failure as a motivation failure)"),
 ("single_active_plan_per_goal","II-4 more than one active if-then plan per goal is allowed (stacked competing plans for one goal split the cue link; the evidence base forms one plan per goal striving episode)"),
 ("expectation_set_to_corrected_effect","II-5 expectations / claims are not set to the corrected effect (2024 robust-Bayesian correction: d=0.15, interval 0.08-0.22 - quoting the uncorrected d=0.65 as expected or marketed effect overstates the evidence fourfold)"),
 ("initiation_at_cue_measured","II-5 action initiation at the cue is not measured (the mechanism outcome is starting when the cue appears - initiation d=0.61 - not only the distal goal outcome weeks later)"),
 ("plan_cohort_read_separately","II-5 plan-formers are not read as a separate cohort (mixing plan and no-plan users makes the plan's effect - and its high variability across studies - unreadable in your own data)"),
]
def main(p):
    s=json.load(open(p)); fails=[m for k,m in CHECKS if s.get(k) is not True]
    for f in fails: print("FAIL",f)
    print(f"RESULT {'PASS' if not fails else 'FAIL'} pass={len(CHECKS)-len(fails)}/{len(CHECKS)} fails={len(fails)}")
    return 0 if not fails else 1
if __name__=="__main__":
    if len(sys.argv)!=2: print("usage: ifthen_check.py <state.json>"); sys.exit(2)
    sys.exit(main(sys.argv[1]))
