#!/usr/bin/env python3
"""install-paid-check: deterministic gate for EXPERIMENT DECISION RULES
on onboarding/paywall changes -- is every change judged on
install-to-paid (not trial starts), was a real value moment offered
before the paywall and measured, and are dismissal offers, reminders
and length changes decided on trial quality + refunds with a hold?
Stdlib only, offline, free. Exit 0=PASS, 1=FAIL.

Source (read in full 2026-11-24):
- Kiko (Emma Park), "How a seed-stage home workout app got
  trial-to-paid from 34% to 47%" (published 2026-11-06, updated
  2026-11-13) https://www.kikogrowth.com/case-studies/fitness-app-paywall/
  Client anonymised under NDA; figures are the agency's own report.
  90-day sprint, 7-day trial, $59.99/yr or $12.99/mo. Method: "We
  judged every change on install-to-paid, not on trial starts, because
  a paywall that asks later will always start fewer trials." Baseline
  first: subscription events fixed against store records, 8 prior
  weeks pulled; only 48% of trial users did a single workout in-trial.
  Sequence: 6-screen quiz (from 14) -> one real 7-minute workout
  BEFORE the paywall -> plan paywall (user's own 4-week plan, trial
  timeline today/day-5 reminder/day-7 charge, annual as $1.15/week)
  -> trial reminder 2 days before first charge -> weeks 8-12 HOLD
  with no new changes; weekly trial cohorts read at first charge and
  14 days after it for refunds; sprint review in week 13.
  Results: trial-to-paid 34% -> 47% (3,713/7,900 vs 3,944/11,600),
  install-to-trial 21% -> 19% (accepted), install-to-paid 7.1% ->
  8.9%, in-trial workout completion 48% -> 79%, refund requests
  within 14 days of first charge 6.0% -> 2.8%, annual share 58% ->
  66%. Dropped: a 40%-off dismissal offer (lifted trial starts, only
  29% of those trials converted, refunds rose) and an AI coach chat
  in onboarding (longer, no conversion effect). Reminder kept: cost
  ~1pt of conversion, roughly halved refunds. Every paywall claim
  came from a counsel-signed approved claims list.
- Auxiliary (read in full 2026-11-23 in an earlier run of this loop):
  RevenueCat Everlove experiment -- cutting 28 steps to 19 raised
  completion 78.1% -> 86.7% and paywall reach 74.3% -> 83.9%, but
  trial starts per paywall view fell 3.83% -> 3.13% (-18%) and net
  conversion was flat (3.35% vs 3.11%, n.s., 24,000 users). Length
  changes must be read on BOTH halves before a decision.

Separation: funnel-definition-check owns event definitions and read
rules; trial-check owns reminder sequence content and delivery;
paywall-personalization-second-offer-spec owns the second offer's
depth cap and 6-month revenue read; message-match-check owns
answer-to-headline/plan correspondence. This gate owns only the
decision layer: which metric decides, whether value preceded the
ask, and whether quality/refunds/hold discipline governed the call.
"""
import json, sys

CHECKS = [
    ("baseline_reconciled_with_store_records", "IP-0 no reconciled baseline (subscription events fixed against the store records and a pre-period pulled BEFORE changes; Kiko spent weeks 1-2 on this -- an unreconciled baseline makes every later lift a guess)"),
    ("owner_named", "IP-0 no named owner for install-to-paid decisions (the metric nobody owns is the metric nobody reads)"),
    ("primary_metric_is_install_to_paid", "IP-0 changes are not judged primarily on install-to-paid (judging on trial starts punishes any change that asks later: 'a paywall that asks later will always start fewer trials' -- Kiko)"),
    ("value_moment_defined", "IP-1 no single real first-use value moment is defined (Kiko: one 7-minute workout; Anicca's equivalent is the first personalised intervention actually experienced, not a screen describing it)"),
    ("value_completion_in_trial_measured", "IP-1 the share of trial users who complete the value moment during the trial is not measured (Kiko's baseline was 48% and it rose to 79% -- this number, not trial starts, showed the rebuild worked)"),
    ("value_before_paywall_tested_or_decided", "IP-1 value-before-paywall has never been tested nor explicitly decided against with a recorded reason (Kiko: trial starts dipped and conversion climbed; an untested sequencing assumption is an original invention)"),
    ("decision_rules_written_before_test", "IP-2 ship/kill rules are not written before the test runs (Kiko wrote each rule in advance, e.g. 'ship if completion +5pp with install-to-paid flat or up' -- rules written after results arrive are rationalisations)"),
    ("trial_start_fall_alone_not_a_kill", "IP-2 a fall in trial starts alone can kill a change (Kiko accepted install-to-trial 21% -> 19% because install-to-paid rose 7.1% -> 8.9%; killing on starts alone reinstates the earliest possible ask)"),
    ("dismissal_offer_judged_on_quality_and_refunds", "IP-2 a paywall-dismissal offer is judged on trial-start lift alone (Kiko's 40%-off offer lifted starts but only 29% of those trials converted and refunds rose, so it was dropped -- start lift with worse trials is a loss)"),
    ("both_halves_measured_for_length_changes", "IP-3 onboarding length changes are decided without reading both halves (completion/paywall reach AND trial starts per paywall view; Everlove: +8.6pp completion, -18% per-view starts, net flat -- reading one half picks a philosophy, not a winner)"),
    ("extra_onboarding_features_cut_if_no_effect", "IP-3 extra onboarding features with no measured conversion effect are kept (Kiko cut its AI coach chat: it made onboarding longer and changed nothing -- length that earns nothing is friction with a roadmap)"),
    ("changes_sequenced_then_held", "IP-3 changes are not sequenced one at a time and then held with no new changes (Kiko: one change per week, weeks 8-12 held -- stacked changes with no hold cannot be attributed, and a funnel that never holds never gets a clean read)"),
    ("cohorts_read_at_first_charge_and_14d", "IP-4 weekly trial cohorts are not read at first charge and again 14 days after it (refunds arrive after the charge; a read taken at trial start or at charge day alone misses the refund half of the result)"),
    ("refunds_part_of_ship_decisions", "IP-4 refunds are not part of ship decisions (Kiko's plan-paywall rule was 'same rule, with refunds flat or down'; a change that converts worse-quality trials shows up first as refunds 6.0% -> 2.8% in reverse)"),
    ("reminder_decision_on_refunds_vs_conversion", "IP-4 the trial reminder's keep/drop decision is not made on refunds vs conversion cost (Kiko kept it: ~1pt of conversion cost, refunds roughly halved; trial-check owns the sequence content -- this gate owns only this decision rule)"),
    ("paywall_claims_from_approved_list", "IP-5 paywall claims do not come from an approved claims list (Kiko: every claim from the client's counsel-signed list; an unlisted claim on the paywall is an unverified claim at the moment of payment)"),
    ("hold_period_review_done", "IP-5 no review is held after the hold period (Kiko's sprint review was week 13, after the hold and after refunds through the read window -- deciding during the hold is deciding on partial cohorts)"),
    ("decision_recorded_per_app", "IP-5 no per-app decision is recorded (whether the value-first test runs, is deferred, or is rejected -- per app; an unrecorded decision is revisited from zero every quarter)"),
]
def main(path):
    s = json.load(open(path))
    fails = [msg for key, msg in CHECKS if s.get(key) is not True]
    for f in fails: print("FAIL", f)
    print(f"RESULT {'PASS' if not fails else 'FAIL'} pass={len(CHECKS)-len(fails)}/{len(CHECKS)} fails={len(fails)}")
    return 0 if not fails else 1
if __name__ == "__main__":
    if len(sys.argv) != 2: print("usage: install_paid_check.py <state.json>"); sys.exit(2)
    sys.exit(main(sys.argv[1]))
