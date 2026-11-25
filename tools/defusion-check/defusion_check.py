#!/usr/bin/env python3
"""defusion-check: deterministic gate. Stdlib only, offline, free.
Primary sources (read via browser.search this run, 2026-11-25):
- Masuda et al. (2004) Behav Res Ther 42:477-485 -- 8 single-case alternating designs; rapid repetition (30s) of a one-word version of a negative self-referential thought reduced believability and discomfort more than distraction and thought control. Tiny lab sample, not a clinical trial.
- Masuda et al. (2009) Behav Modif 33(2):250-262 -- parametric: discomfort bottomed out after 3-10s repetition, believability after 20-30s. Distinct functions, distinct time courses.
- Levin et al. (2012) Behav Ther 43:741-756 -- meta-analysis of 66 laboratory component studies; defusion/acceptance components showed significant effects vs inactive comparisons, larger for theoretically specified outcomes and experiential methods vs rationale alone.
- Ren et al. (2019) Acta Psychol Sinica 51:662-676 MASEM (50 studies) -- mediation via psychological flexibility, acceptance, present-moment and values was significant; cognitive defusion mediation was NOT significant. Counterweight: isolated lab believability effects do not prove defusion drives clinical outcomes.
- JMIR 2022 iACT process meta-analysis (34 RCTs) -- iACT had only a small effect on cognitive defusion as a process measure at posttest.
Boundary: defusion owns ONLY changing the function/context of a thought (seeing it as a thought, reducing its believability/behaviour-regulatory grip) without changing its content, frequency or truth -- distinct from restructuring/disputation, suppression/distraction, acceptance+willingness (acceptance-check), and mindfulness attention practice (mindfulness-check).
Exit 0=PASS, 1=FAIL."""
import json, sys
def check(d):
    f=[]
    inv=d.get("inventory") or {}
    if not inv.get("defusion_surfaces_inventoried"): f.append("CD-0 defusion surfaces are not inventoried per app (any prompt that labels, repeats, sings, externalises or distances a thought)")
    if not inv.get("defusion_defined_as_changing_thought_function_not_content_frequency_or_truth_distinct_from_restructuring_suppression_distraction"): f.append("CD-0 defusion is not defined as changing a thought's function/context (believability and grip), distinct from restructuring its content, suppressing it, or distracting from it")
    if not inv.get("evidence_scope_and_counterweight_audited"): f.append("CD-0 evidence scope/counterweight is not audited (lab component studies and tiny single-case work; Ren 2019 MASEM found defusion mediation not significant; iACT effect on defusion process was small)")
    des=d.get("design") or {}
    if not des.get("named_defusion_technique_with_dose_present"): f.append("CD-1 no named defusion technique with dose (e.g. labelling 'I am having the thought that...', word repetition 20-30s for believability per Masuda 2009, leaves-on-a-stream -- rationale alone is weaker than experiential methods per Levin 2012)")
    if not des.get("thought_chosen_by_user_and_can_stop"): f.append("CD-1 the thought is not chosen by the user / user cannot stop (the user picks the sticky thought and can end the exercise; no forced repetition of a distressing word)")
    if not des.get("defusion_paired_with_a_next_valued_action"): f.append("CD-1 defusion is not paired with a next valued action (loosening a thought's grip is in service of acting on values, not an end-state of feeling detached)")
    pro=d.get("prohibitions") or {}
    if pro.get("restructuring_or_disputation_counted_as_defusion"): f.append("CD-2 restructuring/disputation (arguing the thought is false, evidence-for/against) is counted as defusion (that changes content/truth, the opposite move)")
    if pro.get("ridicule_or_mockery_of_users_thought_used"): f.append("CD-2 ridicule/mockery of the user's thought is used (silly voices or singing may be offered only as a user-chosen option, never imposed on a painful thought, and never as shaming)")
    if pro.get("distress_moment_used_to_paywall_the_exercise"): f.append("CD-2 the moment a sticky distressing thought is surfaced is used to paywall the exercise (core exercise must precede any paywall)")
    mea=d.get("measurement") or {}
    if not mea.get("counts_recorded_not_rates_only"): f.append("CD-3 counts are not recorded (exercises offered, started, completed, stopped early, technique used) -- rates alone hide whether any defusion happened")
    if not mea.get("believability_and_discomfort_measured_separately"): f.append("CD-3 believability and discomfort are not measured separately (Masuda 2009: they are distinct functions with distinct time courses, 3-10s vs 20-30s)")
    if not mea.get("behaviour_followup_measured_not_only_immediate_believability"): f.append("CD-3 no behaviour follow-up is measured (whether the user then did the valued action) -- immediate believability drop alone does not show defusion changed behaviour, cf. Ren 2019 null mediation")
    cit=d.get("citation") or {}
    if not cit.get("source_numbers_cited_with_design"): f.append("CD-4 source claims are not cited with their design (Masuda 2004: 8 single-case designs, 30s repetition; Levin 2012: 66 lab component studies; Ren 2019: defusion mediation n.s.)")
    if cit.get("effect_claimed_as_cure_or_lab_effect_claimed_as_clinical_outcome"): f.append("CD-4 the effect is claimed as a cure, or a lab believability effect is claimed as a clinical outcome (no such evidence)")
    if not cit.get("revenue_chain_recorded"): f.append("CD-4 the revenue chain is not recorded (exercise offered -> practised with counts -> believability/discomfort read separately -> valued action followed -> retention read; no chain may be asserted from lab studies alone)")
    eth=d.get("ethics") or {}
    if eth.get("clinical_claim_made"): f.append("CD-5 a clinical claim is made (treats/cures anxiety/depression) -- this is lab/component evidence, not an app claim")
    if not eth.get("core_defusion_available_to_free_users"): f.append("CD-5 core defusion exercise is not available to free users")
    if not eth.get("review_cadence_recorded"): f.append("CD-5 no review cadence is recorded for re-auditing defusion surfaces")
    return f
def main():
    d=json.load(open(sys.argv[1])); fails=check(d)
    for x in fails: print("FAIL:",x)
    print(f"{'PASS' if not fails else 'FAIL'}: {len(fails)} fail(s) -- {d.get('app')}")
    sys.exit(0 if not fails else 1)
if __name__=="__main__": main()
