#!/usr/bin/env python3
"""signup-placement-check: deterministic gate for WHERE account creation sits in onboarding.
Stdlib only, offline, free.
Primary source (read via social.search this run, 2026-11-25):
- Chris Raroque (@chris.raroque, IG, 53K followers) reel 2026-08-25
  https://www.instagram.com/reel/DceFq7bCXe0/ (4.5K likes, 120 comments):
  'My Top 10 App Mistakes' #5 -- signup/account screen placed BEFORE the
  onboarding questions gave ~50% signup completion; reversing the flow so
  users complete onboarding (weight/height/gender/activity in his app)
  first and meet signup at Step 9 raised completion to ~90% (+~40pp).
  Side-by-side mockups + before/after chart shown; examples from other
  apps cited. This is one practitioner's self-reported before/after on
  his own app, NOT a controlled A/B test -- the gate therefore requires
  local measurement, never imports the 90% figure as an expectation.
Boundary: onboarding-length-check owns length/leak diagnosis;
onboarding-check / adaptive-ob own question design. This gate owns only
the PLACEMENT of the account-creation step relative to first value and
to the onboarding questions, and the measurement that separates signup
completion from downstream paywall conversion.
Exit 0 = PASS, 1 = FAIL.
"""
import json, sys

def check(d):
    f = []
    inv = d.get("inventory") or {}
    if not inv.get("signup_step_position_recorded"):
        f.append("SP-0 signup/account step position in the flow is not recorded (step number / before-or-after questions / before-or-after first value)")
    if not inv.get("signup_required_or_optional_recorded"):
        f.append("SP-0 whether signup is required, optional, or deferred (guest/skip) is not recorded per app")
    if not inv.get("per_app_inventory_complete"):
        f.append("SP-0 inventory is not complete across all apps (a default SDK/template placement in one app is still a placement decision)")
    plc = d.get("placement") or {}
    if plc.get("signup_before_any_value"):
        f.append("SP-1 signup sits before any value/onboarding questions (Raroque mistake #5 form: ~50% completion in his self-report)")
    if not plc.get("onboarding_questions_before_signup"):
        f.append("SP-1 onboarding questions are not completed before signup is requested (the winning order in the source: questions first, signup late, Step 9 in his flow)")
    if not plc.get("signup_after_first_value_or_plan_reveal"):
        f.append("SP-1 signup is not placed after first value / personalised plan reveal, so the user is asked for identity before knowing why the account is worth having")
    pro = d.get("prohibitions") or {}
    if pro.get("password_wall_before_benefit_explained"):
        f.append("SP-2 a password/credential wall is demanded before the benefit of an account is explained")
    if pro.get("signup_blocks_browsing_free_value"):
        f.append("SP-2 signup blocks browsing free value that could be shown without an account")
    if pro.get("fake_account_benefit_claimed"):
        f.append("SP-2 an account benefit is claimed that the product does not actually deliver (sync/backup/personalisation must be real)")
    mea = d.get("measurement") or {}
    if not mea.get("signup_completion_measured_separately"):
        f.append("SP-3 signup completion is not measured separately from onboarding completion and paywall conversion (placement effects hide inside the blended funnel)")
    if not mea.get("counts_recorded_not_rates_only"):
        f.append("SP-3 funnel counts are not recorded (starts, questions completed, signup shown, signup completed) -- rates alone hide cohort-size effects")
    if not mea.get("downstream_paywall_checked"):
        f.append("SP-3 downstream paywall reach / trial starts are not checked after a placement change (moving signup later must not silently starve the paywall, cf. Everlove split result)")
    cit = d.get("citation") or {}
    if not cit.get("source_numbers_cited_with_design"):
        f.append("SP-4 the source numbers are not cited with their design (one practitioner, self-reported before/after, no control arm, his app/category -- not a benchmark)")
    if cit.get("source_90pct_used_as_target"):
        f.append("SP-4 the source's ~90% is used as a target/expectation for our apps (importing a single-app before/after as a promise is fabrication)")
    if not cit.get("revenue_chain_recorded"):
        f.append("SP-4 the revenue chain is not recorded (signup completion -> registered-user base -> paywall reach -> conversion, each step measured locally)")
    rev = d.get("reversibility") or {}
    if not rev.get("placement_change_is_reversible_test"):
        f.append("SP-5 a placement change is not framed as a reversible, separately-tested change (do not bundle with length/paywall changes -- attribution dies)")
    if not rev.get("guest_state_preserved_on_decline"):
        f.append("SP-5 declining/deferring signup does not preserve the user's onboarding answers/state (punishing deferral recreates the wall)")
    if not rev.get("review_cadence_recorded"):
        f.append("SP-5 no review cadence is recorded for re-checking placement when onboarding or paywall changes")
    return f

def main():
    d = json.load(open(sys.argv[1])); fails = check(d)
    for x in fails: print("FAIL:", x)
    print(f"{'PASS' if not fails else 'FAIL'}: {len(fails)} fail(s) -- {d.get('app')}")
    sys.exit(0 if not fails else 1)
if __name__ == "__main__": main()
