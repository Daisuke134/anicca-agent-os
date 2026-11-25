#!/usr/bin/env python3
"""gratitude-check: deterministic gate for gratitude-practice design (Thankful / Anicca).
Stdlib only, offline, free.
Primary sources (read via browser.search this run, 2026-11-25):
- Emmons & McCullough (2003) J Pers Soc Psychol 84(2):377-389 -- Study 1 weekly
  listing of 5 blessings vs hassles / neutral events; Study 2 daily listing;
  Study 3 adults with neuromuscular disease, 21 days. Gratitude groups showed
  heightened wellbeing on several (not all) outcomes; positive affect was the
  most robust finding. Small student / patient samples, self-report.
  https://greatergood.berkeley.edu/pdfs/GratitudePDFs/6Emmons-BlessingsBurdens.pdf?af_js_web=true&
- Davis et al. (2016) J Couns Psychol 63(1):20-31 -- meta-analysis: gratitude
  interventions beat measurement-only controls on wellbeing (d=.31) and
  activity-matched comparisons only slightly (d=.14); vs a psychologically
  active comparison the advantage was d=.03 (ns). Control type decides size.
  https://scottbarrykaufman.com/wp-content/uploads/2021/05/davis2016.pdf
- Cregg & Cheavens (2020) J Happiness Stud -- meta-analysis of 27 studies
  (N=3,675): depression/anxiety g=-0.29 post, -0.23 follow-up, but active
  controls g=-0.20 vs waitlist g=-0.55: waitlist comparisons inflate.
Boundary: self-compassion-check owns lapse language; endowed-progress /
goal-gradient own progress framing. This gate owns only the gratitude
practice itself: is it specific (a concrete benefit / benefactor, not generic
positivity), unforced on hard days, un-paywalled, and measured by outcome
rather than entry count -- with effect claims discounted by control type.
Exit 0 = PASS, 1 = FAIL.
"""
import json, sys
def check(d):
    f=[]
    inv=d.get("inventory") or {}
    if not inv.get("gratitude_surfaces_inventoried"): f.append("GR-0 gratitude surfaces are not inventoried per app (journal prompt, home card, notification, recap)")
    if not inv.get("practice_defined_as_specific_benefit"): f.append("GR-0 the practice is not defined as naming a specific benefit / benefactor (Emmons listing), not generic positivity")
    if not inv.get("current_prompts_audited_for_forced_gratitude"): f.append("GR-0 current gratitude prompts have not been audited for forced / obligatory framing")
    des=d.get("design") or {}
    if not des.get("entries_require_concrete_specificity"): f.append("GR-1 entries do not require concrete specificity (what happened, who / what caused it) -- vague lists are not the tested practice")
    if not des.get("cadence_bounded_and_skippable"): f.append("GR-1 cadence is not bounded and skippable (tested forms were weekly x5 or short daily runs; an endless daily obligation is untested and coercive)")
    if not des.get("optional_expression_path_exists"): f.append("GR-1 no optional expression path exists (letter / share to the benefactor) -- the interpersonal form in the source literature")
    pro=d.get("prohibitions") or {}
    if pro.get("forced_gratitude_on_hard_days"): f.append("GR-2 gratitude is forced on hard days (prompt demands thanks while the user is suffering, with no skip)")
    if pro.get("gratitude_used_to_deny_suffering"): f.append("GR-2 gratitude copy denies suffering ('others have it worse', 'just be grateful') -- social-comparison / dismissal framing")
    if pro.get("gratitude_practice_paywalled"): f.append("GR-2 the gratitude practice itself is withheld behind the paywall")
    mea=d.get("measurement") or {}
    if not mea.get("practice_completion_measured_separately"): f.append("GR-3 gratitude-practice completion is not measured separately from generic journaling / opens")
    if not mea.get("wellbeing_outcome_measured_not_entries_only"): f.append("GR-3 only entry counts are measured -- the source outcomes were affect / wellbeing, not volume of entries")
    if not mea.get("counts_recorded_not_rates_only"): f.append("GR-3 counts are not recorded (prompts, completions, skips, hard-day skips) -- rates alone hide volume and coercion")
    cit=d.get("citation") or {}
    if not cit.get("source_numbers_cited_with_design"): f.append("GR-4 source claims are not cited with their design (2003 small experiments vs 2016 / 2020 meta-analyses, control type stated)")
    if cit.get("waitlist_effect_used_as_product_promise"): f.append("GR-4 a waitlist-comparison effect is used as a product promise (vs psychologically active controls the advantage was d=.03, ns -- Davis 2016)")
    if not cit.get("revenue_chain_recorded"): f.append("GR-4 the revenue chain is not recorded (specific practice -> affect -> return -> renewal, each measured locally)")
    eth=d.get("ethics") or {}
    if eth.get("clinical_claim_made"): f.append("GR-5 a clinical claim is made (treats depression / anxiety) -- meta-analytic symptom effects are small and low-certainty")
    if not eth.get("gratitude_available_to_free_users"): f.append("GR-5 the gratitude practice is not available to free users")
    if not eth.get("review_cadence_recorded"): f.append("GR-5 no review cadence is recorded for re-auditing gratitude prompts when surfaces change")
    return f
def main():
    d=json.load(open(sys.argv[1])); fails=check(d)
    for x in fails: print("FAIL:",x)
    print(f"{'PASS' if not fails else 'FAIL'}: {len(fails)} fail(s) -- {d.get('app')}")
    sys.exit(0 if not fails else 1)
if __name__=="__main__": main()
