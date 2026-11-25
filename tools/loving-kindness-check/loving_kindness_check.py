#!/usr/bin/env python3
"""loving-kindness-check: deterministic gate for other-directed loving-kindness (metta) design.
Stdlib only, offline, free.
Primary sources (read via browser.search this run, 2026-11-25):
- Fredrickson et al. (2008) J Pers Soc Psychol 95(5):1045-1062 doi:10.1037/a0013262
  https://pubmed.ncbi.nlm.nih.gov/18954193/ -- field RCT, working adults n=139, half
  randomised to LKM: daily positive emotions rose over time, building resources
  (mindfulness, purpose, social support, fewer illness symptoms), which predicted
  life satisfaction up and depressive symptoms down. Dose in secondary read: 6-7 weekly
  1h classes, ~80 min/week home practice; gains took time, were not large.
- Galante et al. (2014) J Consult Clin Psychol 82(6):1101-1114 doi:10.1037/a0037249
  https://psycnet.apa.org:443/doi/10.1037/a0037249 -- 22 RCTs of kindness-based
  meditation: vs passive controls depression g=-0.61 [-1.08,-0.14], mindfulness
  g=0.63, compassion g=0.61, self-compassion g=0.45; positive emotions g=0.42 vs
  progressive relaxation. Inconclusive vs active controls; quality low-to-moderate;
  wide CIs from small studies; exposure may initially be challenging for some.
- Zeng et al. (2015) Front Psychol 6:1693 doi:10.3389/fpsyg.2015.01693
  https://pubmed.ncbi.nlm.nih.gov/26579061/ -- 24 studies, N=1,759: medium effects on
  daily positive emotions in wait-list RCTs and non-RCTs; loving-kindness-focused
  interventions medium, compassion-focused small; length/time did not influence size,
  but interventions without didactic components had small effects. Targets proceed
  easy-to-difficult: self, loved ones, neutral, difficult, all beings; phrases such
  as "may you be happy / free from suffering".
- Kreplin, Farias & Brazil (2018) Sci Rep 8:2403 doi:10.1038/s41598-018-20299-z
  https://pmc.ncbi.nlm.nih.gov:443/articles/PMC5799363/ -- RCT meta-analysis in healthy
  adults: effects on compassion and empathy, NOT on aggression, connectedness or
  prejudice; compassion rose only when teacher was a co-author and only vs passive
  (not active) controls; 61% of studies graded weak. Felt compassion is not a
  guarantee of prosocial behaviour.
Boundary: self-compassion-check owns kindness toward oneself at a lapse; sdt /
social-norms own motivation quality / norms. This gate owns only other-directed
loving-kindness: an explicit goodwill wish, sent in a graded target sequence with
a didactic component and a repeated dose, kept voluntary (never forced toward a
difficult person / harm-doer) and never sold as a behaviour guarantee.
Exit 0 = PASS, 1 = FAIL.
"""
import json, sys
def check(d):
    f=[]
    inv=d.get("inventory") or {}
    if not inv.get("lk_surfaces_inventoried"): f.append("LK-0 loving-kindness surfaces are not inventoried per app (home, notification, Dhamma / monk content, recap)")
    if not inv.get("lk_defined_as_other_directed_graded_wish"): f.append("LK-0 loving-kindness is not defined as an other-directed goodwill wish sent in a graded target sequence (self -> benefactor/loved -> neutral -> difficult -> all beings, Zeng et al. 2015), as distinct from self-compassion, generic affirmation or gratitude")
    if not inv.get("difficulty_and_backdraft_audited"): f.append("LK-0 current surfaces have not been audited for difficulty / backdraft (Galante et al. 2014: exposure may initially be challenging for some people; wishes toward a difficult person are the hardest step, not the first)")
    des=d.get("design") or {}
    if not des.get("explicit_goodwill_phrases_present"): f.append("LK-1 no explicit goodwill phrases are present (e.g. 'may you be happy / free from suffering' directed at a named target, Zeng et al. 2015 -- a self-directed affirmation is not loving-kindness)")
    if not des.get("graded_target_sequence_present"): f.append("LK-1 no graded target sequence is present (easy-to-difficult order; jumping straight to a difficult person is not the source design)")
    if not des.get("didactic_component_and_repeated_dose_designed"): f.append("LK-1 no didactic component and repeated dose are designed (Zeng et al. 2015: interventions without didactic components had small effects; Fredrickson et al. 2008 gains built over ~7 weeks of weekly classes plus home practice, not a one-off card)")
    pro=d.get("prohibitions") or {}
    if pro.get("goodwill_forced_toward_difficult_person_or_harm_doer"): f.append("LK-2 goodwill / forgiveness is forced toward a difficult person or a person who caused harm (the difficult step is optional and last in the sequence; forcing it converts the practice into compliance)")
    if pro.get("lk_used_to_bypass_or_deny_negative_feelings"): f.append("LK-2 loving-kindness is used to bypass / deny negative feelings (toxic positivity: the sources measure positive emotions alongside, not instead of, negative experience)")
    if pro.get("lk_sold_as_guaranteed_prosocial_behaviour"): f.append("LK-2 loving-kindness is sold as a guarantee of kinder behaviour (Kreplin et al. 2018: no effect on aggression, connectedness or prejudice; felt compassion is not behaviour)")
    mea=d.get("measurement") or {}
    if not mea.get("daily_positive_emotions_measured_separately"): f.append("LK-3 daily positive emotions are not measured separately from opens / streaks (the primary outcome in Fredrickson et al. 2008 and Zeng et al. 2015 is daily positive emotion, self-reported)")
    if not mea.get("resources_and_connection_measured_not_feelings_only"): f.append("LK-3 only feelings are measured -- the Fredrickson et al. 2008 chain runs through built resources (mindfulness, purpose, social support, illness symptoms) to life satisfaction; and Kreplin et al. 2018 require behaviour / connection to be read separately, not inferred from felt compassion")
    if not mea.get("counts_recorded_not_rates_only"): f.append("LK-3 counts are not recorded (wishes offered, completed by target step, skipped at difficult step, abandoned) -- rates alone hide whether the graded sequence was ever completed")
    cit=d.get("citation") or {}
    if not cit.get("source_numbers_cited_with_design"): f.append("LK-4 source claims are not cited with their design (2008 field RCT n=139 wait-list, 2014 meta of 22 RCTs vs passive controls, 2015 meta of 24 studies N=1,759, 2018 RCT meta-analysis with quality grading)")
    if cit.get("passive_control_effects_claimed_as_active_or_promise"): f.append("LK-4 passive / wait-list effects are claimed as if they held against active controls, or used as a product promise (Galante et al. 2014: inconclusive vs active controls, low-to-moderate quality, wide CIs; Kreplin et al. 2018: compassion effect only vs passive controls and only when teacher was a co-author)")
    if not cit.get("revenue_chain_recorded"): f.append("LK-4 the revenue chain is not recorded (other-directed wish -> daily positive emotions -> built resources / social support -> return as practice -> renewal, each measured locally)")
    eth=d.get("ethics") or {}
    if eth.get("clinical_claim_made"): f.append("LK-5 a clinical claim is made (treats depression / PTSD) -- Galante et al. 2014 depression g=-0.61 is vs passive controls in small, low-to-moderate quality studies and is not a treatment claim for an app")
    if not eth.get("lk_available_to_free_users"): f.append("LK-5 loving-kindness practice is not available to free users")
    if not eth.get("review_cadence_recorded"): f.append("LK-5 no review cadence is recorded for re-auditing loving-kindness surfaces when they change")
    return f
def main():
    d=json.load(open(sys.argv[1])); fails=check(d)
    for x in fails: print("FAIL:",x)
    print(f"{'PASS' if not fails else 'FAIL'}: {len(fails)} fail(s) -- {d.get('app')}")
    sys.exit(0 if not fails else 1)
if __name__=="__main__": main()
