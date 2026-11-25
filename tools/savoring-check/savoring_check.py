#!/usr/bin/env python3
"""savoring-check: deterministic gate for savoring design (Anicca living home / Thankful).
Stdlib only, offline, free.
Primary sources (read via browser.search this run, 2026-11-25):
- Bryant, F. B. (2003) Savoring Beliefs Inventory, J Mental Health 12(2):175-196 --
  6 validation studies; savoring = deriving pleasure through three temporal forms:
  anticipating upcoming positive events, savoring present moments, reminiscing
  about past positive experiences; SBI correlates positively with happiness
  intensity/frequency and life satisfaction, negatively with depression/hopelessness.
  https://psycnet.apa.org/record/2003-03639-008
- Jose, Lim & Bryant (2012) J Positive Psychology 7(3):176-187 -- daily diary,
  101 participants x 30 days: momentary savoring both mediated and moderated
  the impact of daily positive events on momentary happy mood.
- Quoidbach, Dunn, Petrides & Mikolajczak (2010) Psychol Sci 21(6):759-763 --
  wealthier adults reported lower savoring ability; a mere reminder of wealth
  produced the same dampening experimentally; money-primed participants spent
  less time savoring chocolate (32s vs 45s) and enjoyed it less.
  https://pubmed.ncbi.nlm.nih.gov/20483819/
- Savoring interventions meta-analysis (2026) Applied Psychol Health Well-Being
  18(2):e70134 -- 20 RCTs, N=4,805, overall g=0.51, positive states g=0.50;
  BUT Cullen et al. (2024) clinical-population review found efficacy vs active /
  no-intervention controls relatively weak and study quality low -- discount.
Boundary: gratitude-check owns gratitude for benefits received; peak-end-check
owns retrospective peak/end of an episode. This gate owns only savoring: is a
positive moment actually given time and attention to be prolonged (present),
anticipated, and revisited -- and is it kept free of money cues that dampen it.
Exit 0 = PASS, 1 = FAIL.
"""
import json, sys
def check(d):
    f=[]
    inv=d.get("inventory") or {}
    if not inv.get("positive_moment_surfaces_inventoried"): f.append("SV-0 positive-moment surfaces are not inventoried per app (living home, notification landing, recap, celebration)")
    if not inv.get("savoring_defined_as_prolonging_positive_experience"): f.append("SV-0 savoring is not defined as generating / intensifying / prolonging a positive experience (Bryant & Veroff), as distinct from merely delivering content")
    if not inv.get("dampeners_audited"): f.append("SV-0 current surfaces have not been audited for savoring dampeners (money / price cues, instant auto-advance, next-item pressure)")
    des=d.get("design") or {}
    if not des.get("dwell_time_allows_savoring"): f.append("SV-1 the positive moment is not given dwell time to be savored (it is replaced before attention can prolong it -- cf. money-primed savoring time 32s vs 45s, Quoidbach 2010)")
    if not des.get("three_temporal_modes_supported"): f.append("SV-1 not all three temporal modes are supported (anticipation of a coming good moment, present-moment savoring, reminiscence / revisit of a past one -- Bryant 2003)")
    if not des.get("user_can_pause_or_revisit_moment"): f.append("SV-1 the user cannot pause, hold, or revisit a positive moment (no control over its duration means no savoring by design)")
    pro=d.get("prohibitions") or {}
    if pro.get("paywall_or_price_shown_adjacent_to_positive_moment"): f.append("SV-2 a paywall / price is shown adjacent to the positive moment (money reminders measurably dampen savoring -- Quoidbach et al. 2010)")
    if pro.get("moment_rushed_by_auto_advance_or_next_item_pressure"): f.append("SV-2 the moment is rushed by auto-advance / next-item pressure (prolonging is the mechanism; rushing removes it)")
    if pro.get("savoring_moment_used_as_upsell_teaser"): f.append("SV-2 the positive moment is truncated as an upsell teaser (the good moment itself is withheld to sell)")
    mea=d.get("measurement") or {}
    if not mea.get("savoring_behavior_measured_separately"): f.append("SV-3 savoring behavior (dwell on / revisit of positive moments) is not measured separately from generic opens / views")
    if not mea.get("positive_affect_outcome_measured_not_opens_only"): f.append("SV-3 only opens / views are measured -- the source outcomes were momentary happy mood and positive affect (Jose et al. 2012), not exposure counts")
    if not mea.get("counts_recorded_not_rates_only"): f.append("SV-3 counts are not recorded (moments shown, dwelled on, revisited, rushed past) -- rates alone hide whether savoring happened at all")
    cit=d.get("citation") or {}
    if not cit.get("source_numbers_cited_with_design"): f.append("SV-4 source claims are not cited with their design (2003 scale validation, 2012 diary study, 2010 money-prime experiments, 2026 RCT meta-analysis)")
    if cit.get("meta_effect_used_as_product_promise"): f.append("SV-4 a meta-analytic effect (g=0.51) is used as a product promise (the 2024 clinical review found efficacy vs active controls relatively weak and study quality low)")
    if not cit.get("revenue_chain_recorded"): f.append("SV-4 the revenue chain is not recorded (savored moment -> positive affect -> return -> renewal, each measured locally)")
    eth=d.get("ethics") or {}
    if eth.get("clinical_claim_made"): f.append("SV-5 a clinical claim is made (treats depression / anxiety) -- symptom effects are uncertain against active controls")
    if not eth.get("savoring_available_to_free_users"): f.append("SV-5 savoring of positive moments is not available to free users")
    if not eth.get("review_cadence_recorded"): f.append("SV-5 no review cadence is recorded for re-auditing positive-moment surfaces when they change")
    return f
def main():
    d=json.load(open(sys.argv[1])); fails=check(d)
    for x in fails: print("FAIL:",x)
    print(f"{'PASS' if not fails else 'FAIL'}: {len(fails)} fail(s) -- {d.get('app')}")
    sys.exit(0 if not fails else 1)
if __name__=="__main__": main()
