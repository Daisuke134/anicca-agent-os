#!/usr/bin/env python3
"""paywall-structure-check: deterministic gate for the 2026 PAYWALL STRUCTURE surface.
Stdlib only, offline, free. Canonical source (read in full 2026-11-19):
RevenueDot "Paywall best practices for 2026" https://revenuedot.app/blog/paywall-best-practices-2026
 aggregating: RevenueCat State of Subscription Apps 2026 (hard 10.7% vs freemium 2.1% Day-35;
 $3.09 vs $0.38 RPI Day-60; trial toggle rejected since Jan 2026 under 3.1.2; rating prompt
 cited under 5.6.3), Adapty 2026 (89.4% trial starts Day 0; weekly 55.5% of revenue),
 Superwall (multi-page 12.41% vs single 9.07% over 40M opens; simple beats chart +111%;
 exit offers = 17% of revenue across 18 companies), Lazyweb (median paywall at step 11 of 17.2),
 Growth.design Blinkist (timeline+reminder: +23% trials, reminder opt-in 6%->74%),
 trial length: 17-32d converts 42.5% vs <=4d 25.5% (RevenueCat via source).
Exit 0 = all pass, 1 = any fail. null/unverified counts as fail (recorded as such)."""
import json, sys
def check(d):
    r = {}
    r["PW-0a_surface_decided"] = d.get("decided") is True and bool(d.get("owner")) and bool(d.get("source"))
    r["PW-0b_gate_rationale"] = (d.get("gate_type") == "hard") or (d.get("gate_type") == "soft" and d.get("gate_rationale_recorded") is True)
    r["PW-1a_quiz_shape"] = d.get("one_question_per_screen") is True and (d.get("onboarding_steps") or 0) >= 10
    r["PW-1b_value_before_paywall"] = d.get("value_moment_before_paywall") is True
    r["PW-1c_plan_reveal_before"] = d.get("plan_reveal_before_paywall") is True
    r["PW-2a_multipage"] = (d.get("paywall_pages") or 0) >= 2
    r["PW-2b_headline_from_answers"] = d.get("headline_from_answers") is True
    r["PW-2c_simple_benefits"] = d.get("benefit_lines_3_to_5") is True and d.get("comparison_chart") is not True
    td = d.get("trial_days") or 0
    r["PW-3a_trial_timeline_dates"] = d.get("trial_timeline_with_dates") is True
    r["PW-3b_trial_min_7d"] = td >= 7
    r["PW-3c_trial_best_bucket"] = (17 <= td <= 32) or d.get("trial_bucket_exception_recorded") is True
    r["PW-3d_trial_reminder"] = d.get("trial_reminder_offered") is True
    r["PW-4a_plans_preselected"] = (d.get("plans_count") or 0) >= 2 and d.get("one_preselected") is True and d.get("savings_badge") is True
    r["PW-4b_no_trial_toggle"] = d.get("trial_toggle_present") is False
    r["PW-4c_no_onboarding_rating_prompt"] = d.get("rating_prompt_in_onboarding") is False and d.get("review_via_system_after_value") is True
    r["PW-4d_price_prominent_restore"] = d.get("billed_amount_most_prominent") is True and d.get("restore_present") is True
    r["PW-5a_exit_offer_once"] = d.get("exit_offer_on_close") is True and d.get("exit_offer_real_price_named") is True
    r["PW-5b_reshow_and_subscribed_excluded"] = d.get("later_paywall_reshow") is True and d.get("subscribed_never_shown") is True
    r["pass_count"] = sum(1 for v in r.values() if v is True)
    r["fail_count"] = sum(1 for v in r.values() if v is False)
    r["pass"] = r["fail_count"] == 0
    return r
if __name__ == "__main__":
    v = check(json.load(open(sys.argv[1])))
    print(json.dumps(v, indent=2)); sys.exit(0 if v["pass"] else 1)
