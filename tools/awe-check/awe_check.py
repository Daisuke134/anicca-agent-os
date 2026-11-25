#!/usr/bin/env python3
"""awe-check: deterministic gate for awe design (Anicca living home / Dhamma / Thankful).
Stdlib only, offline, free.
Primary sources (read via browser.search/open this run, 2026-11-25):
- Piff, Dietze, Feinberg, Stancato & Keltner (2015) J Pers Soc Psychol 108(6):883-899
  doi:10.1037/pspi0000018 -- 5 studies, N=2,078: awe = response to perceptually vast
  stimuli transcending current frames; inductions increased ethical decision-making,
  generosity, prosocial values and helping, decreased entitlement; effects mediated
  in part by a "small self". https://pubmed.ncbi.nlm.nih.gov/25984788/
- Sturm et al. (2022) Emotion 22(5):1044-1058 doi:10.1037/emo0000876 -- RCT, 60 older
  adults (52 in UCSF summary), weekly 15-min walks x 8 weeks: awe-walk group showed
  greater awe, increasingly small self in selfies, greater joy/prosocial positive
  emotions during walks, greater daily prosocial emotions and decreased daily distress
  outside walks; post anxiety/depression/life satisfaction did NOT change.
- Monroy et al. (2023) Scientific Reports -- daily diary, 22 days, Sample1 N=269
  community adults, Sample2 N=145 healthcare workers during COVID-19: on days with
  more awe than usual, lower stress, fewer somatic symptoms, greater well-being.
  This is a within-person association, NOT proof awe caused the change.
  https://www.nature.com/articles/s41598-023-35200-w
- Li, Hou, Zhang, Xu & Nie (2024) Current Psychology 43:24702-24711
  doi:10.1007/s12144-024-06039-9 -- meta-analysis of awe-prosocial relationship;
  secondary summaries report ~38 articles / 57 effect sizes / ~21k people and a
  moderate association, moderated by age/culture -- treat pooled size as secondary.
Boundary: savoring-check owns prolonging a positive moment; gratitude-check owns
thanks for benefits received. This gate owns only awe: is there a genuine vastness
elicitor that shifts attention outward (small self), dosed as a repeatable practice,
kept free of self-centring and money cues that would collapse it.
Exit 0 = PASS, 1 = FAIL.
"""
import json, sys
def check(d):
    f=[]
    inv=d.get("inventory") or {}
    if not inv.get("awe_surfaces_inventoried"): f.append("AW-0 awe surfaces are not inventoried per app (living home, notification landing, walk / outdoor prompt, recap)")
    if not inv.get("awe_defined_as_vastness_plus_accommodation"): f.append("AW-0 awe is not defined as a response to perceptually vast stimuli that transcend current frames of reference (Piff et al. 2015), as distinct from generic calm / beauty / affirmation")
    if not inv.get("elicitors_and_self_focus_audited"): f.append("AW-0 current surfaces have not been audited for actual awe elicitors (nature, art, music, collective, moral beauty) and for self-centring elements that block a small-self shift")
    des=d.get("design") or {}
    if not des.get("genuine_vastness_elicitor_present"): f.append("AW-1 no genuine vastness elicitor is present (a short text card alone, with no vast referent, is not an awe elicitor in the source designs)")
    if not des.get("repeated_practice_dose_designed"): f.append("AW-1 awe is not designed as a repeated practice with a dose (the walk evidence is weekly 15-min x 8 weeks, Sturm et al. 2022; a one-off exposure is not that design)")
    if not des.get("attention_directed_outward_small_self"): f.append("AW-1 attention is not directed outward toward the vast referent (the mechanism in Piff et al. 2015 is a diminished self-focus / small self, not self-improvement pressure)")
    pro=d.get("prohibitions") or {}
    if pro.get("paywall_or_price_shown_adjacent_to_awe_moment"): f.append("AW-2 a paywall / price is shown adjacent to the awe moment (a money cue re-centres the self the awe design is trying to de-centre)")
    if pro.get("awe_faked_with_false_vastness_or_fear"): f.append("AW-2 awe is faked with false vastness claims or manufactured by fear / threat (threat-based awe is a different, mixed emotion and is not the prosocial design in the sources)")
    if pro.get("awe_moment_framed_selfie_first_or_self_centred"): f.append("AW-2 the awe moment is framed selfie-first / self-centred (in Sturm et al. 2022 the marker of change was the self getting SMALLER in the frame, not larger)")
    mea=d.get("measurement") or {}
    if not mea.get("awe_experience_measured_separately"): f.append("AW-3 experienced awe is not measured separately from generic opens / views / calm ratings")
    if not mea.get("prosocial_and_distress_outcomes_measured_not_opens_only"): f.append("AW-3 only opens / views are measured -- the source outcomes were prosocial positive emotions (compassion, gratitude, joy) and daily distress (Sturm et al. 2022), not exposure counts")
    if not mea.get("counts_recorded_not_rates_only"): f.append("AW-3 counts are not recorded (awe moments offered, experienced, repeated as practice, abandoned) -- rates alone hide whether awe happened at all")
    cit=d.get("citation") or {}
    if not cit.get("source_numbers_cited_with_design"): f.append("AW-4 source claims are not cited with their design (2015 five-study experiments, 2022 walk RCT, 2023 daily-diary association, 2024 meta-analysis)")
    if cit.get("diary_association_claimed_as_causal_or_meta_used_as_promise"): f.append("AW-4 a diary association (Monroy et al. 2023) is claimed as causal, or a meta-analytic association is used as a product promise (Sturm et al. 2022 found no change in anxiety, depression or life satisfaction)")
    if not cit.get("revenue_chain_recorded"): f.append("AW-4 the revenue chain is not recorded (awe moment -> small self / prosocial affect -> return as practice -> renewal, each measured locally)")
    eth=d.get("ethics") or {}
    if eth.get("clinical_claim_made"): f.append("AW-5 a clinical claim is made (treats anxiety / depression) -- Sturm et al. 2022 found no post-intervention change in anxiety, depression or life satisfaction")
    if not eth.get("awe_available_to_free_users"): f.append("AW-5 awe experiences are not available to free users")
    if not eth.get("review_cadence_recorded"): f.append("AW-5 no review cadence is recorded for re-auditing awe surfaces when they change")
    return f
def main():
    d=json.load(open(sys.argv[1])); fails=check(d)
    for x in fails: print("FAIL:",x)
    print(f"{'PASS' if not fails else 'FAIL'}: {len(fails)} fail(s) -- {d.get('app')}")
    sys.exit(0 if not fails else 1)
if __name__=="__main__": main()
