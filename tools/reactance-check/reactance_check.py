#!/usr/bin/env python3
"""reactance-check: deterministic gate for psychological-reactance-safe message design.
Stdlib only, offline, free. Sources (read 2026-11-24):
- Brehm (1966); Brehm & Brehm (1981): reactance is the motivational state to restore
  a behavioural freedom that is threatened or eliminated.
- Dillard & Shen (2005) Commun Monogr 72(2):144-168: a composite of anger and negative
  cognitions fully mediated threat-to-freedom effects on attitude and intention (N=196, N=200).
- Rains (2013) Hum Commun Res: meta-analytic review K=20, N=4,942; the intertwined model
  (anger + counterarguments as indicators of one latent reactance factor) fit best.
- Li & Shi (2026) Hum Commun Res 52(1):38-52, meta-analyses 2005-2024, 33 studies,
  146 effect sizes: high freedom-threatening language raised anger (k=28, r=.21),
  negative cognitions (k=25, r=.17) and reactance (k=53, r=.20); anger (r=-.23) and
  negative cognitions (r=-.18) were negatively associated with persuasion; gain vs loss
  framing showed NO significant difference (r=-.03/-.01/-.02).
- Carpenter (2013) Commun Stud 64(1):6-17: BYAF meta-analysis, 42 studies; effect decays
  when the decision is not immediate. Fillon et al. (2023) pre-registered re-examination,
  52 experiments, N=19,528: g=0.44 overall but g=0.11 (CI -0.18..0.40, ns) in the 7
  low-risk-of-bias studies; reproducibility critically low.
Boundary: sdt-check owns need support/thwarting (autonomy/competence/relatedness) and
motivation quality; default-check owns pre-selected states. This gate owns the narrower
mechanism: freedom-threatening language and coercive surfaces, reactance measured as
anger + counterarguing, boomerang behaviour, and genuine (not decorative) freedom
restoration. Exit 0 = PASS, 1 = FAIL.
"""
import json, sys

def check(d):
    fails = []
    # RX-0 inventory and threat classification
    if not d.get("persuasive_surfaces_inventoried"):
        fails.append("RX-0 persuasive surfaces are not inventoried (notifications/home/paywall/onboarding/review prompts/store/UGC asks)")
    if not d.get("freedom_threat_classified_per_surface"):
        fails.append("RX-0 freedom-threat level of the language/control on each surface is not classified (controlling vs choice-preserving)")
    if not d.get("freedom_at_stake_named_per_surface"):
        fails.append("RX-0 the user freedom at stake on each surface (skip, refuse, pause, leave, choose otherwise) is not named")
    # RX-1 language and genuine choice
    if not d.get("controlling_language_removed_or_softened"):
        fails.append("RX-1 controlling / freedom-threatening language (must, have to, don't, forced imperatives) is not removed or softened (Li & Shi 2026: r=.20 reactance)")
    if not d.get("choice_preserving_language_present"):
        fails.append("RX-1 choice-preserving language is not present where a behaviour is requested")
    if not d.get("genuine_refusal_path_exists"):
        fails.append("RX-1 no genuine, penalty-free refusal path exists (a freedom statement above a blocked exit is decoration, not restoration)")
    # RX-2 coercion prohibitions
    if d.get("forced_continuation_without_exit"):
        fails.append("RX-2 a flow forces continuation without an exit (freedom eliminated, not merely threatened)")
    if d.get("fake_freedom_statement_above_coercion"):
        fails.append("RX-2 a 'you are free' style statement is paired with coercive mechanics (fake BYAF: timers, blocked close, penalty for refusal)")
    if d.get("threat_or_penalty_for_refusal"):
        fails.append("RX-2 refusal carries a threat or penalty (loss framing of punishment, guilt, streak destruction, withheld content the user already earned)")
    # RX-3 measurement
    if not d.get("reactance_measured_as_anger_plus_counterarguing"):
        fails.append("RX-3 reactance is not measured as anger + negative cognitions/counterarguing (Dillard & Shen 2005; Rains 2013 intertwined model)")
    if not d.get("boomerang_behavior_monitored"):
        fails.append("RX-3 boomerang behaviour is not monitored (doing the opposite, disabling notifications, uninstall, hostile replies/reviews)")
    if not d.get("trait_reactance_segment_considered"):
        fails.append("RX-3 high trait-reactance users are not considered as a segment (they react most strongly to directives)")
    # RX-4 expectation setting
    if not d.get("effect_sizes_cited_with_design"):
        fails.append("RX-4 reactance effect sizes are not cited with their design (Li & Shi 2026: anger r=.21, cognitions r=.17, reactance r=.20; persuasion r=-.23/-.18)")
    if not d.get("byaf_expectation_discounted_for_bias"):
        fails.append("RX-4 the BYAF expectation is not discounted to the low-risk-of-bias estimate (g=0.44 overall vs g=0.11 ns in low-risk studies, Fillon et al. 2023)")
    if d.get("framing_treated_as_reactance_fix"):
        fails.append("RX-4 gain/loss reframing is treated as a reactance fix (Li & Shi 2026: framing differences were null, r=-.03/-.01/-.02; the threat is the language, not the frame)")
    # RX-5 restoration and revenue discipline
    if not d.get("freedom_restoration_designed_after_unavoidable_threat"):
        fails.append("RX-5 where a threat is unavoidable (legal, safety, payment), no freedom-restoration step is designed after it (acknowledged choice, easy reversal)")
    if not d.get("high_pressure_copy_banned_on_distress_surfaces"):
        fails.append("RX-5 high-pressure / controlling copy is not explicitly banned on distress surfaces (the moment a suffering user is most freedom-sensitive)")
    if not d.get("revenue_claim_via_behavior_chain_only"):
        fails.append("RX-5 revenue is claimed without a measured chain (lower reactance -> behaviour -> retention -> revenue)")
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
