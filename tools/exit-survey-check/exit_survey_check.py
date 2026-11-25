#!/usr/bin/env python3
"""exit-survey-check — Exit Survey Gate (ES-1..ES-12).
Sources (read in full 2026-11-21):
- RevenueCat, Cancellation flow best practices: Letting users go the right way
  (2024-11-14) https://www-docs.revenuecat.com/blog/growth/app-cancellation-flow-best-practices/
  Survey: keep it short and simple; randomize the order of reasons; customize the
  follow-up question based on the reason given ("too expensive" -> "what would make
  it worth the price?" separates value vs affordability); start with why they are
  cancelling; then offer an option to stay customized to their feedback. Language:
  communicate value, never guilt-trip ("don't be a guilt-tripping clingy ex").
  Send an immediate personal confirmation of cancellation; if they cancelled via
  the store, add the survey immediately after. Offer must be personalized to them.
  Self-service: never "contact support / call to cancel"; count the steps —
  ideally no more than 4-6 steps to cancel. Pause only where the platform supports
  it and never indefinitely (not available for App Store / Play subscriptions).
- RevenueCat, 'Not Enough Usage' vs. Price: How to Diagnose Subscription Churn
  https://www.revenuecat.com/blog/growth/not-enough-usage-churn
  'Not enough usage' is the #1 stated reason (37% SOSA 2025; 26-40% in 2026),
  price 35%. BUT stated reasons matched the actual driver only 27.4% of the time
  (User Intuition, n=723); price was stated by 34.2% but the real driver in only
  11.7% of those cases. Do not stop at survey data: triangulate with pre-cancel
  usage (30 days before), segment stated-price churners by usage frequency,
  compare reasons across price tiers. A discount does not fix usage churn
  (50%-discount cohort: GBP50 lower LTV, higher churn). Voluntary usage churn is
  a different problem from involuntary billing churn — different fix.
Distinct from customer-center-check (whether the Customer Center surface and its
survey/offer wiring exist), cancel-check (Apple Retention Messaging in ASC) and
winback-timing-check (when post-churn offers fire): this gate is ONLY about the
design and interpretation of the exit survey itself.
Free: Python stdlib only. Input: JSON state. Exit 0 = PASS, 1 = FAIL."""
import json, sys
CHECKS = [
 ("ES-1","why_first_before_offer","Why-first order: the survey asks why they are cancelling BEFORE any stay offer is shown (offer second, matched to the answer)"),
 ("ES-3","reason_order_randomized","The order of cancellation reasons is randomized (a fixed first option harvests clicks, not reasons)"),
 ("ES-4","reason_specific_followup","The follow-up question is customized per reason (e.g. 'too expensive' -> 'what would make it worth the price?', separating value from affordability)"),
 ("ES-5","offer_matched_to_reason","The stay offer is customized to the stated reason, not a generic discount shown to everyone"),
 ("ES-6","no_discount_for_usage_reason","Usage-reason churners are NOT answered with a discount (a price cut does not repair a broken habit; discount cohort had lower LTV and higher churn)"),
 ("ES-7","no_guilt_trip_language","Cancellation copy contains no guilt-tripping / breakup language and communicates value instead"),
 ("ES-8","immediate_cancellation_confirmation","An immediate personal confirmation reassures the user the cancellation took effect (silence after cancelling — the Strava failure — is a fail)"),
 ("ES-9","stated_reason_not_treated_as_truth","Stated reasons are recorded as surface explanations, NOT as the churn cause (stated vs actual match is only 27.4%; price stated 34.2% vs real 11.7%)"),
 ("ES-10","triangulated_with_usage_data","Survey answers are triangulated with behavioural data: pre-cancel 30-day usage, usage-frequency segmentation of stated-price churners, reason split by price tier"),
 ("ES-11","voluntary_involuntary_separated","Voluntary (survey) churn and involuntary billing churn are measured and fixed separately (different problem, different fix)"),
 ("ES-12","feedback_routed_to_product_fix","Survey findings are routed into an upstream product/onboarding fix with an owner (insights segment earlier prevention; a survey nobody acts on is decoration)"),
]
def main(path):
    s=json.load(open(path)); fails=[]
    for gid,key,desc in CHECKS:
        ok = s.get(key) is True
        print(f"{'PASS' if ok else 'FAIL'} {gid} {desc}")
        if not ok: fails.append(gid)
    # ES-2 numeric: survey must be short — one reason question, at most 2 questions total
    q = s.get("survey_question_count")
    ok2 = isinstance(q,(int,float)) and 1 <= q <= 2
    print(f"{'PASS' if ok2 else 'FAIL'} ES-2 Survey is short and simple: {q!r} question(s), at most 2 (reason + one reason-specific follow-up); people skip long exit surveys")
    if not ok2: fails.append("ES-2")
    total=12; passed=total-len(fails)
    print(f"TOTAL {'PASS' if not fails else 'FAIL'} {passed}/{total}")
    return 0 if not fails else 1
if __name__=="__main__":
    sys.exit(main(sys.argv[1]))
