#!/usr/bin/env python3
"""social-proof-check: deterministic gate for social proof placement and honesty.
Stdlib only, offline, free. Sources (read in full 2026-11-21):
- Airbridge, Social Proof for Apps https://www.airbridge.io/en/blog/social-proof-for-apps
  (placement > presence; three trust moments; 82% of trial decisions Day 0; never before
  user investment; goal first then matching testimonial; loading screen = final trust layer
  with precise counts; precision builds credibility; paywall sequence rating top /
  testimonial middle / user count near CTA; rating before price; purchase likelihood peaks
  4.2-4.5 stars; below ~4.0 or low volume lead with counts/outcomes instead; testimonial
  must answer the category objection specifically; freshness beats old volume)
- Adapty, high-performing paywall 2026 https://adapty.io/blog/high-performing-paywall-2026/
  (audit item: social proof visible before or on paywall; personalized plan loader with
  social proof is table stakes) and paywall experiments playbook (never change price +
  background + reviews together; don't manufacture fake social proof)
- Ernesto Lopez 9-step onboarding (IG, 21,346 screens / 1,335 apps): step (5) is
  "Reviews from similar users".
Exit 0 = PASS, 1 = FAIL.
"""
import json, sys

def check(d):
    fails = []
    if not d.get("inventory_recorded"):
        fails.append("SP-0 proof claims are not inventoried with sources across store/onboarding/loading/paywall surfaces")
    if not d.get("all_proof_real_and_sourced"):
        fails.append("SP-1 not every testimonial/count is a real, verbatim, source-recorded claim (fabricated or unsourced proof is prohibited)")
    if d.get("fabricated_proof_present"):
        fails.append("SP-1 fabricated proof is present (invented testimonial, made-up user count, or inflated rating)")
    if d.get("proof_on_first_screen_before_investment"):
        fails.append("SP-2 social proof sits on the first screen before any user investment (it reads as a brand claim, not peer validation)")
    ob = d.get("onboarding") or {}
    if not ob.get("goal_collected_before_proof"):
        fails.append("SP-3 the user's goal is not collected before proof is shown (matching is impossible without the goal)")
    if not ob.get("goal_matched_testimonial_shown"):
        fails.append("SP-3 no goal-matched testimonial is shown after goal selection (Ernesto step 5: reviews from similar users)")
    if (ob.get("testimonial_library_per_goal") or 0) < 1:
        fails.append("SP-3 testimonial library has fewer than 1 sourced quote per goal option (generic praise is not a library)")
    if ob.get("generic_praise_used_as_testimonial"):
        fails.append("SP-3 generic praise ('I love this app') is used in place of a goal-matched, specific testimonial")
    ld = d.get("loading_layer") or {}
    if not ld.get("proof_present"):
        fails.append("SP-4 the pre-paywall loading/plan-builder screen carries no proof (it is the highest-attention, zero-friction trust layer)")
    if not (ld.get("precise_user_count_with_date") or ld.get("rating_with_count")):
        fails.append("SP-4 loading layer has neither a precise user count with an as-of date nor a rating with review count")
    pw = d.get("paywall") or {}
    if not pw.get("rating_and_count_at_top"):
        fails.append("SP-5 paywall does not lead with rating + review count near the headline (the first element frames price as trust or as cost)")
    if not pw.get("testimonial_below_plans"):
        fails.append("SP-5 no goal-matched testimonial in the paywall middle, below the plan options")
    if not pw.get("user_count_near_cta"):
        fails.append("SP-5 no user count near the CTA (community validation at the decision point)")
    rt = d.get("rating_handling") or {}
    if not rt.get("featured_rating_is_real_store_rating"):
        fails.append("SP-6 the featured rating is not the app's real current store rating")
    if rt.get("rating_below_4_or_volume_below_50") and rt.get("leads_with_rating"):
        fails.append("SP-6 rating leads the proof while the rating is below 4.0 or volume below 50 (lead with user count/outcomes/press instead)")
    if rt.get("perfect_rating_presented"):
        fails.append("SP-6 a perfect 5.0 is presented as the proof anchor (purchase likelihood peaks at 4.2-4.5; 5.0 reads as curated)")
    if d.get("vague_numbers_used"):
        fails.append("SP-7 vague numbers are used ('thousands of users', 'everyone loves it') instead of precise, dated, verifiable figures")
    if not d.get("outcome_claims_have_timeframe"):
        fails.append("SP-7 outcome claims carry no timeframe (an outcome without a period is an unsubstantiated claim)")
    if not pw.get("testimonial_answers_main_objection"):
        fails.append("SP-8 the paywall testimonial does not specifically answer the category's main objection (sticking with it / it works for me)")
    fr = d.get("freshness") or {}
    if not fr.get("featured_reviews_freshness_tracked"):
        fails.append("SP-9 freshness of featured reviews is not tracked (recent reviews outperform a larger old set)")
    if not fr.get("supply_connected_to_value_moment_prompt"):
        fails.append("SP-9 proof supply is not connected to the value-moment review prompt (freshness has no inflow)")
    ms = d.get("measurement") or {}
    if not ms.get("tested_as_single_variable"):
        fails.append("SP-10 proof placement was not tested as a single variable (price/background/reviews changed together cannot be attributed)")
    if not ms.get("judged_on_trial_or_revenue"):
        fails.append("SP-10 proof is not judged on trial starts / paid revenue (clicks and views are not the decision metric)")
    if ms.get("shown_to_subscribed_users"):
        fails.append("SP-10 paywall proof is shown to subscribed users (the paywall itself must never be shown to them)")
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
