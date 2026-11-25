#!/usr/bin/env python3
"""owned-audience-check: deterministic gate for the OWNED AUDIENCE (email capture) surface.
Stdlib only, offline, free.
Owns: whether an app collects a reachable address at all, where the ask sits,
how the address is wired to subscription identity, and whether collected
addresses are actually acted on. Not win-back campaign mechanics
(winback-check), not dunning (dunning-check), not share/referral (share-check).
Sources (read 2026-11-22):
- Adapty, "How to collect emails in your mobile app without killing conversion"
  https://adapty.io/blog/how-to-collect-emails-in-your-mobile-app/
  Top 5% of subscription apps earn 13.2% of revenue from email vs 4.3% median
  (Adapty analysis of 5B emails, vendor figure). Zeely, Cal AI, Flo and Hallow
  collect at 40%+ opt-in with no measurable paywall impact. The ask converts
  AFTER the user has built something worth protecting: quiz -> loader ->
  result with their own numbers and a date -> email framed as preservation
  ("Save your progress"), as the last step before retrieving the result.
  Four patterns: (1) quiz-gated before paywall, (2) in-app after value,
  (3) early with feature-specific utility, (4) after paywall / gradual.
  A generic "Create an account" screen at the top loses people. For sensitive
  data, a privacy screen immediately before the field neutralises the
  data-grab reading. Three failure modes: never built collection; collected
  but never wired to a sender; known but never scheduled.
- RevenueCat, "Recover churned subscribers automatically with win-back
  campaigns for web" https://www.revenuecat.com/blog/company/win-back-campaigns-for-web
  The win-back email goes to the address stored in the $email subscriber
  attribute; if the app does not collect email in signup/onboarding, it must
  start setting it via the SDK before any win-back can exist.
- House rules (founder, primary): raw behaviour / personal data stays private
  and is never sold (what is sold is the upper layer only); paid growth tools
  are never even considered; a deferred decision that never gets scheduled is
  a system problem, not a resting place.
Exit 0=PASS, 1=FAIL.
"""
import json, sys
def check(d):
    f=[]
    c=d.get("collection") or {}
    if not c.get("email_collection_exists"): f.append("OA-0 no email collection exists at all (every churned user is gone permanently; the never-purchased segment alone is usually larger than the paying base and entirely out of reach)")
    if not c.get("placement_pattern_named_from_four"): f.append("OA-0 no placement pattern is named (one of: quiz-gated before paywall / in-app after value / early with feature-specific utility / gradual after paywall -- an unnamed placement is an unmade decision)")
    if not c.get("ask_after_something_worth_protecting_built"): f.append("OA-0 the ask does not come after the user built something worth protecting (40%+ opt-in comes from asking at retrieval time -- a plan, result, streak or log the user would pay a real cost to lose)")
    if c.get("generic_create_account_at_top"): f.append("OA-0 a generic 'Create an account' screen sits at the top of onboarding (a demand with no visible benefit, shown before anything worth staying for -- the documented losing form)")
    t=d.get("timing_framing") or {}
    if not t.get("result_preview_with_own_numbers_before_ask"): f.append("OA-1 no result preview with the user's own numbers and a date precedes the ask (a goal without a deadline is a wish; the specific result is what makes the address feel worth giving)")
    if not t.get("framing_is_preservation_not_account_creation"): f.append("OA-1 the ask is framed as account creation, not preservation ('Save your progress' / 'access your plan' -- the user is protecting what they built, not registering)")
    if not t.get("privacy_commitments_before_ask_for_sensitive_data"): f.append("OA-1 no privacy commitments immediately precede the ask (for suffering/health-adjacent data the ask reads as a data grab without them; the privacy screen is a conversion tool, not compliance decoration)")
    if not t.get("no_price_information_forced_before_ask_decision_recorded"): f.append("OA-1 the price-exposure trade-off is unrecorded (Cal AI shows no pricing before the ask, which fills the list with low-intent addresses the sequences must then convert -- copy the pattern knowingly or not at all)")
    i=d.get("identity_wiring") or {}
    if not i.get("email_set_as_subscription_email_attribute"): f.append("OA-2 the address is not set as the subscription platform's $email attribute (win-back, billing recovery and re-engagement all address that attribute; an address saved 'somewhere' reaches nobody)")
    if not i.get("identity_matched_to_app_user_id"): f.append("OA-2 addresses are not matched to the app user ID (subscription platforms identify people by app user ID, not email; unmatched events land on nobody)")
    if i.get("anonymous_ids_turned_into_contacts"): f.append("OA-2 anonymous IDs are turned into contacts (junk contacts poison deliverability and segment counts; anonymous IDs are skipped, not stored as people)")
    if not i.get("apple_relay_address_handling_recorded"): f.append("OA-2 Sign in with Apple relay addresses are unhandled in the record (Apple may return a relay address instead of a real one; reachability planning that ignores this overstates the owned audience)")
    a=d.get("actionability") or {}
    if not a.get("collection_connected_to_a_sender"): f.append("OA-3 collected addresses are not connected to any sender (failure mode two: the address is saved, no integration exists, sequences sit unconfigured, and the billing-issue segment churns silently every month)")
    if not a.get("flows_cover_never_purchased_trial_billing_expired"): f.append("OA-3 lifecycle flows do not cover the four segments that require an address (never purchased / renewal cancelled / billing issue / expired -- each has a playbook and all of them require the address first)")
    if not a.get("email_attributed_revenue_measured"): f.append("OA-3 email-attributed revenue is not measured (the 13.2% vs 4.3% gap is only visible if email revenue is read separately; unmeasured, the channel looks like zero and stays unfunded in attention)")
    m=d.get("measurement") or {}
    if not m.get("optin_rate_measured_against_40pct_winner_bar"): f.append("OA-4 the opt-in rate is not measured against the winner bar (Zeely / Cal AI / Flo / Hallow sit at 40%+; an unmeasured rate cannot be judged, and a rate far below the bar is a placement problem, not a user problem)")
    if not m.get("paywall_impact_measured_before_after"): f.append("OA-4 paywall impact of the ask was not measured before/after (the fear that the ask kills conversion is only settled by measuring it; placed correctly the winners saw no measurable paywall impact)")
    if not m.get("segment_sizes_known"): f.append("OA-4 segment sizes are unknown (you cannot prioritise flows without knowing how many people sit in never-purchased vs expired; the largest segment is usually the one nobody emails)")
    h=d.get("house_rules") or {}
    if not h.get("raw_addresses_kept_private_never_sold"): f.append("OA-5 raw addresses are not kept private (house rule: raw personal / behaviour data is never sold; only the upper layer is a product -- an owned list is a trust asset, not inventory)")
    if not h.get("consent_and_optin_recorded"): f.append("OA-5 consent / opt-in is not recorded per address (an address without its consent record is a liability in every later send, not an asset)")
    if not h.get("no_paid_tool_blocks_collection"): f.append("OA-5 collection is blocked waiting on a paid tool decision (house rule: paid growth is never even considered -- collection ships on the free / already-paid stack, and 'email is on the roadmap' for two quarters is a system failure)")
    return f
def main():
    d=json.load(open(sys.argv[1]))
    fails=check(d)
    for x in fails: print("FAIL", x)
    print(f"RESULT: {'PASS' if not fails else 'FAIL'} ({len(fails)} fails)")
    sys.exit(0 if not fails else 1)
if __name__=="__main__": main()
