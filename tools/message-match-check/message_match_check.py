#!/usr/bin/env python3
"""message-match-check: Paywall Message-Match Gate MM-0..MM-5 (18 checks).
Stdlib only, offline, free. Exit 0=PASS, 1=FAIL.
Source (full read 2026-11-23): RevenueDot, Paywall best practices for 2026
https://revenuedot.app/blog/paywall-best-practices-2026
Spec: hidden_files/paywall-message-match-gate-spec-2026-11-23.md
"""
import json, sys

CHECKS = [
    ("MM-0", "answers_collected", "onboarding answers are not collected"),
    ("MM-0", "answer_headline_map_recorded", "answer->headline map not recorded"),
    ("MM-0", "paywall_surfaces_inventoried", "paywall surfaces not inventoried"),
    ("MM-1", "headline_uses_user_answer", "paywall headline does not use the user's answers"),
    ("MM-1", "benefits_reflect_answers", "benefit lines do not reflect the answers"),
    ("MM-1", "fallback_defined_no_fabrication", "no generic fallback defined / personalization may be fabricated"),
    ("MM-2", "plan_reveal_before_paywall", "no plan reveal immediately before the paywall"),
    ("MM-2", "reveal_specific_not_generic", "pre-paywall screen is generic, not answer-specific"),
    ("MM-2", "reveal_uses_answers", "plan reveal does not use the answers"),
    ("MM-3", "value_first_or_multipage", "paywall is neither value-first nor multi-page"),
    ("MM-3", "single_preselected_plan", "preselected plan is not exactly one"),
    ("MM-3", "trial_timeline_with_dates", "trial is not shown as a timeline with dates"),
    ("MM-4", "no_trial_toggle", "free-trial toggle present (Apple 3.1.2 rejection risk, 2026)"),
    ("MM-4", "no_rating_prompt_in_onboarding", "rating prompt inside onboarding (Apple 5.6.3 risk)"),
    ("MM-4", "billed_amount_most_prominent", "billed amount is not the most prominent price"),
    ("MM-5", "variant_id_logged", "paywall variant ID not logged"),
    ("MM-5", "conversion_read_by_answer_segment", "conversion not read by answer segment"),
    ("MM-5", "structure_tested_before_price", "price is tested before structure"),
]

def main():
    if len(sys.argv) < 2:
        print("usage: message_match_check.py <state.json>"); return 2
    s = json.load(open(sys.argv[1]))
    fails = [f"{g}: {m}" for g, k, m in CHECKS if s.get(k) is not True]
    passed = len(CHECKS) - len(fails)
    print(f"{'PASS' if not fails else 'FAIL'} {passed}/{len(CHECKS)}")
    for f in fails: print(" -", f)
    return 0 if not fails else 1

if __name__ == "__main__":
    sys.exit(main())
