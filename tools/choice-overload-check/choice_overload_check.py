#!/usr/bin/env python3
"""choice-overload-check: gate for sizing and structuring choice sets.
Choice overload is CONDITIONAL, not a law. Iyengar & Lepper (2000,
JPSP) jam field study: 24 varieties attracted more stoppers (60% vs
40%) but converted far worse among tasters (~30% purchase from 6
varieties vs ~3% from 24; N=249 analyzed). Scheibehenne, Greifeneder
& Todd (2010, JCR) meta-analysis of 50 experiments (63 conditions,
N=5,036) found a mean effect of virtually zero with large variance.
Chernev, Bockenholt & Goodman (2015, JCP) meta-analysis of 99
observations (N=7,202) found overload becomes reliable when four
moderators are high: choice set complexity, decision task difficulty,
preference uncertainty, and an effort-minimizing decision goal.
Distinct from paywall-decision-check (plan-count decision record) and
tool-choice-check (LLM tool_choice): this gate owns (1) inventorying
every user-facing choice surface with its option count, (2) assessing
the four moderators per surface, (3) a curated default path with the
full set reachable on demand, and (4) measuring deferral/regret, not
just conversion. Stdlib only, offline, free. Exit 0=PASS, 1=FAIL.
"""
import json, sys
CHECKS=[
 ("choice_surfaces_recorded_per_app","CO-0 no user-facing choice surface (paywall plans, onboarding questions, catalogue/theme pickers, settings) is recorded per app, so assortment size cannot be audited"),
 ("option_counts_recorded_per_surface","CO-0 the number of options actually presented at each surface is not recorded; 'we offer a lot of choice' is not a count"),
 ("moderators_assessed_per_surface","CO-0 the four Chernev et al. (2015) moderators (set complexity, task difficulty, preference uncertainty, effort-minimizing goal) are not assessed per surface; overload is conditional, so an unassessed surface cannot be judged by assortment size alone"),
 ("curated_default_path_exists","CO-1 there is no curated default path (the product/model chooses first, the user can override); presenting the raw full set as the first step dumps the decision cost on the least-informed moment"),
 ("full_set_available_on_demand","CO-1 curation removes access: the full set is not reachable on demand from the default path, so 'curated' quietly becomes 'hidden' and users who know what they want cannot get it"),
 ("default_is_genuine_best_not_manipulated","CO-1 the default/preselected option is chosen for margin or sponsorship rather than as the genuinely best fit for this user; a manipulated default is a dark pattern, not curation"),
 ("options_categorized_or_chunked","CO-2 a large set that must be shown is presented flat instead of categorized/chunked; set complexity is a moderator, and flat presentation maximizes it"),
 ("options_comparable_on_shared_attributes","CO-2 options are not comparable on shared, alignable attributes, so each option must be evaluated from scratch (complexity moderator left at maximum)"),
 ("deferral_measured_not_just_conversion","CO-2 choice deferral / no-choice / abandonment at the surface is not measured; overload shows up first as choosing nothing, which a conversion-only read mislabels as 'not interested'"),
 ("paywall_plans_kept_small_with_preselected_default","CO-3 the paywall does not keep plans small (about 3) with one genuinely-best plan preselected; plan choice is a high-uncertainty, effort-minimizing decision - the exact moderator profile where overload fires"),
 ("onboarding_questions_sequenced_one_choice_at_a_time","CO-3 onboarding presents parallel option grids / many simultaneous decisions instead of one question per screen in sequence; sequencing converts one hard choice into several easy ones"),
 ("satisfaction_and_regret_measured_after_choice","CO-3 post-choice satisfaction / confidence / regret / switching is not measured; Chernev et al. (2015) found these are interchangeable overload measures, and a choice that converts but is regretted churns later"),
 ("jam_numbers_quoted_with_design","CO-4 the jam numbers are quoted without their design (Iyengar & Lepper 2000: 24 vs 6 varieties, ~30% vs ~3% purchase among tasters, N=249, and the large set attracted MORE stoppers 60% vs 40%) - bare '10x' strips both conditions and the attraction half of the result"),
 ("expectations_set_conditional_not_law","CO-4 'fewer options always convert better' is treated as a law; Scheibehenne et al. (2010) found a mean effect of virtually zero across 50 experiments, so expected gains must be conditioned on the four moderators, not assumed"),
 ("no_app_effect_promised_from_jam_study","CO-4 an app conversion effect is promised from the jam study or either meta-analysis; the evidence licenses a conditional design audit, not a promised lift"),
 ("curation_not_used_to_hide_price_or_terms","CO-5 curation/preselection is used to hide a price, a renewal term, or a cheaper fitting option (curating away the option the user would have chosen is steering, cf. banned dark patterns)"),
 ("reduction_not_used_to_remove_meaningful_choice","CO-5 assortment is cut where users genuinely differentiate (language, accessibility, real preference differences); removing meaningful choice to simplify metrics harms the users the variety existed for - the large set's attraction effect is real"),
 ("revenue_claim_tied_to_source_chain","CO-5 any revenue claim is not tied to the source chain - high moderators -> deferral/regret -> lost or reversed conversion - instead of asserting that cutting options directly creates revenue"),
]
def main(p):
    s=json.load(open(p)); fails=[m for k,m in CHECKS if s.get(k) is not True]
    for f in fails: print("FAIL",f)
    print(f"RESULT {'PASS' if not fails else 'FAIL'} pass={len(CHECKS)-len(fails)}/{len(CHECKS)} fails={len(fails)}")
    return 0 if not fails else 1
if __name__=="__main__":
    if len(sys.argv)!=2: print("usage: choice_overload_check.py <state.json>"); sys.exit(2)
    sys.exit(main(sys.argv[1]))
