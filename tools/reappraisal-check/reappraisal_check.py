#!/usr/bin/env python3
"""reappraisal-check: deterministic gate for cognitive reappraisal design.
Stdlib only, offline, free.
Primary sources (read via browser.search this run, 2026-11-25):
- Webb, Miles & Sheeran (2012) Psychol Bull 138(4):775-808 -- meta-analysis
  of 306 experimental comparisons: cognitive change d+=0.36 (small-to-medium),
  response modulation d+=0.16, attentional deployment d+=0.00. Within
  cognitive change: reappraising the stimulus d+=0.36 and perspective taking
  d+=0.45 beat reappraising the emotional response d+=0.23. Suppressing the
  experience/thought did not work (d+=-0.04 / -0.12).
- Buhle et al. (2014) Cereb Cortex 24(11):2981-2990 -- meta-analysis of 48
  neuroimaging studies: reappraisal = changing how one thinks about a
  stimulus to change its affective impact; consistently activated cognitive
  control + lateral temporal cortex and modulated bilateral amygdala.
- Troy, Shallcross & Mauss (2013) Psychol Sci 24(12):2505-2514, N=170 --
  reappraisal ability was associated with lower depression for
  UNCONTROLLABLE stressors but greater depression for CONTROLLABLE stressors.
  Reappraisal is not adaptive per se; adaptiveness depends on context.
Boundary: distancing-check owns perspective shift while engaging;
defusion-check owns changing the function of thoughts; acceptance-check owns
willingness. This gate owns only changing the INTERPRETATION of the
stimulus/situation itself, whether the new interpretation is plausible and
user-generated, and whether a controllable situation is paired with action
instead of reframing alone.
Exit 0 = PASS, 1 = FAIL.
"""
import json, sys
def check(d):
    f=[]
    inv=d.get("inventory") or {}
    if not inv.get("reappraisal_surfaces_inventoried"): f.append("RA-0 reappraisal surfaces are not inventoried per app")
    if not inv.get("reappraisal_defined_as_changing_interpretation_of_stimulus_distinct_from_suppression_distraction_distancing_defusion_toxic_positivity"): f.append("RA-0 reappraisal is not defined as changing the interpretation of the stimulus/situation, distinct from suppression, distraction, distancing, defusion and forced positivity")
    if not inv.get("evidence_scope_and_counterweight_audited"): f.append("RA-0 evidence scope/counterweight not audited (Webb 2012 d+=0.36 lab experiments; Troy 2013 controllability reversal)")
    des=d.get("design") or {}
    if not des.get("named_technique_targets_stimulus_or_situation_not_only_emotional_response"): f.append("RA-1 no named technique targets the stimulus/situation (Webb: stimulus 0.36 / perspective 0.45 vs response 0.23)")
    if not des.get("alternative_interpretation_user_generated_and_plausible_not_imposed"): f.append("RA-1 the alternative interpretation is imposed or implausible, not generated and checked for plausibility by the user")
    if not des.get("controllability_checked_and_controllable_paired_with_action"): f.append("RA-1 controllability is not checked / a controllable stressor is reframed alone without pairing with action or problem-solving (Troy 2013)")
    pro=d.get("prohibitions") or {}
    if pro.get("forced_positivity_or_invalidation_used"): f.append("RA-2 forced positivity / invalidation is used ('look on the bright side' that denies the facts)")
    if pro.get("suppression_or_distraction_counted_as_reappraisal"): f.append("RA-2 suppression or distraction is counted as reappraisal")
    if pro.get("distress_moment_used_to_paywall_the_exercise"): f.append("RA-2 the distress moment is used to paywall the reappraisal exercise")
    mea=d.get("measurement") or {}
    if not mea.get("counts_recorded_not_rates_only"): f.append("RA-3 counts are not recorded (prompts, attempts, completions, early stops, technique)")
    if not mea.get("interpretation_change_and_affect_change_measured_separately"): f.append("RA-3 interpretation change and affect change are not measured separately")
    if not mea.get("followup_measured_not_only_immediate_calm"): f.append("RA-3 follow-up is not measured (only immediate calm is read)")
    cit=d.get("citation") or {}
    if not cit.get("source_numbers_cited_with_design"): f.append("RA-4 source numbers are not cited with design (Webb 306 comparisons / Buhle 48 neuroimaging / Troy N=170)")
    if cit.get("lab_effect_claimed_as_clinical_or_product_promise"): f.append("RA-4 a lab effect is claimed as a clinical or product/revenue promise")
    if not cit.get("revenue_chain_recorded"): f.append("RA-4 revenue chain is not recorded")
    eth=d.get("ethics") or {}
    if eth.get("clinical_claim_made"): f.append("RA-5 a clinical claim is made")
    if not eth.get("core_reappraisal_available_to_free_users"): f.append("RA-5 core reappraisal is not available to free users")
    if not eth.get("review_cadence_recorded"): f.append("RA-5 no review cadence is recorded")
    return f
def main():
    d=json.load(open(sys.argv[1])); fails=check(d)
    for x in fails: print("FAIL:",x)
    print(f"{'PASS' if not fails else 'FAIL'}: {len(fails)} fail(s) -- {d.get('app')}")
    sys.exit(0 if not fails else 1)
if __name__=="__main__": main()
