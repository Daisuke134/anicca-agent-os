#!/usr/bin/env python3
"""Review-prompt gate checker (stdlib only, offline, free).

Gates (sources in spec review-prompt-eligibility-denominator-spec-2026-11-12.md;
 RP-6..RP-9 added 2026-11-22, spec review-prompt-budget-api-gate-spec-2026-11-22.md):
 RP-1 placement: never in onboarding / first launch / first session (Guideline 5.6.3, RevenueCat 2026)
 RP-2 dialog: system dialog only; no gating/filtering, no incentive, no custom star dialog
 RP-3 eligibility bundle: >=3 distinct days or >=3 sessions AND local cooldown >=90 days
 RP-4 trigger: immediately after a completed core-value event; not timer/button/auto-step
 RP-5 denominator: judge calls against ELIGIBLE users only. eligible==0 -> 0 calls is expected.
      System display itself is unobservable from the app side (Apple decides); count calls, not displays.
Input: JSON file path as argv[1]. Exit 0 = PASS/EXPECTED/ABSENT-noted, 1 = FAIL/BROKEN.
"""
import json, sys

def main():
    with open(sys.argv[1]) as f:
        c = json.load(f)
    fails, warns, notes = [], [], []
    placement = c.get("placement")
    if placement in ("onboarding", "first_launch", "first_session"):
        fails.append(f"RP-1: placement={placement} is inside onboarding/first-run (5.6.3 rejection pattern)")
    elif placement == "none":
        notes.append("RP-1: no review prompt implemented (ABSENT) - no rejection risk, no rating inflow either")
    elif placement == "after_value":
        notes.append("RP-1: placement=after_value OK")
    else:
        warns.append(f"RP-1: placement unknown/unread ({placement}) - do not assert compliance")
    if c.get("dialog") == "custom":
        fails.append("RP-2: custom star dialog is not a substitute for the system dialog (5.6.1)")
    if c.get("gating"):
        fails.append("RP-2: sentiment gating (routing unhappy users away) is review gating - prohibited")
    if c.get("incentive"):
        fails.append("RP-2: incentive offered for a review - prohibited")
    if c.get("dialog") == "system":
        notes.append("RP-2: system dialog OK")
    days, sessions, cd = c.get("min_distinct_days"), c.get("min_sessions"), c.get("cooldown_days")
    if placement not in ("none", None):
        if not ((days or 0) >= 3 or (sessions or 0) >= 3):
            fails.append(f"RP-3: eligibility too thin (distinct_days={days}, sessions={sessions}); need >=3 of one")
        if cd is None:
            warns.append("RP-3: cooldown unread/unknown")
        elif cd < 90:
            fails.append(f"RP-3: local cooldown {cd}d < 90d (Apple budget is 3 displays / 365d)")
        else:
            notes.append(f"RP-3: eligibility bundle OK (cooldown {cd}d)")
    trig = c.get("trigger_event")
    if placement not in ("none", None):
        if trig == "value_completed":
            notes.append("RP-4: trigger=value_completed OK")
        elif trig in ("auto_step", "timer", "button"):
            fails.append(f"RP-4: trigger={trig} is not a completed-value moment")
        else:
            warns.append(f"RP-4: trigger unknown ({trig})")
    for k in ("crash_guard", "after_error_block", "stacking_block"):
        if c.get(k) is None and placement not in ("none", None):
            warns.append(f"RP-4b: {k} unconfirmed in source record - not asserted either way")
    b = c.get("budget") or {}
    if placement not in ("none", None) and b:
        api = b.get("api")
        if api == "deprecated":
            fails.append("RP-6: API is SKStoreReviewController (deprecated iOS 18); use RequestReviewAction / AppStore.requestReview(in:)")
        elif api == "current":
            notes.append("RP-6: current API OK")
        else:
            warns.append(f"RP-6: api unknown ({api})")
        if b.get("once_per_version") is False:
            fails.append("RP-7: no once-per-version guard - same release can re-ask")
        elif b.get("once_per_version") is True:
            notes.append("RP-7: once-per-version guard OK")
        else:
            warns.append("RP-7: once_per_version unknown")
        sd = b.get("settle_delay_sec")
        if sd is not None and sd < 1:
            warns.append(f"RP-7: settle delay {sd}s < 1s - prompt covers the success screen before it registers")
        if b.get("production_timing_ab_test"):
            fails.append("RP-8: A/B testing prompt timing on production calls burns the 3/365d budget; test logic in dev builds instead")
        if b.get("tested_in_dev") is False:
            warns.append("RP-8: prompt logic not verified in dev builds (TestFlight never shows the prompt; absence there is not a bug)")
        if b.get("settings_rate_row") is False:
            fails.append("RP-9: no Settings Rate row (write-review link) - the only prompt path with no cap and immune to the user-level opt-out")
        elif b.get("settings_rate_row") is True:
            notes.append("RP-9: settings Rate row OK")
        else:
            warns.append("RP-9: settings_rate_row unknown")
    elif placement not in ("none", None):
        warns.append("RP-6..RP-9: no budget section - API currency / per-version / dev-test / rate-row unmeasured (unknown, not pass)")
    coh = c.get("cohort") or {}
    elig, calls = coh.get("eligible"), coh.get("calls")
    verdict = "PASS"
    if fails:
        verdict = "FAIL"
    if elig is not None and calls is not None:
        if elig == 0:
            notes.append("RP-5: eligible=0 -> 0 calls is EXPECTED under the eligibility bundle, not a broken funnel")
            if verdict == "PASS": verdict = "PASS_EXPECTED_ZERO"
        elif calls == 0:
            fails.append(f"RP-5: eligible={elig} but calls=0 -> BROKEN_NEVER_CALLED")
            verdict = "FAIL"
        else:
            notes.append(f"RP-5: calls/eligible = {calls}/{elig} = {calls/elig:.2f} (system display is decided by Apple and unobservable app-side; never report displays)")
    else:
        warns.append("RP-5: eligible and/or calls unmeasured -> a funnel count of 'displays=0' cannot be judged broken or healthy")
    if placement == "none" and verdict == "PASS":
        verdict = "ABSENT"
    print(json.dumps({"app": c.get("app"), "verdict": verdict, "fails": fails, "warnings": warns, "notes": notes}, ensure_ascii=False, indent=2))
    sys.exit(1 if verdict == "FAIL" else 0)

if __name__ == "__main__":
    main()
