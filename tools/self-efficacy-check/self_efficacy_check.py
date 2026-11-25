#!/usr/bin/env python3
"""self-efficacy-check: gate for building self-efficacy (Bandura).
Bandura (1977, Psychol Rev 84:191-215): efficacy expectations come
from 4 sources - performance accomplishments (mastery, most
influential, based on personal success), vicarious experience,
verbal persuasion, physiological states; the more dependable the
source, the greater the change. Bandura, Adams & Beyer (1977):
efficacy predicted subsequent performance in 92% of tasks, partial
mastery predicted 84% on never-attempted tasks. Keller et al. (2021,
JMIR mHealth, RCT N=232): efficacy mediated outcome (b=-0.09, CI
-0.26 to -0.01) but intervention was NOT superior to active control
and only 47.4% gave post data.
Distinct from anchor-check / ifthen-check / endowed-progress-check:
this gate owns (1) mastery-first graded task design, (2) source
ordering - persuasion/affirmations alone never counted as efficacy
building, (3) efficacy measured per task, separately from outcome
expectancy. Stdlib only, offline, free. Exit 0=PASS, 1=FAIL.
"""
import json, sys
CHECKS=[
 ("efficacy_measured_per_task_not_global","SE-0 self-efficacy is not measured per specific task/domain; a global confidence or mood score is used instead - Bandura: efficacy is a judgement of capability for a specific performance, not a trait"),
 ("efficacy_baseline_taken_before_intervention","SE-0 no baseline efficacy reading is taken before the intervention for that task, so any later change cannot be attributed or even detected"),
 ("efficacy_sources_inventoried_per_surface","SE-0 the four sources (mastery, vicarious, persuasion, physiological state) are not inventoried per surface, so a surface built only of words is mistaken for a capability-building surface"),
 ("first_task_graded_attainable_but_real","SE-1 the first assigned task is not graded to be challenging yet attainable; too hard produces an early failure before efficacy is established, too trivial produces no mastery information"),
 ("success_is_real_performance_not_praise","SE-1 counted success is not the user's real performance of the task; taps, streak animations or praise without performance are recorded as mastery, which they are not"),
 ("difficulty_progresses_from_performance_pattern","SE-1 difficulty does not progress from the user's actual success/failure pattern (scaffold/support withdrawn as mastery grows); a fixed ladder ignores the timing and total pattern of experiences that Bandura shows determines the effect of failure"),
 ("similar_models_used_for_vicarious","SE-2 vicarious material does not use models similar to the user succeeding through effort; superstar or dissimilar models do not raise the observer's efficacy for their own task"),
 ("persuasion_specific_credible_and_subordinate","SE-2 verbal persuasion is not specific and credible and explicitly subordinate to mastery; generic affirmations alone are treated as efficacy building, though persuasion is a weak, easily extinguished source"),
 ("affective_state_not_misread_as_inability","SE-2 the user's arousal/anxiety state is not read as state information; anxiety at task time is left to be misattributed by the user as inability, lowering efficacy"),
 ("efficacy_distinguished_from_outcome_expectancy","SE-3 efficacy (can I do it) is not measured separately from outcome expectancy (will it work); pooling them hides whether the blocker is capability belief or outcome belief, which need different interventions"),
 ("efficacy_read_against_next_performance","SE-3 efficacy is not read against the next actual performance (Bandura's microanalysis: efficacy predicted performance in 92% of tasks); an efficacy score never checked against behaviour is decoration"),
 ("failure_pattern_read_not_single_failure","SE-3 failure is read as a single event rather than by timing and total pattern; one miss after established efficacy has a different meaning from repeated early failures"),
 ("primary_numbers_quoted_with_design","SE-4 the 92% / 84% figures are quoted without their design (Bandura, Adams & Beyer 1977, phobia treatment, participant modelling, microanalysis) - bare numbers strip their conditions"),
 ("expectations_discounted_for_rct_limits","SE-4 expectations are set without discounting for the app RCT evidence: Keller et al. 2021 was not superior to active control, post data came from 47.4% of 232 enrolled, and the mediated effect was small (b=-0.09)"),
 ("no_revenue_promised_from_efficacy_alone","SE-4 revenue or retention is promised from raising efficacy scores alone, without the chain efficacy -> initiation, effort and persistence -> repeated behaviour -> retention being measured"),
 ("no_manufactured_fake_success","SE-5 success is manufactured (rigged easy wins, false feedback, inflated progress) to raise efficacy; efficacy built on false performance collapses on first real contact and is deception"),
 ("no_persuasion_claiming_unsupported_capability","SE-5 persuasion copy claims the user has capabilities or results that no performance evidence supports; persuasion that outruns mastery is extinguished by disconfirming experience"),
 ("mastery_records_kept_and_reused","SE-5 the user's real mastery record is not kept and resurfaced to them (their own past successes are the most dependable efficacy information available and are left unused)"),
]
def main(p):
    s=json.load(open(p)); fails=[m for k,m in CHECKS if s.get(k) is not True]
    for f in fails: print("FAIL",f)
    print(f"RESULT {'PASS' if not fails else 'FAIL'} pass={len(CHECKS)-len(fails)}/{len(CHECKS)} fails={len(fails)}")
    return 0 if not fails else 1
if __name__=="__main__":
    if len(sys.argv)!=2: print("usage: self_efficacy_check.py <state.json>"); sys.exit(2)
    sys.exit(main(sys.argv[1]))
