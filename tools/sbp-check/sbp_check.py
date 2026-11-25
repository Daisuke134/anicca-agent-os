#!/usr/bin/env python3
"""sbp-check: deterministic gate for the APP STORE SMALL BUSINESS
PROGRAM surface (the commission rate the company actually pays Apple:
15% under the program vs the standard 30%).
Stdlib only, offline, free.
Source (read in full 2026-11-16):
- Apple Developer official "App Store Small Business Program"
  https://developer.apple.com/app-store/small-business-program/
  Reduced commission of 15% on paid apps and In-App Purchases for
  developers whose total proceeds (sales net of Apple's commission and
  certain taxes and adjustments), together with all Associated
  Developer Accounts, were no more than 1 million USD in the prior
  calendar year (the 12 fiscal months occurring within it) and no more
  than 1 million USD in the current year; new developers qualify.
  Surpassing the threshold in the current year moves FUTURE sales to
  the standard rate; falling below it in a future year re-qualifies
  the year after. Enrollment requires the Account Holder, acceptance
  of the latest Paid Apps agreement (Schedule 2) in App Store Connect,
  and listing every Associated Developer Account (an account the
  developer owns/controls, or that owns/controls the developer --
  >50% ownership or ultimate decision-making authority), with name,
  Team ID, Account Holder email, and relationship for each. Adjusted
  proceeds take effect 15 days after the end of the fiscal month in
  which enrollment is approved. Eligibility is estimated from bank
  deposits plus taxes/adjustments in App Store Connect Payments and
  Financial Reports, converted to USD. App transfers associate the
  year's proceeds with all accounts that initiate or accept the
  transfer. EU alternative-terms developers in the program get 10% on
  subscriptions after their first year. Enrolled developers with
  fewer than two million first-time downloads are also eligible for
  Apple Foundation Models on Private Cloud Compute at no cloud API
  cost (PCC entitlement required).
Exit 0 = PASS, 1 = FAIL.
Input JSON: {app,
 inventory:{decision_recorded, eligibility_facts_recorded,
   apps_and_accounts_enumerated, proceeds_estimate_computed},
 associated:{associated_identified_or_none_recorded,
   details_collected_for_each, proceeds_included_in_eligibility},
 enrollment:{enrollment_verified_in_asc,
   paid_apps_agreement_current, approval_state_read_back},
 rate:{effective_date_recorded, effective_rate_verified_from_reports,
   reporting_uses_actual_rate},
 threshold:{proceeds_tracked_against_threshold,
   crossing_consequence_recorded, requalification_calendared},
 measurement:{commission_cost_line_tracked,
   eu_variant_decision_recorded, pcc_benefit_decision_recorded}}
"""
import json, sys

def check(d):
    fails = []
    inv = d.get("inventory") or {}
    if not inv.get("decision_recorded"):
        fails.append("SB-0 no Small Business Program decision is recorded (whether the company is enrolled, enrolling, or knowingly not enrolled is nowhere written -- at the standard 30% rate an unrecorded non-decision silently doubles the commission on every sale)")
    if not inv.get("eligibility_facts_recorded"):
        fails.append("SB-0 the eligibility facts are not recorded: 15% on paid apps and IAP for total proceeds of no more than 1 million USD in the prior calendar year and the current year, aggregated with Associated Developer Accounts; new developers qualify")
    if not inv.get("apps_and_accounts_enumerated"):
        fails.append("SB-0 the apps and accounts inside the proceeds total are not enumerated for eligibility (eligibility is an account-level aggregate over every app and every Associated Developer Account -- a total nobody enumerated cannot be compared to the threshold honestly)")
    if not inv.get("proceeds_estimate_computed"):
        fails.append("SB-0 no eligibility proceeds estimate was computed by Apple's method (bank deposits for the prior calendar year, adjusted with taxes and adjustments from App Store Connect Payments and Financial Reports, converted to USD, associated accounts included) -- 'we are obviously small' is an impression, not an estimate")
    asc = d.get("associated") or {}
    if not asc.get("associated_identified_or_none_recorded"):
        fails.append("SB-1 Associated Developer Accounts were never assessed (Apple's test: an account you own or control, or that owns or controls yours -- over 50% ownership or ultimate decision-making authority, in either direction; an unassessed 'none' is a guess, and an undisclosed associated account voids the eligibility it was meant to prove)")
    if not asc.get("details_collected_for_each"):
        fails.append("SB-1 the per-account details Apple requires are not collected for each Associated Developer Account (name, Team ID, Account Holder email address, description of the relationship) -- enrollment cannot be completed without them")
    if not asc.get("proceeds_included_in_eligibility"):
        fails.append("SB-1 associated accounts' proceeds are not included in the eligibility total (the threshold applies to the collective proceeds of all related accounts, not to one account read alone)")
    enr = d.get("enrollment") or {}
    if not enr.get("enrollment_verified_in_asc"):
        fails.append("SB-2 enrollment is not verified in App Store Connect (enrollment is an Account Holder action in ASC; intent, eligibility, and memory are not enrollment, and an unverified state must be reported as unverified, never as enrolled)")
    if not enr.get("paid_apps_agreement_current"):
        fails.append("SB-2 acceptance of the latest Paid Apps agreement (Schedule 2 to the Apple Developer Program License Agreement) is not verified current -- it is a stated enrollment prerequisite, and a stale agreement blocks the adjusted rate")
    if not enr.get("approval_state_read_back"):
        fails.append("SB-2 the enrollment approval state was never read back (submission is not approval; the adjusted rate runs from approval, so an unread approval state leaves the effective rate unknown)")
    rate = d.get("rate") or {}
    if not rate.get("effective_date_recorded"):
        fails.append("SB-3 the adjusted-proceeds effective date is not recorded (adjusted proceeds begin 15 days after the end of the fiscal month in which enrollment is approved -- without that date, no financial report can be reconciled against the rate that should have applied)")
    if not rate.get("effective_rate_verified_from_reports"):
        fails.append("SB-3 the effective commission rate was never verified from financial reports (15% must be read off actual Payments and Financial Reports, not assumed from eligibility or enrollment -- a rate nobody reconciled can be wrong indefinitely without anyone noticing)")
    if not rate.get("reporting_uses_actual_rate"):
        fails.append("SB-3 revenue and gross-profit reporting does not use the verified actual commission rate (proceeds, MRR, and gross profit computed at an assumed rate misstate the company's top-line economics by up to 15 points of every sale)")
    thr = d.get("threshold") or {}
    if not thr.get("proceeds_tracked_against_threshold"):
        fails.append("SB-4 current-year proceeds are not tracked against the 1 million USD threshold (crossing it moves future sales to the standard rate; a threshold nobody watches is discovered from a smaller bank deposit, after the fact)")
    if not thr.get("crossing_consequence_recorded"):
        fails.append("SB-4 the crossing consequence is not recorded (surpass the threshold in the current year and the standard rate applies to future sales; app transfers also associate the year's proceeds with every account that initiates or accepts the transfer)")
    if not thr.get("requalification_calendared"):
        fails.append("SB-4 re-qualification is not calendared (if proceeds fall below the threshold in a future calendar year, the developer can re-qualify for 15% the year after -- an uncalendared re-qualification is a discount that expires unclaimed)")
    ms = d.get("measurement") or {}
    if not ms.get("commission_cost_line_tracked"):
        fails.append("SB-5 commission paid to Apple is not tracked as its own cost line (commission is the company's largest single cost of sale; folded invisibly into 'proceeds' it can never be compared across rates, stores, or the web-paywall alternative)")
    if not ms.get("eu_variant_decision_recorded"):
        fails.append("SB-5 the EU alternative-terms variant has no recorded decision (developers on the EU alternative terms who are in the program receive 10% on subscriptions after their first year -- applicable or not, the decision belongs in the record next to the rate)")
    if not ms.get("pcc_benefit_decision_recorded"):
        fails.append("SB-5 the Private Cloud Compute benefit has no recorded decision (enrolled developers with fewer than two million first-time downloads can use Apple Foundation Models on PCC at no cloud API cost, entitlement required -- an unrecorded benefit is a free inference budget nobody claims)")
    return fails

def main():
    if len(sys.argv) != 2:
        print("usage: sbp_check.py <state.json>")
        return 2
    with open(sys.argv[1]) as f:
        d = json.load(f)
    fails = check(d)
    app = d.get("app", "?")
    if fails:
        print(f"FAIL {app}: {len(fails)} gate failures")
        for x in fails:
            print(" -", x)
        return 1
    print(f"PASS {app}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
