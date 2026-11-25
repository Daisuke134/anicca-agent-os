#!/usr/bin/env python3
"""self-compassion-check: deterministic gate for self-compassion design at lapse / hard-day moments.
Stdlib only, offline, free.
Primary sources (read via browser.search this run, 2026-11-25):
- Neff & Germer (2013) J Clin Psychol 69(1):28-44 -- MSC 8-week program:
  pilot N=21 + waitlist RCT (treatment N=25 vs waitlist N=27); significantly
  larger increases in self-compassion, mindfulness and wellbeing vs control;
  gains maintained at 6-month and 1-year follow-up. Small, mostly female,
  waitlist (not active) control -- effect sizes are not product promises.
  http://self-compassion.org/wp-content/uploads/2014/10/Neff-Germer-MSC-RCT-2012.pdf
- Ferrari et al. (2019) Mindfulness 10:1455-1473, doi:10.1007/s12671-019-01134-6
  -- meta-analysis of 27 RCTs: moderate effects on self-compassion (g=0.75),
  stress (0.67), depression (0.66), self-criticism (0.56), anxiety (0.57);
  large on rumination (1.37). Intervention types too diverse to isolate a
  category; publication bias may be present (authors' own caveats).
Neff's construct = 3 components: self-kindness (vs self-judgment), common
humanity (vs isolation), mindfulness (vs over-identification).
Boundary: sdt-check owns the 3 basic needs; streak-check owns streak
mechanics; winback-check owns lapsed-subscriber offers. This gate owns only
the language and sequencing at the moment of failure/lapse: is the user met
with the 3 components, in full, before any re-engagement or payment ask --
and is post-lapse return measured.
Exit 0 = PASS, 1 = FAIL.
"""
import json, sys
def check(d):
    f=[]
    inv=d.get("inventory") or {}
    if not inv.get("lapse_surfaces_inventoried"): f.append("SC-0 lapse / hard-day surfaces are not inventoried per app (missed day, broken streak, cancelled, bad-day open)")
    if not inv.get("three_components_defined"): f.append("SC-0 self-compassion is not defined by Neff's 3 components (self-kindness, common humanity, mindfulness) in the surface spec")
    if not inv.get("current_copy_audited_for_self_judgment"): f.append("SC-0 current lapse copy has not been audited for self-judgment language")
    des=d.get("design") or {}
    if not des.get("compassion_break_before_reengagement_ask"): f.append("SC-1 no self-compassion break (kindness + common humanity + mindful naming) is delivered before any re-engagement ask at lapse")
    if not des.get("return_path_no_penalty"): f.append("SC-1 the return path penalises the lapse (progress reset, lost content, restart cost) instead of a one-step penalty-free return")
    if not des.get("compassion_precedes_paywall_at_lapse"): f.append("SC-1 at lapse, a paywall / streak-repair offer precedes the compassion copy (kindness is sequenced after the payment ask)")
    pro=d.get("prohibitions") or {}
    if pro.get("shame_or_guilt_copy"): f.append("SC-2 shame/guilt copy is present at lapse ('you broke it', 'don't fail again') -- the opposite pole of self-kindness")
    if pro.get("toxic_positivity_denies_suffering"): f.append("SC-2 copy denies the suffering ('just stay positive') instead of mindful acknowledgement -- over-identification's mirror image")
    if pro.get("compassion_withheld_behind_paywall"): f.append("SC-2 the compassionate response itself is withheld behind the paywall at the moment of lapse")
    mea=d.get("measurement") or {}
    if not mea.get("lapse_return_measured_separately"): f.append("SC-3 lapse -> return is not measured separately from ordinary next-day retention")
    if not mea.get("post_lapse_churn_measured"): f.append("SC-3 post-lapse churn / non-return is not measured (the lapse is where the churn decision happens)")
    if not mea.get("counts_recorded_not_rates_only"): f.append("SC-3 counts are not recorded (lapses, compassionate returns, abandonments) -- rates alone hide volume")
    cit=d.get("citation") or {}
    if not cit.get("source_numbers_cited_with_design"): f.append("SC-4 source claims are not cited with their design (2013 small waitlist RCT vs 2019 meta-analysis of 27 RCTs, publication-bias caveat)")
    if cit.get("program_effect_used_as_product_promise"): f.append("SC-4 an 8-week group-program effect is used as a product / retention / revenue promise")
    if not cit.get("revenue_chain_recorded"): f.append("SC-4 the revenue chain is not recorded (lapse -> compassionate return -> retained -> renewal, each measured locally)")
    eth=d.get("ethics") or {}
    if eth.get("clinical_claim_made"): f.append("SC-5 a clinical claim is made (treats depression/anxiety) -- the product is a wellbeing surface, not therapy")
    if not eth.get("compassion_available_to_free_users"): f.append("SC-5 the lapse compassion response is not available to free users (care gated by payment status)")
    if not eth.get("review_cadence_recorded"): f.append("SC-5 no review cadence is recorded for re-auditing lapse copy when surfaces change")
    return f
def main():
    d=json.load(open(sys.argv[1])); fails=check(d)
    for x in fails: print("FAIL:",x)
    print(f"{'PASS' if not fails else 'FAIL'}: {len(fails)} fail(s) -- {d.get('app')}")
    sys.exit(0 if not fails else 1)
if __name__=="__main__": main()
