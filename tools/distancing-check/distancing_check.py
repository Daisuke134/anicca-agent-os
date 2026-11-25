#!/usr/bin/env python3
"""distancing-check: deterministic gate. Stdlib only, offline, free.
Primary sources (read via browser.search this run, 2026-11-25):
- Guo et al. (2022) Cogn Emot 36(8):1531-1554 -- meta-analysis of 48 experimental studies / 102 effect sizes; self-distancing attenuated emotional responses, small effect Hedges g=-0.26 (95%CI -0.36,-0.15). Visual+verbal (externalise and articulate in writing/talking) was stronger than visual-only or pronouns-only approaches.
- Kross et al. (2014) J Pers Soc Psychol 106(2):304-324 -- 7 studies, total N=585; using one's own name / non-first-person pronouns during introspection enhanced self-distancing, reduced distress and maladaptive post-event processing under social stress, and shifted appraisals toward challenge vs threat. Not moderated by trait social anxiety in their meta-analysis (Study 6).
- Ayduk & Kross (2008) Psychol Sci -- N=90 undergraduates; analysing a negative interpersonal experience from a self-distanced (observer) perspective reduced blood-pressure reactivity vs self-immersed analysis.
- Orvell et al. (2023) Psychol Conscious 10(2):164-180 -- proof-of-principle, N=111, ~1h computer training; at 10 days vulnerable self-distancing participants matched less-vulnerable peers on rumination/negative affect; at 3 and 6 months both self-distancing AND active-control (relaxation) groups reported lower depressive symptoms than no-treatment -- preliminary, not distancing-specific at follow-up.
- Kross & Ayduk (2023) Handbook of Emotion Regulation ch.63 -- distancing is a perspective shift away from the self-immersed first-person view; it is NOT avoidance or distraction. Caution: a third-person visual observer perspective provoked social anxiety in some work (Schultz & Heimberg 2008).
Boundary: distancing owns ONLY changing the vantage point on an experience (observer / third-person or name-based self-talk / temporal distance) while still engaging and reconstruing it -- distinct from defusion (changing a thought's function, defusion-check), acceptance+willingness (acceptance-check), expressive writing as disclosure (expressive-writing-check; Park et al. 2016 shows writing can work partly THROUGH distancing), and avoidance/distraction/suppression.
Exit 0=PASS, 1=FAIL."""
import json, sys
def check(d):
    f=[]
    inv=d.get("inventory") or {}
    if not inv.get("distancing_surfaces_inventoried"): f.append("DT-0 distancing surfaces are not inventoried per app (any prompt that shifts perspective: observer view, name/you self-talk, fly-on-the-wall, temporal 'how will this feel in a year')")
    if not inv.get("distancing_defined_as_perspective_shift_while_engaging_distinct_from_avoidance_distraction_suppression_defusion"): f.append("DT-0 distancing is not defined as a perspective shift that still engages and reconstrues the experience, distinct from avoidance, distraction, suppression and defusion")
    if not inv.get("evidence_scope_and_counterweight_audited"): f.append("DT-0 evidence scope/counterweight is not audited (Guo 2022: small g=-0.26, mostly lab experiments; Orvell 2023 follow-up gains were shared with relaxation control; observer perspective can provoke social anxiety in some contexts)")
    des=d.get("design") or {}
    if not des.get("named_distancing_technique_with_externalisation_present"): f.append("DT-1 no named distancing technique that externalises and articulates (Guo 2022: visual+verbal -- writing/talking it through from the distanced view -- beat visual-only and pronouns-only; a pronoun swap alone is the weaker form)")
    if not des.get("event_chosen_by_user_and_can_stop_or_return_to_first_person"): f.append("DT-1 the event is not chosen by the user / user cannot stop or return to first person (the user picks the experience and can end the exercise; no forced observer view of a painful memory)")
    if not des.get("distancing_paired_with_reconstrual_and_a_next_action"): f.append("DT-1 distancing is not paired with reconstrual and a next action (distanced reflection should end in a broader re-reading of the event and a concrete next step, not detached numbness)")
    pro=d.get("prohibitions") or {}
    if pro.get("avoidance_or_distraction_counted_as_distancing"): f.append("DT-2 avoidance/distraction (looking away, thinking of unrelated facts, numbing) is counted as distancing (Kross & Ayduk: distancing engages the experience from a new vantage; avoidance disengages from it)")
    if pro.get("cold_detachment_or_dismissal_of_feelings_used"): f.append("DT-2 cold detachment / dismissal is used ('it doesn't matter, stop feeling it') -- distancing changes perspective, it does not invalidate the feeling or the person who felt it")
    if pro.get("distress_moment_used_to_paywall_the_exercise"): f.append("DT-2 the moment a painful experience is surfaced is used to paywall the exercise (core exercise must precede any paywall)")
    mea=d.get("measurement") or {}
    if not mea.get("counts_recorded_not_rates_only"): f.append("DT-3 counts are not recorded (exercises offered, started, completed, stopped early, technique used) -- rates alone hide whether any distancing happened")
    if not mea.get("reactivity_and_reconstrual_measured_separately"): f.append("DT-3 emotional reactivity and reconstrual are not measured separately (distancing should lower reactivity AND shift recounting toward reconstruing; lower reactivity via avoidance alone is not the mechanism)")
    if not mea.get("followup_measured_not_only_immediate_calm"): f.append("DT-3 no follow-up is measured (rumination / intrusive ideation later, and the next action taken) -- immediate calm alone does not show distanced reflection worked, cf. Orvell 2023 10-day and 3/6-month windows")
    cit=d.get("citation") or {}
    if not cit.get("source_numbers_cited_with_design"): f.append("DT-4 source claims are not cited with their design (Guo 2022: 48 studies/102 effects, g=-0.26; Kross 2014: 7 studies N=585; Ayduk & Kross 2008: N=90 BP reactivity; Orvell 2023: N=111 preliminary training)")
    if cit.get("effect_claimed_as_cure_or_lab_effect_claimed_as_clinical_outcome"): f.append("DT-4 the effect is claimed as a cure, or a small lab effect (g=-0.26) is claimed as a clinical outcome (no such evidence)")
    if not cit.get("revenue_chain_recorded"): f.append("DT-4 the revenue chain is not recorded (exercise offered -> practised with counts -> reactivity/reconstrual read separately -> follow-up rumination and next action -> retention read; no chain may be asserted from lab studies alone)")
    eth=d.get("ethics") or {}
    if eth.get("clinical_claim_made"): f.append("DT-5 a clinical claim is made (treats/cures depression/anxiety) -- this is small lab-experimental evidence, not an app claim")
    if not eth.get("core_distancing_available_to_free_users"): f.append("DT-5 core distancing exercise is not available to free users")
    if not eth.get("review_cadence_recorded"): f.append("DT-5 no review cadence is recorded for re-auditing distancing surfaces")
    return f
def main():
    d=json.load(open(sys.argv[1])); fails=check(d)
    for x in fails: print("FAIL:",x)
    print(f"{'PASS' if not fails else 'FAIL'}: {len(fails)} fail(s) -- {d.get('app')}")
    sys.exit(0 if not fails else 1)
if __name__=="__main__": main()
