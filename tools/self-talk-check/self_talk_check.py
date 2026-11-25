#!/usr/bin/env python3
"""self-talk-check: deterministic gate for planned self-talk design.
Stdlib only, offline, free.
Primary sources (read via browser.search this run, 2026-11-25):
- Hatzigeorgiadis et al. (2011) Perspect Psychol Sci 6(4):348-356 --
  meta-analysis of 32 studies / 62 effect sizes: planned self-talk
  interventions improved task performance, ES=.48 (moderate). More
  effective for fine than gross motor tasks and for novel than
  well-learned tasks; instructional self-talk beat motivational
  self-talk for fine tasks; interventions WITH self-talk training
  were more effective than untrained cue delivery.
- Tod, Hardy & Oliver (2011) J Sport Exerc Psychol -- systematic
  review of 47 studies: benefits for positive, instructional and
  motivational self-talk; negative self-talk did NOT consistently
  impede performance; authors advised against thought-stopping.
Boundary: distancing-check owns perspective shift (name/non-first-
person); this gate owns cue TYPE matched to the task (instructional
cue = next step/technique; motivational cue = effort/confidence),
whether the cue is planned and PRACTISED (not just delivered), and
whether harsh self-criticism is replaced rather than suppressed.
Exit 0 = PASS, 1 = FAIL.
"""
import json, sys
def check(d):
    f=[]
    inv=d.get("inventory") or {}
    if not inv.get("self_talk_surfaces_inventoried"): f.append("ST-0 self-talk surfaces are not inventoried per app")
    if not inv.get("self_talk_defined_as_planned_cue_distinct_from_affirmation_repetition_distancing_thought_stopping"): f.append("ST-0 self-talk is not defined as a planned task cue, distinct from generic affirmation repetition, distancing, and thought-stopping")
    if not inv.get("evidence_scope_and_counterweight_audited"): f.append("ST-0 evidence scope/counterweight not audited (Hatzigeorgiadis 2011 sport/lab ES=.48; Tod 2011 negative self-talk not consistently harmful)")
    des=d.get("design") or {}
    if not des.get("cue_type_matched_to_task_instructional_for_precise_or_new_steps_motivational_for_effort_persistence"): f.append("ST-1 cue type is not matched to the task (instructional for precise/new steps, motivational for effort/persistence)")
    if not des.get("cue_short_user_chosen_and_practised_not_only_delivered"): f.append("ST-1 the cue is not short, user-chosen and practised (trained cues beat delivered-only cues, Hatzigeorgiadis 2011)")
    if not des.get("cue_tied_to_a_specific_upcoming_action_not_generic_mood_claim"): f.append("ST-1 the cue is not tied to a specific upcoming action (it is a generic mood claim)")
    pro=d.get("prohibitions") or {}
    if pro.get("thought_stopping_or_suppression_of_negative_self_talk_used"): f.append("ST-2 thought-stopping / suppression of negative self-talk is used (Tod 2011 advises against it)")
    if pro.get("harsh_or_shaming_cue_used"): f.append("ST-2 a harsh or shaming cue is used")
    if pro.get("distress_moment_used_to_paywall_the_exercise"): f.append("ST-2 the distress moment is used to paywall the self-talk exercise")
    mea=d.get("measurement") or {}
    if not mea.get("counts_recorded_not_rates_only"): f.append("ST-3 counts are not recorded (cues offered, chosen, practised, used, early stops, cue type)")
    if not mea.get("task_completion_and_affect_measured_separately"): f.append("ST-3 task completion and affect are not measured separately")
    if not mea.get("followup_measured_not_only_immediate_calm"): f.append("ST-3 follow-up is not measured (only immediate calm is read)")
    cit=d.get("citation") or {}
    if not cit.get("source_numbers_cited_with_design"): f.append("ST-4 source numbers are not cited with design (Hatzigeorgiadis 32 studies/62 ES, ES=.48 / Tod 47 studies)")
    if cit.get("sport_lab_effect_claimed_as_clinical_or_product_promise"): f.append("ST-4 a sport/lab effect is claimed as a clinical or product/revenue promise")
    if not cit.get("revenue_chain_recorded"): f.append("ST-4 revenue chain is not recorded")
    eth=d.get("ethics") or {}
    if eth.get("clinical_claim_made"): f.append("ST-5 a clinical claim is made")
    if not eth.get("core_self_talk_available_to_free_users"): f.append("ST-5 core self-talk is not available to free users")
    if not eth.get("review_cadence_recorded"): f.append("ST-5 no review cadence is recorded")
    return f
def main():
    d=json.load(open(sys.argv[1])); fails=check(d)
    for x in fails: print("FAIL:",x)
    print(f"{'PASS' if not fails else 'FAIL'}: {len(fails)} fail(s) -- {d.get('app')}")
    sys.exit(0 if not fails else 1)
if __name__=="__main__": main()
