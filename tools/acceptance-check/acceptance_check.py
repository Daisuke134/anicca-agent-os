#!/usr/bin/env python3
"""acceptance-check: deterministic gate. Stdlib only, offline, free.
Primary sources (read via browser.search this run, 2026-11-25):
- A-Tjak et al. (2015) Psychother Psychosom 84:30-36, DOI 10.1159/000365764 -- 39 RCTs, N=1821; ACT vs controls Hedges g=0.57 (waitlist 0.82, placebo 0.51, TAU 0.64); vs established treatment incl CBT no significant difference (p=.140); secondary outcomes g=0.30, process g=0.56.
- Ost (2014) Behav Res Ther -- 60 RCTs, N=4234; mean effect 0.42, vs cognitive/behavioral treatments 0.16 n.s.; verdict: ACT not yet well-established for any disorder. Cited as the discount on A-Tjak.
- AAQ meta-analysis, Behavior Therapy 55 (2024) 26-41 -- 151 studies, 25 AAQ versions; psychological inflexibility vs well-being r=-.47; mostly cross-sectional, causal reading not licensed.
- Akbari et al. (2022) J Contextual Behav Sci -- experiential avoidance meta-analysis, 441 studies, N=135347; avoidance vs depression r=.562, anxiety r=.506 (correlational, largely trait self-report).
- AAQ-II critique (Wolgast 2014; Rochefort et al.): AAQ-II loads with distress/neuroticism, discriminant validity suboptimal -- do not use AAQ-II alone as the flexibility measure.
Boundary: acceptance owns ONLY willingness to contact unwanted private events (thoughts/feelings/sensations) while persisting/changing behaviour in service of chosen values, distinct from suppression, distraction, endurance of harm, self-compassion (self-compassion-check), savoring, and behavioral activation scheduling (behavioral-activation-check). Evidence is therapist-delivered ACT for clinical problems; an app prompt is not that treatment.
Exit 0=PASS, 1=FAIL."""
import json, sys
def check(d):
    f=[]
    inv=d.get("inventory") or {}
    if not inv.get("acceptance_surfaces_inventoried"): f.append("AC-0 acceptance surfaces are not inventoried per app (any prompt that asks a user to allow, make room for, or stop fighting a difficult thought/feeling)")
    if not inv.get("acceptance_defined_as_willingness_plus_values_action_distinct_from_suppression_distraction_endurance"): f.append("AC-0 acceptance is not defined as willingness to contact unwanted private events while acting on chosen values, distinct from suppression, distraction, white-knuckle endurance, and resignation")
    if not inv.get("evidence_scope_and_measurement_caveat_audited"): f.append("AC-0 evidence scope/measurement caveat is not audited (ACT evidence is therapist-delivered clinical treatment; Ost 2014 g=0.42 and 'not yet well-established'; AAQ-II conflates distress/neuroticism and must not be the sole flexibility measure)")
    des=d.get("design") or {}
    if not des.get("willingness_paired_with_a_chosen_values_action"): f.append("AC-1 acceptance is not paired with a concrete chosen-values action (willingness without committed action is endurance, not psychological flexibility as tested)")
    if not des.get("contact_graded_and_user_controlled_not_forced_exposure"): f.append("AC-1 contact is not graded and user-controlled (the user chooses the step and can stop; forced flooding or 'sit with it no matter what' is not the tested protocol)")
    if not des.get("language_invites_allowing_not_controlling_or_eliminating_feeling"): f.append("AC-1 language does not invite allowing/noticing (it frames the feeling as something to control, fix or eliminate first -- that is the control agenda acceptance replaces)")
    pro=d.get("prohibitions") or {}
    if pro.get("suppression_or_distraction_counted_as_acceptance"): f.append("AC-2 suppression or distraction is counted as acceptance (pushing the thought away / keeping busy to not feel it is experiential avoidance, the opposite process; Akbari 2022 r=.56 with depression)")
    if pro.get("acceptance_used_to_endure_harm_or_bypass_changeable_problems"): f.append("AC-2 acceptance is used to make a user endure harm, injustice or a changeable problem instead of acting (acceptance targets private events, not external conditions that should be changed)")
    if pro.get("unwillingness_shamed_or_framed_as_failure"): f.append("AC-2 unwillingness/struggle is shamed or framed as user failure (struggle is the normal starting point; shaming it adds a second layer of suffering and is not in the protocol)")
    mea=d.get("measurement") or {}
    if not mea.get("counts_recorded_not_rates_only"): f.append("AC-3 counts are not recorded (willingness prompts offered, started, completed, stopped by user, values action taken) -- rates alone hide whether any willingness happened")
    if not mea.get("flexibility_measured_behaviourally_not_aaq2_alone"): f.append("AC-3 flexibility is not measured behaviourally / AAQ-II is used alone (AAQ-II loads with distress and neuroticism; pair any self-report with a behavioural willingness measure: did the user still take the values action while the feeling was present)")
    if not mea.get("outcomes_measured_at_followup_separately_from_same_day_relief"): f.append("AC-3 outcomes are not measured at a follow-up window separately from same-day relief (acceptance can feel worse same-day while functioning improves later; same-day relief alone misreads the mechanism)")
    cit=d.get("citation") or {}
    if not cit.get("source_numbers_cited_with_design"): f.append("AC-4 source claims are not cited with their design (A-Tjak 2015: 39 RCTs, N=1821, g=0.57 vs controls, no significant difference vs CBT; Ost 2014: 60 RCTs, g=0.42, not yet well-established)")
    if cit.get("effect_claimed_as_cure_or_app_equivalent_to_therapy"): f.append("AC-4 the effect is claimed as a cure, or the app surface is claimed equivalent to therapist-delivered ACT (the trials are clinical treatment; no app prompt has that evidence)")
    if not cit.get("revenue_chain_recorded"): f.append("AC-4 the revenue chain is not recorded (willingness prompt -> feeling contacted without suppression -> values action still taken -> follow-up functioning read locally; no chain may be asserted from the meta-analysis alone)")
    eth=d.get("ethics") or {}
    if eth.get("clinical_claim_made"): f.append("AC-5 a clinical claim is made (treats/cures anxiety/depression) -- this is a structured treatment's evidence, not an app claim")
    if not eth.get("core_acceptance_available_to_free_users"): f.append("AC-5 core acceptance/willingness practice is not available to free users")
    if not eth.get("review_cadence_recorded"): f.append("AC-5 no review cadence is recorded for re-auditing acceptance surfaces")
    return f
def main():
    d=json.load(open(sys.argv[1])); fails=check(d)
    for x in fails: print("FAIL:",x)
    print(f"{'PASS' if not fails else 'FAIL'}: {len(fails)} fail(s) -- {d.get('app')}")
    sys.exit(0 if not fails else 1)
if __name__=="__main__": main()
