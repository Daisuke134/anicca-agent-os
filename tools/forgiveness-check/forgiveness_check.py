#!/usr/bin/env python3
"""forgiveness-check: deterministic gate for forgiveness intervention design.
Stdlib only, offline, free.
Primary sources (read via browser.search this run, 2026-11-25):
- Wade, Hoyt, Kidwell & Worthington (2014) J Consult Clin Psychol 82(1):154-170,
  DOI 10.1037/a0035268 -- meta-analysis, 54 reports, k=53 posttreatment
  (N=2,323): explicit forgiveness treatments > no treatment Delta=0.56
  [0.43,0.68] and > alternative treatments Delta=0.45 [0.21,0.69]; greater
  change in depression, anxiety and hope vs no treatment. Dosage (longer)
  and individual modality uniquely predicted change vs no treatment.
- Ho et al. (2024) BMJ Public Health 2:e000072, DOI 10.1136/bmjph-2023-000072 --
  multisite waitlist RCT, N=4,598 (Colombia, Hong Kong, Indonesia, South
  Africa, Ukraine): self-directed REACH workbook, immediate vs delayed:
  unforgiveness SMD -0.53 [-0.58,-0.47], depression -0.22, anxiety -0.21
  at 2 weeks. Workbook is secular, self-directed, ~2-3 hours.
- Worthington REACH: Recall, Empathize, Altruistic gift, Commit, Hold on.
  Decisional forgiveness (intention not to retaliate) is distinct from
  emotional forgiveness (replacement of unforgiving emotions).
Boundary: forgiveness owns ONLY work on a SPECIFIC interpersonal hurt where
the user works toward forgiving a specific offender. It does NOT own
self-compassion (self-compassion-check, for the self), loving-kindness
wishes (loving-kindness-check), prosocial acts (prosocial-check), or
reconciliation (forgiveness does NOT require reconciling, excusing,
condoning or returning to an unsafe relationship). Pressuring a user --
especially after abuse -- to forgive is a fail (FG-2).
Exit 0 = PASS, 1 = FAIL.
"""
import json, sys
def check(d):
    f=[]
    inv=d.get("inventory") or {}
    if not inv.get("forgiveness_surfaces_inventoried"): f.append("FG-0 forgiveness surfaces are not inventoried per app (any prompt/flow inviting the user to forgive a specific person for a specific hurt)")
    if not inv.get("forgiveness_defined_as_specific_hurt_decisional_and_emotional_distinct_from_reconciliation_or_excusing"): f.append("FG-0 forgiveness is not defined as work on a specific hurt, with decisional vs emotional forgiveness distinguished, and distinct from reconciliation, excusing or condoning")
    if not inv.get("safety_and_pressure_prompts_audited"): f.append("FG-0 existing prompts have not been audited for pressure to forgive, especially after abuse or ongoing harm (sources test voluntary work on a chosen transgression; coerced forgiveness is a different, untested intervention)")
    des=d.get("design") or {}
    if not des.get("process_steps_present_not_decision_only"): f.append("FG-1 no process is present (Wade 2014 / REACH: forgiveness is worked through -- Recall, Empathize, Altruistic gift, Commit, Hold on; a one-tap 'decide to forgive' prompt is not the tested design, decision-based brief interventions showed ~0 effect in Baskin & Enright 2004)")
    if not des.get("dose_recorded_and_multi_session"): f.append("FG-1 dose is not recorded / not multi-session (Wade 2014: dosage uniquely predicted change, ~d=0.1 per hour; Ho 2024 workbook is ~2-3 hours -- a single short prompt cannot carry the cited effect)")
    if not des.get("user_chooses_specific_transgression_and_may_stop"): f.append("FG-1 the user does not choose the specific transgression and cannot stop/skip (Ho 2024 eligibility was a self-identified interpersonal transgression; voluntariness is a design condition, not a courtesy)")
    pro=d.get("prohibitions") or {}
    if pro.get("forgiveness_forced_or_guilt_framed"): f.append("FG-2 forgiveness is forced, guilt-framed or presented as a duty/streak obligation (no source tests coerced forgiveness; pressure converts a voluntary process into compliance)")
    if pro.get("forgiveness_equated_with_reconciliation_or_excusing"): f.append("FG-2 forgiveness is equated with reconciling, excusing, condoning or returning to an unsafe relationship (the sources separate these; conflating them can endanger users)")
    if pro.get("forgiveness_paywalled_or_upsold_at_hurt_moment"): f.append("FG-2 the forgiveness process itself is paywalled, or an upsell is placed at the moment of recalling the hurt (the tested workbook is free-of-cost; inserting payment at the hurt changes the intervention)")
    mea=d.get("measurement") or {}
    if not mea.get("unforgiveness_measured_not_mood_only"): f.append("FG-3 unforgiveness itself is not measured (Ho 2024 primary outcome was unforgiveness, TRIM-18, SMD -0.53; measuring only mood misses the claimed mechanism)")
    if not mea.get("counts_recorded_not_rates_only"): f.append("FG-3 counts are not recorded (prompt shown, process started, steps completed, stopped/skipped, dose minutes) -- rates alone hide whether any process ever happened")
    if not mea.get("depression_anxiety_measured_separately_and_followup"): f.append("FG-3 depression/anxiety are not measured separately with a follow-up window (Ho 2024: depression -0.22 and anxiety -0.21 at 2 weeks, smaller than the unforgiveness effect; pooling or immediate-only reads overstate it)")
    cit=d.get("citation") or {}
    if not cit.get("source_numbers_cited_with_design"): f.append("FG-4 source claims are not cited with their design (Wade 2014 meta: 54 reports, N=2,323, Delta=0.56 vs no treatment; Ho 2024 RCT: N=4,598, unforgiveness -0.53 at 2 weeks vs delayed receipt)")
    if cit.get("effect_claimed_as_cure_or_guaranteed_release"): f.append("FG-4 the effect is claimed as a cure or guaranteed release (honest claim: a multi-hour voluntary process reduced unforgiveness by ~half a standard deviation at 2 weeks in the largest trial)")
    if not cit.get("revenue_chain_recorded"): f.append("FG-4 the revenue chain is not recorded (voluntary forgiveness prompt -> process completed with dose -> unforgiveness down -> return and renewal, each measured locally; no chain may be asserted from the RCT alone)")
    eth=d.get("ethics") or {}
    if eth.get("clinical_claim_made"): f.append("FG-5 a clinical claim is made (treats depression/anxiety) -- Ho 2024 measured symptom reductions as secondary outcomes in a community sample; this is not a treatment")
    if not eth.get("forgiveness_process_available_to_free_users"): f.append("FG-5 the forgiveness process is not available to free users")
    if not eth.get("review_cadence_recorded"): f.append("FG-5 no review cadence is recorded for re-auditing forgiveness surfaces when they change")
    return f
def main():
    d=json.load(open(sys.argv[1])); fails=check(d)
    for x in fails: print("FAIL:",x)
    print(f"{'PASS' if not fails else 'FAIL'}: {len(fails)} fail(s) -- {d.get('app')}")
    sys.exit(0 if not fails else 1)
if __name__=="__main__": main()
