#!/usr/bin/env python3
"""Paywall 2026 Winner Gate checker (free, stdlib only, offline).
Source of truth: RevenueDot 'Paywall best practices for 2026' (updated 2026-11-16),
which cites RevenueCat State of Subscription Apps 2026, Adapty 2026, Superwall (40M opens), Lazyweb (40 flows).
Input: JSON state description. Output: PASS/FAIL per gate PW26-1..12, exit 0 only if all pass.
"""
import json, sys

def check(s):
    g = []
    def add(gid, ok, note): g.append((gid, bool(ok), note))
    add("PW26-1", s.get("access_model_decided") and s.get("hard_vs_soft_in_queue"),
        "access model explicitly decided AND hard-vs-current A/B test queued (hard median D35 10.7% vs freemium 2.1%, RevCat 2026)")
    add("PW26-2", (s.get("quiz_steps") or 0) >= 10 and s.get("quiz_one_per_screen") and s.get("quiz_personalized"),
        "quiz >=10 steps, one question per screen, personalized (Lazyweb median paywall at step 11 of 17.2)")
    add("PW26-3", s.get("plan_reveal_before_paywall"),
        "plan-reveal / value-recap screen immediately before paywall (not a generic screen; Lazyweb 28/40 had generic = anti-pattern)")
    add("PW26-4", (s.get("paywall_pages") or 0) >= 2,
        "paywall is multi-page (Superwall 40M opens: 12.41% multi-page vs 9.07% single-page)")
    add("PW26-5", s.get("trial_timeline_shown") and not s.get("trial_toggle_used"),
        "trial shown as timeline (today/reminder/charge date) AND no trial toggle (Apple rejects toggles since mid-Jan 2026, guideline 3.1.2)")
    add("PW26-6", (s.get("trial_days") or 0) >= 17 or s.get("long_trial_test_queued"),
        "trial 17-32 days (RevCat median trial-to-paid 42.5%) or a longer-trial test is queued (<=4 days = 25.5%)")
    add("PW26-7", (s.get("plans_count") or 0) >= 2 and bool(s.get("preselected_plan")) and s.get("billed_amount_most_prominent"),
        ">=2 plans, one pre-selected, billed amount is the most prominent price (Apple requirement)")
    add("PW26-8", s.get("exit_offer_once") and s.get("exit_offer_real_price"),
        "exactly one exit offer on close, real price/period named (Superwall: discounted post-cancel offers = 17% of revenue across 18 cos; scrutiny risk if mislabeled)")
    add("PW26-9", not s.get("custom_review_prompt_in_onboarding"),
        "no custom rating prompt in onboarding (Apple 5.6.3; use Apple prompt after a value moment only)")
    add("PW26-10", s.get("subscribed_hidden"),
        "paywall never shown to subscribed users")
    add("PW26-11", s.get("judge_metric_rpi"),
        "experiments judged on revenue per install first, conversion/renewal as explanation (Rocketship/RevenueCat practice)")
    add("PW26-12", s.get("structure_before_price"),
        "experiment order is structural before price (Adapty win rates: trial 59.6% / plan-duration 58.7% LTV vs price 45.5%)")
    return g

def main():
    path = sys.argv[1]
    s = json.load(open(path))
    gates = check(s)
    fails = [x for x in gates if not x[1]]
    for gid, ok, note in gates:
        print(f"{'PASS' if ok else 'FAIL'} {gid}: {note}")
    print(f"TOTAL: {len(gates)-len(fails)}/{len(gates)} passed")
    sys.exit(0 if not fails else 1)

if __name__ == "__main__":
    main()
