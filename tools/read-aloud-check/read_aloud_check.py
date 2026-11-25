#!/usr/bin/env python3
"""read-aloud-check: deterministic gate for the PAYWALL READ-ALOUD test
(can a fresh user, reading only the signup screens, say in plain language
what they will pay after the trial and how they cancel?).
Stdlib only, offline, free. Exit 0=PASS, 1=FAIL.

Source (read in full 2026-11-23):
- Box Fresh, "The Paywall Read-Aloud Test: Six Apps, Two Honest Answers,
  Four Mumbled Excuses" (published 2026-11-13)
  https://box-freshapp.com/paywall-read-aloud-test-apps-2026/
  Method: fresh email + low-limit virtual card, standard consumer plan,
  screenshots of every disclosure screen, then one support question --
  "What will I pay after the trial, and how do I cancel?" Scored on five
  things: trial length, renewal price, cancellation steps, feature limits,
  and whether the signup screen told the truth without a magnifying glass.
  2 of 6 passed. Winners: renewal price on the SAME screen as the
  "Start free trial" button (CalPal $6/mo, 14-day trial, limits in a short
  table, cancel in 3 taps, support reply matched the screen in plain text);
  SnapNote added a price-confirmation checkbox before trial start.
  Failures: renewal price only in a gray footnote under Continue
  ($12.99/mo); cancel replaced by "Pause plan" + business-hours chat;
  "free forever" with a 15-minute cap and an upgrade prompt at minute 12,
  renewal price ($18/mo) disclosed only AFTER "Start trial"; "7 days free"
  counted from account creation, not trial start ($15/mo), cancel
  instructions only in a help article linked from the receipt email.
  Dark patterns named: pre-checked annual upgrades, countdown timers that
  reset on refresh, pause buttons that do not stop billing, support chats
  that only work in business hours, card asked for before pricing is shown.
  Caveat: this is a 6-app mystery shop by one small publication, not a
  large-sample study -- the gate uses its five scoring dimensions and its
  pass/fail examples, not any prevalence claim.

Separation: price-consent-check owns price-INCREASE consent for existing
subscribers; paywall-2026-check / paywall-cta-check own paywall structure
and CTA; customer-center-check owns the self-service management surface;
dunning-check owns billing-error recovery. This gate owns only the
first-purchase plain-language truth test: what the signup screens say,
in the order and prominence they say it, verified by a fresh-account
read-aloud and a support-answer match.
"""
import json, sys

CHECKS = [
    ("audit_recorded", "RA-0 no read-aloud audit is recorded (a fresh-account mystery shop with screenshots of every disclosure screen; a designer reading their own paywall is not the test -- 4 of 6 apps in the source looked fine to their makers and failed a stranger)"),
    ("owner_named", "RA-0 no named owner for the read-aloud audit (the audit must be re-run by a named owner, not absorbed into general QA)"),
    ("fresh_account_test_done", "RA-0 the test was not done as a fresh user (fresh email, standard consumer plan, no pre-checked upgrade clicked; an existing/tester account already knows where the price and the cancel button hide)"),
    ("trial_length_on_signup_screen", "RA-1 trial length is not stated on the signup screen itself (the source pattern: trial length is big, the word 'trial' is saved for a later screen -- the length belongs where the decision is made)"),
    ("renewal_price_same_screen_as_cta", "RA-1 the renewal price is not on the same screen as the trial-start button (both passing apps did this; a price on a later screen is a price disclosed after commitment)"),
    ("renewal_price_not_footnote_only", "RA-1 the renewal price appears only in a footnote / small gray text under the button (PocketPlan failed on exactly this: $12.99/mo in a gray footnote under Continue)"),
    ("renewal_date_basis_is_trial_start", "RA-2 the renewal date is not counted from trial start (TaskTide failed: '7 days free' counted from account creation, so the free period the user actually gets is shorter than the screen promises)"),
    ("price_shown_before_payment_entry", "RA-2 pricing is not shown before the user is asked for payment (source: 'The price should come first' -- card-before-pricing reverses the decision)"),
    ("no_prechecked_upgrade_beyond_chosen_plan", "RA-2 an upgrade beyond the plan the user chose is pre-checked (a pre-checked annual upgrade is named in the source as a dark pattern to spot before tapping Start; pre-selection inside one paywall's plan list is a separate, already-gated question)"),
    ("free_claim_matches_actual_limits", "RA-3 a 'free' / 'free forever' claim does not match the plan's actual limits (MeetMint failed: 'free forever' calls capped at 15 minutes; a real but locked free plan must say what is locked, on the listing/paywall, not after)"),
    ("feature_limits_on_pricing_surface", "RA-3 feature limits are not on the pricing surface itself (SnapNote's only deduction: the free plan's export limit buried in the help center; limits that decide the purchase belong in a short table next to the price)"),
    ("in_product_upgrade_prompts_disclosed", "RA-3 in-product upgrade prompts are not disclosed at signup (an upgrade prompt appearing mid-use -- e.g. at minute 12 of a 15-minute free call -- is part of the free plan's real shape and must not be a surprise)"),
    ("cancel_steps_counted", "RA-4 cancellation steps are not counted and recorded (the passing apps were 2-3 taps in Settings/account; an uncounted cancel path is an unmeasured one, and email-to-support with a 48-hour window is not a step count, it is a wait)"),
    ("cancel_is_cancel_not_pause", "RA-4 the cancel action is replaced by pause (CloudCrate failed: 'Pause is not cancel' -- a pause that does not stop the subscription must never be presented as the way to stop it)"),
    ("cancel_without_chat_or_email", "RA-4 cancellation requires a chat (business hours only) or an email to support (a support channel is not a cancellation step; if stopping feels like a support issue, users will read it as one -- source holiday rule)"),
    ("support_answer_matches_screen", "RA-5 the support answer to 'What will I pay after the trial, and how do I cancel?' does not match the signup screens in plain language (both passing apps answered with the same information in plain text; a template that contradicts or dodges the screen fails the whole test)"),
    ("no_resetting_countdown", "RA-5 a countdown on the paywall resets on refresh / is not a real deadline (named in the source's dark-pattern list; a resetting timer is a false deadline, already banned in this company)"),
    ("reaudit_per_release_with_screenshots", "RA-5 the read-aloud audit is not re-run per release with screenshots archived (prices, trials and cancel paths change between releases; last version's honesty is not this version's)"),
]
def main(path):
    s = json.load(open(path))
    fails = [msg for key, msg in CHECKS if s.get(key) is not True]
    for f in fails: print("FAIL", f)
    print(f"RESULT {'PASS' if not fails else 'FAIL'} pass={len(CHECKS)-len(fails)}/{len(CHECKS)} fails={len(fails)}")
    return 0 if not fails else 1
if __name__ == "__main__":
    if len(sys.argv) != 2: print("usage: read_aloud_check.py <state.json>"); sys.exit(2)
    sys.exit(main(sys.argv[1]))
