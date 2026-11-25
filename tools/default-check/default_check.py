#!/usr/bin/env python3
"""default-check: gate for pre-selected / default choices.
Defaults are chosen disproportionately: Johnson & Goldstein (2003,
Science 302:1338-1339) online experiment n=161 - consent 42% opt-in,
82% opt-out, 79% neutral; European effective consent ~4-28% in opt-in
countries vs ~86-99.98% in opt-out countries, while actual donation
rates differed far less (~16 vs ~14 per million). Samuelson &
Zeckhauser (1988, J Risk Uncertain 1:7-59, n=486) named status quo
bias: an option is chosen most when framed as status quo, bias grows
with number of alternatives and shrinks with strong preference.
A 2022 direct replication found a smaller gap (73.5% vs 62.5%).
Distinct from anchor-check (first number), choice-overload-check
(number of options) and paywall-structure specs: this gate owns
(1) inventory of every default, (2) defaults set to the option that
is genuinely best for the typical user and disclosed as changeable,
(3) measuring default acceptance vs active choice separately, and
(4) never using a default to smuggle consent, cost or renewal.
Stdlib only, offline, free. Exit 0=PASS, 1=FAIL.
"""
import json, sys
CHECKS=[
 ("defaults_inventoried_per_surface","DF-0 no inventory of defaults exists per surface (pre-selected plan, trial on/off, notification cadence, privacy/analytics toggles, renewal, sorting), so the strongest choice lever in the product is unaudited"),
 ("default_value_recorded_with_reason","DF-0 the current value of each default is not recorded together with why it was set; an inherited or accidental default is treated as if it were a decision"),
 ("default_owner_named","DF-0 no named owner can change each default; defaults set once by a template, SDK or store page persist by inertia - the product's own status quo bias"),
 ("default_is_best_for_typical_user","DF-1 the pre-selected option is not the one genuinely best for the typical user (value per price over the expected life); a default chosen to maximise seller revenue against typical-user interest converts inertia into harm and refunds"),
 ("alternatives_equally_visible_and_changeable","DF-1 alternatives to the default are not equally visible and changeable in the same step (one tap/click, no extra screens, no confirm-shaming); a default that is hard to leave is a trap, not a default"),
 ("default_disclosed_as_preselected","DF-1 the user is not told the option was pre-selected for them and that they can change it; an undisclosed default borrows consent the user never gave"),
 ("no_default_for_consent_or_privacy","DF-2 no consent, privacy, data-sharing, marketing or tracking choice is pre-ticked / defaulted-on; Johnson & Goldstein's own case is consent - defaults there decide for people who never chose"),
 ("no_default_hiding_cost_or_renewal","DF-2 the default does not hide a cost, renewal price, trial-to-paid conversion or a later charge; acceptance of a default is not informed agreement to a bill"),
 ("default_not_dark_pattern","DF-2 the default is not combined with dark patterns (fake timer, pre-checked add-on, roach-motel cancel, win-back pressure) - cf. banned Prayer Lock patterns; a default plus friction asymmetry is manipulation"),
 ("default_acceptance_measured_separately","DF-3 passive acceptance of the default is not measured separately from active choice of the same option; pooled numbers make inertia look like preference"),
 ("switch_away_rate_and_reasons_read","DF-3 the rate and reasons of switching away from the default are not read; a high switch-away rate is evidence the default is wrong, not that users are indecisive"),
 ("defaults_read_by_cohort_and_option_count","DF-3 default effects are not read by cohort and by number of alternatives (Samuelson & Zeckhauser: bias grows with the number of alternatives and shrinks with strong preference, so one pooled rate hides where the default decides)"),
 ("primary_numbers_quoted_with_design","DF-4 the 42% vs 82% figures are quoted without their design (Johnson & Goldstein 2003, Science, online experiment n=161, hypothetical move-to-a-new-state; cross-country effective consent ~4-28% opt-in vs ~86-99.98% opt-out) - bare numbers strip their conditions"),
 ("expectations_discounted_for_replication_and_outcome_gap","DF-4 expectations are set at the 2003 headline gap without discounting: a 2022 direct replication found 73.5% vs 62.5%, and effective consent is not the downstream outcome (actual donation ~16 vs ~14 per million)"),
 ("no_app_effect_promised_from_donation_or_pension_data","DF-4 an app conversion/retention effect is promised from organ-donation or 401(k) auto-enrolment data - those show choice-share under a default, not subscription revenue"),
 ("default_reversible_without_penalty","DF-5 accepting the default is not costlessly reversible later on the same terms; a default whose consequences lock in (lost discount, changed price, started trial) punishes the passive user the default itself created"),
 ("default_reviewed_on_schedule","DF-5 defaults are not re-reviewed on a schedule against typical-user outcomes; prices, plans and user mix change, so yesterday's right default silently becomes today's wrong one"),
 ("revenue_claim_tied_to_default_chain","DF-5 any revenue claim is not tied to the source chain - default shapes choice share, which shapes paid mix, which must still prove retention/refunds - instead of asserting the default itself caused revenue the studies did not measure"),
]
def main(p):
    s=json.load(open(p)); fails=[m for k,m in CHECKS if s.get(k) is not True]
    for f in fails: print("FAIL",f)
    print(f"RESULT {'PASS' if not fails else 'FAIL'} pass={len(CHECKS)-len(fails)}/{len(CHECKS)} fails={len(fails)}")
    return 0 if not fails else 1
if __name__=="__main__":
    if len(sys.argv)!=2: print("usage: default_check.py <state.json>"); sys.exit(2)
    sys.exit(main(sys.argv[1]))
