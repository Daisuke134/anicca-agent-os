#!/usr/bin/env python3
"""pause-check: deterministic gate for subscription pause as a pre-cancel lever.
Stdlib only, offline, free. Sources (read in full 2026-11-23):
- RevenueCat State of Subscription Apps 2026 Part 2, via ppc.land summary
  https://ppc.land/95-of-annual-app-subscribers-who-cancel-never-return-revenuecat-finds/
  Annual reactivation is capped at ~5% (4.4-5.9% across geography, price tier and
  discount depth); monthly ~20%. Pause yields higher reactivation because the
  relationship and the payment method survive, so return needs no re-entry.
  The effective intervention is before cancellation, not after.
- RevenueCat Monetization Strategies codelab
  https://revenuecat.github.io/codelabs/monetization-strategies.html
  In the cancellation survey, "don't use the app enough" maps to a pause offer;
  one retention offer matched to the stated reason.
- Geetansh Saini, "Pause subscription option for SaaS" (2026-10-13)
  https://www.geeetansh.com/guides/pause-subscription-option
  Pause beats cancel only when the reason is the calendar (seasonal / not now),
  never for price, missing feature or competitor. Fixed length 1-3 months with
  the resume date shown, extendable once; billing stops at the end of the paid
  period and restarts on the same plan with no new trial; data and settings are
  kept and that is stated in one sentence on the pause screen; pause is offered
  on the plan page, not only inside the cancel flow; one reminder before the
  resume date and a confirmation on the day. Measure resume rate (paying 30
  days after the resume date), net resume rate (still paying at 60 days),
  pause-to-cancel (a pause passing resume date + 30 days with no action counts
  as churn on that date), extension rate and pauses by reason. Paused MRR is
  its own line, never retained revenue until it resumes. Platform honesty:
  a store with no pause state (Shopify App Pricing in the guide) forces a
  workaround; never design assuming a state the platform does not provide.
Delimitation: cancel-check owns the cancel flow, winback-check owns
post-cancel recovery, exit-survey-check owns the survey. This gate owns the
pause state itself: reason matching, its fixed length and resume design, and
the honesty of its measurement.
Exit 0 = PASS, 1 = FAIL. Input JSON keys are the check names (booleans).
"""
import json, sys
CHECKS = [
    ("pause_offer_exists", "SP-0 no pause option exists at all (once an annual subscriber cancels, reactivation is capped at ~5% whatever the discount; the save has to happen before the cancel)"),
    ("pause_matched_to_not_now_reason", "SP-0 pause is not matched to the 'not using it right now / calendar' reason from the cancellation survey (one offer per reason; pause is the answer to that reason, not a generic save)"),
    ("pause_not_offered_for_price_or_feature_reasons", "SP-0 pause is offered to price, missing-feature or competitor leavers (for those reasons pause only delays the cancel by months and books it as a save in the meantime)"),
    ("platform_pause_mechanism_verified", "SP-1 the store's actual pause mechanism was not verified before designing (some stores expose no settable pause state; a design that assumes one hits the billing API and stops)"),
    ("fixed_length_with_resume_date_shown", "SP-1 pause length is not fixed (1-3 months, chosen by the user) with the resume date shown (an open-ended pause is a cancel that has not been admitted)"),
    ("extendable_once_only", "SP-1 the pause can be extended repeatedly (one extension, from inside the app, moving the date; repeated extensions signal the wrong reasons are being matched)"),
    ("billing_stops_and_resumes_same_plan", "SP-2 billing does not stop at the end of the paid period and restart on the resume date on the same plan with no new trial (the preserved payment method and plan are exactly why pause reactivates better than cancel)"),
    ("data_and_settings_preserved", "SP-2 the user's data, history and settings are not fully preserved through the pause (losing them on return removes the switching cost the pause was meant to keep)"),
    ("data_retention_stated_in_one_sentence", "SP-2 what happens to the user's data is not stated in one sentence on the pause screen and confirmation (stating it is not optional)"),
    ("pause_available_outside_cancel_flow", "SP-3 pause is only reachable inside the cancel flow (a user who knows a break is coming should be able to pause from the plan / subscription page without starting a cancellation)"),
    ("reminder_before_resume_and_confirmation_on_day", "SP-3 there is no reminder before the resume date and no confirmation on the day itself (a silent restart that charges without warning converts a save into a refund request)"),
    ("resume_rate_measured", "SP-4 resume rate is not measured (of pauses whose resume date passed, the share paying 30 days after that date; this is the headline number)"),
    ("net_resume_rate_measured", "SP-4 net resume rate is not measured (still paying 60 days after resuming; a resume that cancels after one invoice was delayed churn, and only this number catches it)"),
    ("pause_to_cancel_counted_as_churn", "SP-4 pauses that pass resume date + 30 days with no action are not counted as churn on that date (otherwise pause turns churn into a number nobody counts)"),
    ("pauses_reported_by_reason_and_extension", "SP-4 pauses are not reported by reason and extension rate (if 'too expensive' pauses resume poorly, the offer is matched to the wrong reason; if most pauses extend, the lengths offered are wrong)"),
    ("paused_mrr_reported_separately", "SP-5 paused MRR is not reported as its own line, separate from active and churned (a pause is not retained revenue until it resumes)"),
    ("no_fake_save_counting", "SP-5 a pause is counted as a save at the moment it is taken (a save is only proven when the user resumes and pays a second invoice)"),
    ("outside_equals_inside_pause", "SP-5 marketing or the cancel flow promises a pause the product or store cannot actually deliver (what is shown outside must exist inside)"),
]
def check(d):
    return [m for k, m in CHECKS if not d.get(k)]
def main():
    d = json.load(open(sys.argv[1]))
    fails = check(d)
    for f in fails: print("FAIL", f)
    print(f"RESULT: {'PASS' if not fails else 'FAIL'} ({len(CHECKS)-len(fails)}/{len(CHECKS)} checks passed, {len(fails)} fails)")
    sys.exit(0 if not fails else 1)
if __name__ == "__main__": main()
