#!/usr/bin/env python3
"""prosocial-check: deterministic gate for prosocial / acts-of-kindness design.
Stdlib only, offline, free.
Primary sources (read via browser.search this run, 2026-11-25):
- Dunn, Aknin & Norton (2008) Science 319:1687, DOI 10.1126/science.1150952 --
  nationally representative survey: prosocial spending predicted happiness
  (b=0.11, p<.01) while personal spending did not (b=-0.02, NS), independent of
  income; windfall field study replicated longitudinally; experiment: $5 or $20
  to spend by end of day, prosocial assignees happier that evening, AMOUNT had
  no bearing; forecasters predicted the opposite on both counts.
- Dunn, Aknin & Norton, Current Directions in Psychological Science review
  (Harvard DASH) -- benefits emerge around the world and in toddlers; strongest
  when giving satisfies relatedness, competence and autonomy; buying the same
  gift bag for a sick child raised mood vs buying it for oneself.
- Curry et al. (2018) J Exp Soc Psychol 76:320-329 meta-analysis -- 27 studies,
  N=4,045, 52 effect sizes: acts of kindness raise the ACTOR's wellbeing
  delta=0.28 (small-to-medium), not moderated by sex/age/intervention type.
Boundary: prosocial owns ONLY the surface where the USER performs a real act
benefiting a specific other person (gift, help, kind message, time). It does
NOT own loving-kindness meditation (an internal practice, loving-kindness-
check), gratitude journaling (gratitude-check), gifting a subscription
(gift-check), or referral invites (referral-check). Guilt, public ranking or
paying-to-give mechanics are fails (PS-2).
Exit 0 = PASS, 1 = FAIL.
"""
import json, sys
def check(d):
    f=[]
    inv=d.get("inventory") or {}
    if not inv.get("prosocial_surfaces_inventoried"): f.append("PS-0 prosocial surfaces are not inventoried per app (prompts to gift/help/thank a specific person, kindness challenges, share-a-word flows)")
    if not inv.get("prosocial_defined_as_real_act_for_specific_other_distinct_from_meditation_or_journaling"): f.append("PS-0 prosocial is not defined as the user performing a real act benefiting a specific other person, distinct from loving-kindness meditation, gratitude journaling and subscription gifting")
    if not inv.get("guilt_or_ranking_prompts_audited"): f.append("PS-0 existing prompts have not been audited for guilt/shame framing or public ranking (sources test voluntary acts; coerced giving is a different, untested intervention)")
    des=d.get("design") or {}
    if not des.get("act_is_user_chosen_recipient_and_form"): f.append("PS-1 the act is not user-chosen in recipient and form (Dunn/Aknin/Norton review: benefits are strongest when autonomy is satisfied -- an assigned recipient with an assigned act removes the condition the effect depends on)")
    if not des.get("impact_or_recipient_response_made_visible"): f.append("PS-1 the impact is not made visible to the actor (competence condition: the actor must be able to see the act landed -- an act sent into a void with no confirmation or response path is not the tested design)")
    if not des.get("no_money_acts_included_not_spending_only"): f.append("PS-1 only money acts are offered (Curry 2018 covers acts of kindness broadly -- time, help and kind words; Dunn 2008 found amount spent had NO effect, so a money-only design adds cost without source support)")
    pro=d.get("prohibitions") or {}
    if pro.get("giving_guilt_tripped_or_shamed"): f.append("PS-2 giving is guilt-tripped or non-givers are shamed (no source tests coerced giving; shame framing converts a voluntary act into compliance)")
    if pro.get("public_leaderboard_or_social_pressure_ranking"): f.append("PS-2 acts are publicly ranked or leader-boarded (public pressure is a conversion lever, not a condition in any cited study)")
    if pro.get("act_paywalled_or_donation_upsold_by_app"): f.append("PS-2 the act itself is paywalled, or the app upsells its own donation/subscription at the giving moment (the tested act benefits the OTHER person; inserting the app as beneficiary changes the intervention)")
    mea=d.get("measurement") or {}
    if not mea.get("actor_wellbeing_measured_not_recipient_only"): f.append("PS-3 the ACTOR's wellbeing is not measured (the replicated finding is an effect on the giver -- Curry 2018 delta=0.28 on actor wellbeing; measuring only recipient outcomes or act counts misses the claimed mechanism)")
    if not mea.get("counts_recorded_not_rates_only"): f.append("PS-3 counts are not recorded (prompt shown, act started, act completed, impact seen, skipped) -- rates alone hide whether any act ever happened")
    if not mea.get("chosen_vs_assigned_acts_compared"): f.append("PS-3 chosen acts and assigned acts are not compared (autonomy is a named moderator in the review literature; pooling them hides whether the design condition is doing the work)")
    cit=d.get("citation") or {}
    if not cit.get("source_numbers_cited_with_design"): f.append("PS-4 source claims are not cited with their design (Dunn 2008 Science: survey + windfall + $5/$20 experiment; Curry 2018 meta: 27 studies, N=4,045, delta=0.28)")
    if cit.get("small_effect_claimed_as_happiness_guarantee"): f.append("PS-4 a small-to-medium effect (delta=0.28) is claimed as a happiness guarantee or lasting transformation (honest claim: 'small lift in the giver's mood/wellbeing')")
    if not cit.get("revenue_chain_recorded"): f.append("PS-4 the revenue chain is not recorded (prosocial prompt -> real act completed -> actor warm glow / relatedness -> return and renewal, each measured locally; Dunn 2008 amount-null also means spend size is not the lever)")
    eth=d.get("ethics") or {}
    if eth.get("clinical_claim_made"): f.append("PS-5 a clinical claim is made (treats depression) -- Curry 2018 measures subjective wellbeing, not clinical outcomes; this is not a treatment")
    if not eth.get("prosocial_prompts_available_to_free_users"): f.append("PS-5 prosocial prompts are not available to free users")
    if not eth.get("review_cadence_recorded"): f.append("PS-5 no review cadence is recorded for re-auditing prosocial surfaces when they change")
    return f
def main():
    d=json.load(open(sys.argv[1])); fails=check(d)
    for x in fails: print("FAIL:",x)
    print(f"{'PASS' if not fails else 'FAIL'}: {len(fails)} fail(s) -- {d.get('app')}")
    sys.exit(0 if not fails else 1)
if __name__=="__main__": main()
