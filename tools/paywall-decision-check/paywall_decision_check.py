#!/usr/bin/env python3
"""paywall-decision-check — Paywall Decision Gate (PD-1..PD-16).
PD-13..PD-16 (added 2026-11-22) come from ShotCanvas "Hard paywall or freemium is the wrong first question" (2026-11-06, full-text read) summarising RevenueCat State of Subscription Apps 2026 (115,000+ apps, $16B+): the model gap (hard 10.7% vs freemium 2.1% D35, RPI $3.09 vs $0.38 D60, 1yr retention 27% vs 28% negligible) is smaller than the spread inside each model (hard range 4.2% to top-10% 38.7%; top-quartile freemium 4.5% beats hard bottom), so the deciding question is WHEN value becomes legible: before use / after user input / when others are there. Freemium: 23% of conversions arrive at week 6+, so a 30-day judgement window misses ~a quarter; gate the repeat-value output (exports/history/projects), let the full job complete once, show the limit before it bites. Hard: onboarding must show the product working on the user's own input before price, and the store listing must carry the promise alone. The value_legibility section is optional/backward-compatible: absent = WARN unknown + PARTIAL exit 2, never a pass.
Sources: Snapp AI hard-vs-freemium 2026 (Adapty/RevenueCat/Superwall data),
FirstApp 6 decisions (Adapty 2026). Free: Python stdlib only.
Input: JSON state description. Exit 0 = all pass, 1 = any fail."""
import json, sys
CHECKS = [
 ("PD-1","category_fit_documented","Category fit for hard vs soft is documented (habit/wellness -> soft onboarding paywall is the documented fit, not the hard default)"),
 ("PD-2","denominator_declared","Every benchmark is recorded with its denominator (downloads vs paywall views) and benchmarks are never mixed"),
 ("PD-3","combined_trial_direct_judgement","Hard/soft is judged on trials + direct purchases combined (hard: +48% trial starts, -33% direct purchases), never on trial starts alone"),
 ("PD-4","volume_threshold_or_low_volume_mode","Formal A/B requires >=200 subscriptions per variant, OR low-volume mode is declared (structural no-downside changes + before/after cohorts, no formal test)"),
 ("PD-5","structural_before_visual","Test order is structural (model/plans/trial/price) before visual/copy"),
 ("PD-6","later_paywall_retained","A later / contextual paywall is retained alongside the onboarding paywall (later paywalls ~38% of subscription revenue)"),
 ("PD-7","day0_concentration_measured","Day-0 concentration is measured (trial starts and first purchases on install day)"),
 ("PD-8","hard_disclosure_if_hard","If hard: store page discloses subscription required and App Review notes explain the model"),
 ("PD-9","plan_count_decision_recorded","Plan-count decision is recorded against the 2-plan winner data (owner overrides are recorded as overrides, not silently kept)"),
 ("PD-10","trial_length_decision_recorded","Trial-length decision is recorded against 17-32d vs 3-7d data and aligned to billing cycle / time-to-aha"),
 ("PD-11","experiment_ledger_and_cadence","Experiments are counted in a ledger with order logged (cadence is tracked; 50+ experiments / regular testing is the winner pattern)"),
 ("PD-12","higher_price_test_considered","A +30% higher-price segment test was considered before any visual redesign"),
]
def main(path):
    s=json.load(open(path))
    fails=[]; partial=False
    for gid,key,desc in CHECKS:
        ok = s.get(key) is True
        print(f"{'PASS' if ok else 'FAIL'} {gid} {desc}")
        if not ok: fails.append(gid)
    vl = s.get("value_legibility")
    if vl is None:
        print("WARN PD-13..PD-16 value_legibility section not recorded (unknown, not a pass)")
        partial=True
    else:
        def req(cond,gid,desc):
            print(f"{'PASS' if cond else 'FAIL'} {gid} {desc}")
            if not cond: fails.append(gid)
        cls = vl.get("legibility_class")
        req(cls in ("before_use","after_input","when_others") and vl.get("legibility_evidence_recorded") is True and vl.get("class_recorded_before_model_decision") is True,
            "PD-13","Value-legibility class (before_use / after_input / when_others) is recorded with evidence BEFORE the model decision (the deciding question is when value shows up, not hard vs freemium)")
        model = vl.get("model")
        if model in ("freemium","soft"):
            req((vl.get("judgement_window_days") or 0) >= 42 and vl.get("late_conversion_share_tracked") is True,
                "PD-14","Freemium is judged on a >=42-day window with the late-conversion share tracked (23% of freemium conversions arrive at week 6+; a 30-day read misses ~a quarter)")
            req(vl.get("gates_repeat_value_not_first_experience") is True and vl.get("full_job_completes_once_before_limit") is True and vl.get("limit_shown_before_it_bites") is True,
                "PD-15","Freemium gates the repeat-value output, not the first experience: the full job completes once before the limit, and the limit is shown (counter) before it bites, never as a mid-task wall")
            print("PASS PD-16 not applicable (model is not hard)")
        elif model == "hard":
            print("PASS PD-14 not applicable (model is not freemium/soft)")
            print("PASS PD-15 not applicable (model is not freemium/soft)")
            req(vl.get("onboarding_shows_product_on_own_input_before_price") is True and vl.get("store_listing_carries_promise_alone") is True,
                "PD-16","Hard paywall earns the ask: onboarding shows the product working on the user's own input before price appears, and the store listing carries the promise on its own")
        else:
            req(False,"PD-14","model in value_legibility is not one of freemium/soft/hard, so the legibility gates cannot be applied")
    total = len(CHECKS) + (0 if vl is None else 4)
    print(f"TOTAL {'FAIL' if fails else ('PARTIAL' if partial else 'PASS')} fails={len(fails)}")
    if fails: return 1
    return 2 if partial else 0
if __name__=="__main__":
    sys.exit(main(sys.argv[1]))
