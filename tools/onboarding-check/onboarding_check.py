#!/usr/bin/env python3
"""Onboarding flow Gate checker (OB-0..OB-12). Stdlib only, deterministic, offline.
Source pattern: Built by Foundry '7 Onboarding Steps That Convert Creator App Trials'
(citing RevenueCat SOSA 2025, Adapty 2025, Digia Engage Q2 2025 - secondary benchmarks).
Adaptations recorded in spec: face-led opening NOT copied (face-dependent form is
disqualified by house winner rules); annual-default kept as recorded warning only
(soft-paywall decision 2026-11-13 governs)."""
import json, sys

def check(d):
    fails, warns = [], []
    # OB-0 recorded screen-by-screen
    screens = d.get("screens")
    if not isinstance(screens, list) or len(screens) < 4:
        fails.append("OB-0: screen-by-screen flow not recorded (>=4 screens with order)")
    if d.get("flow_duration_seconds") is None:
        fails.append("OB-0: total flow duration not recorded")
    # OB-1 duration 90-180s to paywall view
    dur = d.get("flow_duration_seconds")
    if isinstance(dur,(int,float)) and not (90 <= dur <= 180):
        fails.append(f"OB-1: flow duration {dur}s outside 90-180s budget")
    qw = d.get("quick_win_minutes")
    if qw is None or not (2 <= qw <= 4):
        fails.append("OB-4: no quick win of 2-4 minutes recorded in session 1")
    if d.get("quick_win_before_paywall") is not True:
        fails.append("OB-4/OB-5: quick win is not before the paywall")
    # OB-2 quiz 3-5, outcome-shaping, no data-collection first
    q = d.get("quiz_questions")
    if q is None or not (3 <= q <= 5):
        fails.append("OB-2: quiz question count not in 3-5 range (or unrecorded)")
    if d.get("quiz_first_is_data_collection") is True:
        fails.append("OB-2: first quiz question is data collection (email/age), not outcome-shaping")
    if d.get("quiz_answers_used_in_paywall_copy") is not True:
        fails.append("OB-5: paywall copy does not reference quiz answers / personalized plan")
    # OB-3 single proof screen, real claims only
    proof = d.get("proof_screen") or {}
    if not proof.get("present"):
        fails.append("OB-3: no proof screen before the ask")
    else:
        if not proof.get("specific_number"): fails.append("OB-3: proof screen lacks a specific number")
        if proof.get("testimonial_count") != 1: fails.append("OB-3: proof screen must carry exactly one testimonial")
        if not proof.get("goal_matched_stat"): fails.append("OB-3: proof screen lacks a stat matched to the picked goal")
        if not proof.get("rating_real"): fails.append("OB-3: proof rating not attested as the real store rating")
    # OB-5 paywall position screen 5-6
    pos = d.get("paywall_screen_position")
    if pos is None or not (5 <= pos <= 6):
        fails.append("OB-5: paywall position not screen 5-6 (or unrecorded)")
    # OB-6 trial framed as progress
    if d.get("trial_framing") != "progress":
        fails.append("OB-6: trial framed as countdown (or unrecorded), not progress (streak/roadmap/next session)")
    # OB-7 day2 push rules
    push = d.get("day2_push") or {}
    if not push.get("enabled"): fails.append("OB-7: no Day 2 welcome push")
    else:
        if not push.get("same_time_as_session1"): fails.append("OB-7: Day 2 push not sent at session-1 time")
        if not push.get("names_next_session"): fails.append("OB-7: Day 2 push does not name the next session")
        if (push.get("pushes_per_day") or 99) > 1: fails.append("OB-7: more than 1 push per day")
    # OB-8 five metrics measured
    m = d.get("metrics") or {}
    for k in ["completion_rate","trial_start_rate","day2_retention","trial_to_paid","annual_share"]:
        if m.get(k) is None: fails.append(f"OB-8: metric {k} not measured")
    if m.get("day2_open_rate") is not None and m["day2_open_rate"] < 0.25:
        warns.append("OB-7: Day 2 open rate below 25% - onboarding leaking (source threshold)")
    if d.get("annual_default") is None:
        warns.append("OB-5: annual-default choice not recorded (house soft-paywall decision governs; record the choice)")
    # OB-9..OB-12 length experiment (Everlove/RevenueCat 2026-11-19): optional section;
    # absent = warns (not recorded, not a pass), present-but-wrong = fails.
    le = d.get("length_experiment")
    if le is None:
        warns.append("OB-9: no length_experiment record - leak-first diagnosis not recorded (not a pass)")
        warns.append("OB-10: no length_experiment record - both-halves measurement not recorded")
        warns.append("OB-11: no length_experiment record - removed-question disposition not recorded")
        warns.append("OB-12: no length_experiment record - concurrent-test guard not recorded")
    else:
        # OB-9 diagnose the leak before touching length
        if le.get("bottleneck_stage") not in ("onboarding","paywall"):
            fails.append("OB-9: bottleneck_stage not diagnosed as onboarding|paywall before length change")
        if le.get("completion_rate_measured") is not True or le.get("paywall_viewer_conversion_measured") is not True:
            fails.append("OB-9: leak diagnosis must measure BOTH completion rate and conversion per paywall viewer first")
        if le.get("length_decided_before_diagnosis") is True:
            fails.append("OB-9: length was decided before the leak diagnosis (Everlove: length is not the first decision)")
        # OB-10 measure both halves separately; decision on joint metric, never completion alone
        if le.get("reports_completion_and_viewer_trial_separately") is not True:
            fails.append("OB-10: completion and trial-start-per-paywall-viewer must be reported separately (one up / other down is the normal result)")
        if le.get("decision_metric") != "initial_conversion_per_registered":
            fails.append("OB-10: decision metric must be initial_conversion_per_registered, not completion alone")
        if le.get("plan_mix_checked") is not True:
            fails.append("OB-10: plan mix / LTV per registered user not checked (fewer buyers may be worth more)")
        # OB-11 removed questions: later, not never; heavy questions not before first value
        rq = le.get("removed_questions") or []
        for q in rq:
            if q.get("disposition") not in ("moved_after_value","dropped_with_reason"):
                fails.append(f"OB-11: removed question {q.get('id')} has no disposition (moved_after_value|dropped_with_reason)")
        if le.get("heavy_questions_before_first_value") is True:
            fails.append("OB-11: heavy/emotional questions sit before the user has experienced any value")
        # OB-12 single variable: no concurrent paywall test, or equal exposure recorded
        if le.get("concurrent_paywall_test") is True and le.get("equal_exposure_recorded") is not True:
            fails.append("OB-12: concurrent paywall test without equally-exposed window recorded (length is no longer the only difference)")
    return fails, warns

def main():
    with open(sys.argv[1]) as f: d=json.load(f)
    fails,warns=check(d)
    for w in warns: print("WARN:",w)
    for x in fails: print("FAIL:",x)
    print(f"RESULT: {'PASS' if not fails else 'FAIL'} fails={len(fails)} warns={len(warns)}")
    sys.exit(0 if not fails else 1)
if __name__=="__main__": main()
