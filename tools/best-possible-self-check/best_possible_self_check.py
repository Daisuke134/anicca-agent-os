#!/usr/bin/env python3
"""best-possible-self-check: deterministic gate for Best Possible Self (BPS) writing design.
Stdlib only, offline, free.
Primary sources (read via browser.search this run, 2026-11-25):
- King (2001) Pers Soc Psychol Bull: N=81, writing 20 min/day x 4 consecutive days
  about one's best possible future self (everything gone as well as it possibly
  could, having WORKED HARD and succeeded) raised subjective wellbeing at 3 weeks
  and was associated with decreased illness at 5 months vs neutral control.
- Carrillo et al. (2019) PLoS ONE meta-analysis: 29 studies, N=2,909 --
  wellbeing d+=.325, optimism d+=.334, positive affect d+=.511 vs controls;
  small effects for negative affect / depressive symptoms.
- Heekerens & Eid (2021) J Posit Psychol meta-analysis: positive affect
  g=0.28 [0.16,0.41], optimism g=0.21 [0.04,0.38]; optimism significant only as
  positive FUTURE EXPECTATIONS (not general life orientation); NO substantial
  follow-up effects -- the lift fades.
Boundary: BPS owns ONLY the future-self writing surface (user writes, in
concrete detail, a future reached by their own effort). It does NOT own WOOP /
mental contrasting (obstacle + if-then plan, woop-check), self-affirmation
(values writing, self-affirmation-check), or passive manifestation content
(reading/watching a pre-written ideal future). Selling BPS as a guarantee that
the imagined future will arrive is a fail (BPS-2/BPS-4).
Exit 0 = PASS, 1 = FAIL.
"""
import json, sys
def check(d):
    f=[]
    inv=d.get("inventory") or {}
    if not inv.get("bps_surfaces_inventoried"): f.append("BPS-0 best-possible-self surfaces are not inventoried per app (onboarding future vision, manifestation/home, goal setting, New Year / fresh-start moments)")
    if not inv.get("bps_defined_as_user_written_effort_based_future_distinct_from_passive_manifestation"): f.append("BPS-0 BPS is not defined as the user WRITING in concrete detail a future in which they worked hard and succeeded, as distinct from passively reading/watching a pre-written ideal future (King 2001 prompt premise is effort, not wish)")
    if not inv.get("fantasy_only_content_audited"): f.append("BPS-0 existing future/manifestation content has not been audited for fantasy-only form (an imagined outcome with no effort premise, no concrete detail and no writing step has no source basis as BPS)")
    des=d.get("design") or {}
    if not des.get("user_writes_concrete_detail_across_life_domains"): f.append("BPS-1 the user does not write concrete, specific detail of the future self across life domains (vague affirmation text or a single generic sentence is not the King 2001 writing task)")
    if not des.get("dose_matches_source_range"): f.append("BPS-1 dose does not match the source range (King 2001: ~20 min/day on consecutive days; a seconds-long card view is not the tested dose -- shorter app doses must be recorded as untested adaptations, not as the studied intervention)")
    if not des.get("repeat_cadence_for_fading_effect_recorded"): f.append("BPS-1 no repeat cadence is recorded for an effect with no substantial follow-up (Heekerens & Eid 2021: follow-up effects are not substantial -- a one-off exposure design ignores the known fade)")
    pro=d.get("prohibitions") or {}
    if pro.get("bps_sold_as_guarantee_or_law_of_attraction"): f.append("BPS-2 BPS is sold as a guarantee / law-of-attraction claim that imagining the future makes it arrive (sources measure affect and future expectations, not outcome delivery)")
    if pro.get("bps_forced_or_shamed_when_future_feels_unreachable"): f.append("BPS-2 the exercise is forced, or a user who cannot imagine a good future is shamed / shown failure framing (the sources are voluntary writing tasks; unreachable-future distress is a stop signal, not a conversion lever)")
    if pro.get("bps_paywalled_or_used_as_upsell_at_goal_setting"): f.append("BPS-2 the BPS writing exercise is paywalled or used as an upsell at the goal-setting moment (no source tests a paid gate on the writing step)")
    mea=d.get("measurement") or {}
    if not mea.get("positive_affect_and_future_expectations_measured_separately"): f.append("BPS-3 positive affect and positive future expectations are not measured separately (Heekerens & Eid 2021: optimism effect holds only as future expectations g=0.21, not as general orientation -- pooling hides which, if either, moved)")
    if not mea.get("followup_fade_measured"): f.append("BPS-3 no follow-up measurement is recorded (the known failure mode is fade: immediate lift with no substantial follow-up effect -- measuring only the immediate post-exercise moment overstates the intervention)")
    if not mea.get("counts_recorded_not_rates_only"): f.append("BPS-3 counts are not recorded (exercise offered, writing started, writing completed with concrete detail, skipped, repeat sessions) -- rates alone hide whether any writing ever happened")
    cit=d.get("citation") or {}
    if not cit.get("source_numbers_cited_with_design"): f.append("BPS-4 source claims are not cited with their design (King 2001 single study N=81, 20 min x 4 days; Carrillo 2019 meta 29 studies N=2,909; Heekerens & Eid 2021 meta with follow-up null)")
    if cit.get("small_immediate_effect_claimed_as_lasting_or_outcome_promise"): f.append("BPS-4 a small, mainly immediate effect is claimed as lasting change or as a promise about the user's actual future (honest claim: 'small lift in positive affect and future expectations, fading without repetition')")
    if not cit.get("revenue_chain_recorded"): f.append("BPS-4 the revenue chain is not recorded (effort-based future writing -> concrete goal clarity + positive future expectations -> next action taken -> return/renewal, each measured locally)")
    eth=d.get("ethics") or {}
    if eth.get("clinical_claim_made"): f.append("BPS-5 a clinical claim is made (treats depression/anxiety) -- Carrillo 2019 found only small effects on negative affect / depressive symptoms; this is not a treatment")
    if not eth.get("bps_available_to_free_users"): f.append("BPS-5 the BPS writing exercise is not available to free users")
    if not eth.get("review_cadence_recorded"): f.append("BPS-5 no review cadence is recorded for re-auditing BPS surfaces when they change")
    return f
def main():
    d=json.load(open(sys.argv[1])); fails=check(d)
    for x in fails: print("FAIL:",x)
    print(f"{'PASS' if not fails else 'FAIL'}: {len(fails)} fail(s) -- {d.get('app')}")
    sys.exit(0 if not fails else 1)
if __name__=="__main__": main()
