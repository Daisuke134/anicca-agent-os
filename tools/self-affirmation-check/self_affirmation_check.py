#!/usr/bin/env python3
"""self-affirmation-check: deterministic gate for Steele/Cohen values-affirmation design.
Stdlib only, offline, free.
Primary sources (read via browser.search this run, 2026-11-25):
- Epton et al. (2015) Health Psychol 34(3):187-196 doi:10.1037/hea0000116
  https://pubmed.ncbi.nlm.nih.gov/25133846/ -- 144 experimental tests: message
  acceptance d+=.17 [.03,.31] (34 tests, N=3,433), intentions d+=.14 [.05,.23]
  (64 tests, N=5,564), behavior d+=.32 [.19,.44] (46 tests, N=2,715). Small but
  reliable; induction = reflecting on important values/attributes/relations,
  deployed ALONGSIDE persuasive/threatening information.
- Wu, Spreckelsen & Cohen (2021) J Soc Issues, meta-analysis of values
  affirmation on academic achievement, 58 studies: threatened students g=.15,
  non-threatened g=.01 (null); heterogeneity moderate-high; works best as a
  NORMAL activity (not framed as research), with resources for improvement
  present and distal outcomes over time.
- Cohen et al. (2006) Science: ~15-min values-writing at term start closed
  ~40% of the achievement gap in that sample; recursive/persistent in follow-ups.
  Boundary condition: identity threat must be live; Schwinger 2022 (k=73) pooled
  near-zero -- effect is conditional, not universal.
Boundary: this gate owns ONLY theory-based self-affirmation (user selects own
important value unrelated to the threatened domain and writes why it matters).
It does NOT own folk daily affirmations ("I am..." repetition, Anicca's core
catalogue), self-compassion (lapse kindness), or SDT. Conflating the two is
itself a fail (SA-0).
Exit 0 = PASS, 1 = FAIL.
"""
import json, sys
def check(d):
    f=[]
    inv=d.get("inventory") or {}
    if not inv.get("sa_surfaces_inventoried"): f.append("SA-0 self-affirmation surfaces are not inventoried per app (onboarding, hard-moment notifications, feedback/failure moments, recap)")
    if not inv.get("sa_defined_as_own_values_writing_distinct_from_folk_affirmations"): f.append("SA-0 self-affirmation is not defined as the user selecting their own important value (unrelated to the threatened domain) and writing why it matters, as distinct from repeating 'I am...' catalogue affirmations (Steele 1988; Cohen & Sherman 2014)")
    if not inv.get("threat_contexts_audited"): f.append("SA-0 threat contexts have not been audited (Wu et al. 2021: effect g=.15 under identity threat, g=.01/null without it -- affirmation placed where no threat is live has no source basis)")
    des=d.get("design") or {}
    if not des.get("user_selects_own_value_from_list"): f.append("SA-1 the user does not select their own value from a values list (the canonical manipulation is self-chosen cherished values, not an app-assigned slogan)")
    if not des.get("writing_why_value_matters_present"): f.append("SA-1 no writing step about why the chosen value matters is present (~10-15 min writing in Cohen et al. 2006; reading a pre-written affirmation is not the manipulation)")
    if not des.get("placed_before_threatening_message_and_framed_as_normal_activity"): f.append("SA-1 affirmation is not placed before the threatening message/moment and framed as a normal activity (Epton et al. 2015: deployed alongside persuasive information; Wu et al. 2021: normal-activity framing moderates positively, research framing weakens it)")
    pro=d.get("prohibitions") or {}
    if pro.get("folk_affirmation_sold_as_theory_based_self_affirmation"): f.append("SA-2 folk 'I am...' repetition is sold/labelled as theory-based self-affirmation (different mechanism: self-integrity under threat, not positive self-talk)")
    if pro.get("sa_forced_or_timed_as_manipulation_disclosed"): f.append("SA-2 the exercise is forced, or framed to the user as a manipulation/research trick (coercion and research framing both break the source design)")
    if pro.get("sa_paywalled_or_used_as_upsell_at_threat_moment"): f.append("SA-2 self-affirmation is paywalled or used as an upsell at the moment of threat (the moment of defensiveness is not a sales surface; no source tests a paid gate)")
    mea=d.get("measurement") or {}
    if not mea.get("acceptance_intention_behavior_measured_separately"): f.append("SA-3 acceptance, intention and subsequent behavior are not measured separately (Epton et al. 2015 reports them as three distinct outcome points with different sizes)")
    if not mea.get("threatened_vs_nonthreatened_split_recorded"): f.append("SA-3 outcomes are not split by whether a threat context was live (Wu et al. 2021: pooling threatened and non-threatened users hides the entire effect, g=.15 vs g=.01)")
    if not mea.get("counts_recorded_not_rates_only"): f.append("SA-3 counts are not recorded (values offered, selected, writing completed, skipped, threatening message then accepted) -- rates alone hide whether the writing step ever happened")
    cit=d.get("citation") or {}
    if not cit.get("source_numbers_cited_with_design"): f.append("SA-4 source claims are not cited with their design (2015 meta of 144 tests with three outcome points; 2021 meta of 58 classroom studies split by threat; 2006 single-school field study)")
    if cit.get("conditional_effect_claimed_as_universal_or_promise"): f.append("SA-4 a conditional effect is claimed as universal or used as a product promise (non-threatened g=.01; Schwinger 2022 pooled near-zero across 73 experiments -- the honest claim is 'small, under threat, over time')")
    if not cit.get("revenue_chain_recorded"): f.append("SA-4 the revenue chain is not recorded (own-values writing before a hard moment -> lower defensiveness -> message accepted -> intended action taken -> return/renewal, each measured locally)")
    eth=d.get("ethics") or {}
    if eth.get("clinical_claim_made"): f.append("SA-5 a clinical claim is made (treats depression/anxiety) -- the sources measure defensiveness, achievement and health-behavior steps, not treatment of a disorder")
    if not eth.get("sa_available_to_free_users"): f.append("SA-5 self-affirmation exercise is not available to free users")
    if not eth.get("review_cadence_recorded"): f.append("SA-5 no review cadence is recorded for re-auditing self-affirmation surfaces when they change")
    return f
def main():
    d=json.load(open(sys.argv[1])); fails=check(d)
    for x in fails: print("FAIL:",x)
    print(f"{'PASS' if not fails else 'FAIL'}: {len(fails)} fail(s) -- {d.get('app')}")
    sys.exit(0 if not fails else 1)
if __name__=="__main__": main()
