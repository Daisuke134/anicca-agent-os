#!/usr/bin/env python3
"""social-norms-check: deterministic gate for social-norm message design.
Stdlib only, offline, free. Sources (read 2026-11-24):
- Schultz, Nolan, Cialdini, Goldstein & Griskevicius (2007) Psychol Sci 18(5):429-434
  https://pubmed.ncbi.nlm.nih.gov/17576283/ — descriptive-norm-only feedback boomerangs
  for better-than-norm households; adding an injunctive approval signal removes it.
- Cialdini (2003) Petrified Forest: descriptive sign theft 7.92% vs injunctive 1.67%.
- Nolan et al. (2008) PSPB: normative influence is underdetected in self-report,
  so effects must be judged on behaviour, not on reported motivation.
- Papakonstantinou et al. (2025) Nat Hum Behav (89 studies, n=85,759): raw d=0.10,
  disappears after publication-bias correction. Yu meta-analysis (112 RCTs):
  behaviour d=0.104, bias-adjusted d=0.039.
Boundary: social-proof-check owns proof placement/honesty on paywalls; this gate owns
norm type (descriptive vs injunctive), the boomerang, reference-group proximity,
and segment-wise measurement. Exit 0 = PASS, 1 = FAIL.
"""
import json, sys

def check(d):
    fails = []
    # SN-0 inventory and classification
    if not d.get("norm_surfaces_inventoried"):
        fails.append("SN-0 norm-using surfaces are not inventoried (notifications/home/progress/review/UGC/store)")
    if not d.get("norm_type_classified_per_surface"):
        fails.append("SN-0 norm type (descriptive vs injunctive) is not classified per surface")
    if not d.get("reference_group_named_per_surface"):
        fails.append("SN-0 the reference group (who the user is compared with) is not named per surface")
    # SN-1 boomerang guard
    if not d.get("better_than_norm_segment_identified"):
        fails.append("SN-1 the better-than-norm segment (users already above average) is not identified")
    if not d.get("descriptive_paired_with_injunctive_for_better_segment"):
        fails.append("SN-1 descriptive feedback to the better-than-norm segment is not paired with an injunctive approval signal (Schultz 2007: the pairing removes the boomerang)")
    if d.get("descriptive_only_feedback_to_better_segment"):
        fails.append("SN-1 descriptive-norm-only feedback is sent to the better-than-norm segment (boomerang risk)")
    # SN-2 truth and reference group
    if not d.get("norm_claims_true_and_sourced"):
        fails.append("SN-2 not every norm claim is backed by a real, sourced figure")
    if not d.get("reference_group_proximate_and_relevant"):
        fails.append("SN-2 the reference group is distal or irrelevant (distant averages move behaviour least)")
    if not d.get("norm_value_current_and_dated"):
        fails.append("SN-2 norm figures are not current / carry no as-of date")
    # SN-3 measurement
    if not d.get("effect_measured_by_segment"):
        fails.append("SN-3 effects are not read separately for above-norm and below-norm segments")
    if not d.get("boomerang_monitored"):
        fails.append("SN-3 worsening among the better-than-norm segment (boomerang) is not a monitored metric")
    if d.get("self_report_used_as_effect_measure"):
        fails.append("SN-3 effect is judged by self-reported motivation (Nolan 2008: normative influence is underdetected; judge on behaviour)")
    # SN-4 expectation discount
    if not d.get("effect_size_discounted_for_publication_bias"):
        fails.append("SN-4 expected effect is not discounted to the bias-adjusted range (raw d=0.10; adjusted d=0.039 to ~0 in Nat Hum Behav 2025)")
    if not d.get("injunctive_descriptive_expectations_separated"):
        fails.append("SN-4 expectations for descriptive and injunctive norms are not set separately")
    if not d.get("revenue_claim_via_behavior_chain_only"):
        fails.append("SN-4 revenue is claimed without a measured chain (norm -> behaviour change -> retention)")
    # SN-5 harm prohibitions
    if d.get("undesired_behavior_prevalence_advertised"):
        fails.append("SN-5 the prevalence of an undesired behaviour is advertised (Petrified Forest: descriptive sign 7.92% theft vs injunctive 1.67%)")
    if d.get("fabricated_majority_or_average"):
        fails.append("SN-5 a majority or average is fabricated or inflated")
    if d.get("approval_signal_as_shame_or_punishment"):
        fails.append("SN-5 the injunctive signal is delivered as shame or punishment rather than approval/disapproval information")
    return fails

def main():
    with open(sys.argv[1]) as f:
        d = json.load(f)
    fails = check(d)
    print(f"{d.get('app','?')}: fails={len(fails)}")
    for x in fails:
        print(" FAIL", x)
    print("PASS" if not fails else "FAIL")
    return 0 if not fails else 1

if __name__ == "__main__":
    sys.exit(main())
