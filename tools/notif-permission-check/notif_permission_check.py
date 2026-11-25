#!/usr/bin/env python3
"""Notification permission funnel checker (stdlib only, offline).

Gates (Admiral Media / Airship 2026 benchmarks):
 N-1 denominator: headline opt-in = granted / eligible (not granted / prompt_shown)
 N-2 timing: system prompt must NOT be on first launch; must be after first value
 N-3 soft prompt: a priming/soft prompt must precede the one-shot system prompt
 N-4 benchmark: iOS median 48.85%, Android median 53.3% (Airship 2026, 2025 data)
     rate < median -> BELOW_MEDIAN; rate < median/2 -> BROKEN_PERMISSION_FUNNEL
 N-5 recovery: a later in-app recovery path for opted-out users must exist
     (Airship: +14% average opt-in among opted-out via later in-app message)
 N-6 use-it: opted-in users must receive >=1 push within 90 days
     (permission unused is wasted; flag if sends_within_90d is False)

Extension gates N-7..N-11 (added 2026-11-21, spec:
 hidden_files/notification-permission-reask-protection-spec-2026-11-21.md;
 sources read in full 2026-11-21: Propel push strategy playbook 2026,
 OneSignal prompt-for-push-permissions docs updated 2026-11-12,
 Appfyl notification permission rate guide updated 2026-07-15):
 N-7 re-ask discipline: re-asks go to SOFT-prompt decliners only, via the
     soft prompt, cadence >=7 days or at a moment of obvious need; after a
     SYSTEM denial the only route is system settings (iOS prompt is
     one-shot, Android two) -- a re-prompt design is a fail
 N-8 funnel instrumentation: the 9 permission-funnel events must be
     tracked (permission_eligible, permission_primer_seen,
     system_prompt_requested, permission_allowed, permission_denied,
     notification_settings_opened, first_notification_delivered,
     notification_opened, downstream_action_completed)
 N-9 primer copy: primer must name the specific notification tied to the
     user's own just-completed action; generic copy fails; imitating the
     system dialog fails; buttons must be a direct choice
 N-10 permission protection: per-user weekly cap on non-transactional
     pushes must exist and be <=6 (>6/week = 3.4x uninstall risk in 30d;
     safe band 3-5, so exactly 6 warns); quiet hours defined;
     transactional tier exempt and separate; suppress when the target
     action was already completed within 24h
 N-11 segmentation & control: >=4 cohorts (new / activated / at-risk /
     dormant) or equivalent; a preference center exists and categories
     are separable (not all-or-nothing)

Extension gates N-12..N-14 (added 2026-11-21, spec:
 hidden_files/notification-provisional-upgrade-gate-spec-2026-11-21.md;
 source read in full 2026-11-21: OneSignal prompt-for-push-permissions
 docs, updated 2026-11-12):
 N-12 provisional adoption (iOS): provisional authorization is the
     default starting point on iOS; not using it is a fail. Android n/a.
 N-13 quiet first week: 2-3 high-quality provisional notifications in
     the first week; 0 sends = fail (no evidence to judge), >=4 = warn.
 N-14 upgrade assembly: upgrade ask triggered by a high-signal action
     (opening/acting on a provisional notification, a value action);
     re-show has a cap and a gap (source form: max 20, 2-week gap);
     provisional cohort is measured separately from full-permission
     cohort (state honesty itself remains quiet-check's canonical job).
 provisional (optional): {enabled (bool|null),
   first_week_sends (int|null), upgrade_trigger_high_signal (bool|null),
   upgrade_reshow_capped (bool|null), cohort_measured_separately (bool|null)}
 All N-12..N-14 fields are optional and backward compatible.

Input: JSON file with fields:
 platform ("ios"|"android"), eligible (int), granted (int),
 prompt_shown (int, optional), ask_timing ("after_first_value"|"first_launch"|"before_value"|"unknown"),
 has_soft_prompt (bool|null), has_recovery_path (bool|null), sends_within_90d (bool|null),
 reask (optional): {soft_only (bool|null), cadence_days (int|null),
   at_need_moment (bool|null), system_denied_route ("settings"|"reprompt"|null)},
 funnel_events (optional): list of tracked event names, or null,
 primer (optional): {names_specific_value (bool|null), generic_copy (bool|null),
   imitates_system_dialog (bool|null), buttons_direct_choice (bool|null)},
 protection (optional): {weekly_cap_nontransactional (int|null),
   cap_per_user (bool|null), quiet_hours_defined (bool|null),
   transactional_exempt (bool|null), suppress_if_action_done_24h (bool|null)},
 control (optional): {segments (list|null), preference_center (bool|null),
   categories_separable (bool|null)}
 All N-7..N-11 fields are optional and backward compatible: a missing
 field is an unknown, never a fail; a present value that clearly
 violates a gate is a fail.
Output: JSON verdict. Exit 0 = PASS, 1 = FAIL/BROKEN, 2 = PARTIAL (unknowns present but no hard fail except rate).
"""
import json, sys

BENCH = {"ios": 48.85, "android": 53.3}

def main():
    if len(sys.argv) < 2:
        print("usage: notif_permission_check.py <input.json>"); return 2
    with open(sys.argv[1]) as f:
        d = json.load(f)
    platform = d.get("platform", "ios")
    bench = BENCH.get(platform, 48.85)
    eligible = d.get("eligible", 0)
    granted = d.get("granted", 0)
    prompt_shown = d.get("prompt_shown")
    rate = (granted / eligible * 100) if eligible else 0.0
    prompt_rate = (granted / prompt_shown * 100) if prompt_shown else None
    fails, warns, unknowns = [], [], []
    # N-1
    if prompt_rate is not None and abs(prompt_rate - rate) > 5:
        warns.append(f"N-1 denominator gap: headline {rate:.1f}% (granted/eligible) vs prompt-accept {prompt_rate:.1f}% (granted/prompt_shown) — headline must be the former")
    # N-2
    timing = d.get("ask_timing", "unknown")
    if timing == "first_launch":
        fails.append("N-2 timing: system prompt on first launch spends the one-shot ask before value")
    elif timing == "before_value":
        fails.append("N-2 timing: prompt before first value moment")
    elif timing == "unknown":
        unknowns.append("N-2 timing unknown — real-build read required")
    # N-3
    sp = d.get("has_soft_prompt")
    if sp is False:
        fails.append("N-3 no soft/priming prompt before the one-shot system prompt")
    elif sp is None:
        unknowns.append("N-3 soft prompt presence unknown")
    # N-4
    verdict_rate = "PASS"
    if eligible and rate < bench / 2:
        verdict_rate = "BROKEN_PERMISSION_FUNNEL"
        fails.append(f"N-4 rate {rate:.1f}% < half of {platform} median {bench}% ({bench/2:.1f}%)")
    elif eligible and rate < bench:
        warns.append(f"N-4 rate {rate:.1f}% below {platform} median {bench}%")
    # N-5
    rp = d.get("has_recovery_path")
    if rp is False:
        warns.append("N-5 no recovery path for opted-out users (later in-app message; Airship +14% avg)")
    elif rp is None:
        unknowns.append("N-5 recovery path unknown")
    # N-6
    s90 = d.get("sends_within_90d")
    if s90 is False:
        warns.append("N-6 opted-in users receive no push within 90 days — permission wasted")
    elif s90 is None:
        unknowns.append("N-6 sends-within-90d unknown")
    # N-7 re-ask discipline
    ra = d.get("reask") or {}
    if ra:
        if ra.get("system_denied_route") == "reprompt":
            fails.append("N-7 system-denied users are re-prompted (iOS system prompt is one-shot, Android two; after denial the only route is system settings)")
        elif ra.get("system_denied_route") is None:
            unknowns.append("N-7 route after system denial unknown (must be settings, never a re-prompt)")
        if ra.get("soft_only") is False:
            fails.append("N-7 re-asks are not limited to soft-prompt decliners via the soft prompt")
        elif ra.get("soft_only") is None:
            unknowns.append("N-7 whether re-asks target soft decliners only is unknown")
        cad = ra.get("cadence_days")
        if cad is not None and cad < 7 and ra.get("at_need_moment") is not True:
            fails.append(f"N-7 re-ask cadence {cad}d is an aggressive loop (minimum 7 days between soft re-asks, or only at a moment of obvious need)")
        elif cad is None and ra.get("at_need_moment") is None:
            unknowns.append("N-7 re-ask cadence / need-moment rule unknown")
    else:
        unknowns.append("N-7 re-ask discipline not recorded")
    # N-8 funnel instrumentation
    REQUIRED_EVENTS = ["permission_eligible", "permission_primer_seen",
        "system_prompt_requested", "permission_allowed", "permission_denied",
        "notification_settings_opened", "first_notification_delivered",
        "notification_opened", "downstream_action_completed"]
    fe = d.get("funnel_events")
    if fe is None:
        unknowns.append("N-8 permission-funnel events not recorded (9 events required to read the funnel by cohort)")
    else:
        missing = [e for e in REQUIRED_EVENTS if e not in fe]
        if missing:
            fails.append(f"N-8 funnel events missing: {', '.join(missing)}")
    # N-9 primer copy
    pr = d.get("primer") or {}
    if pr:
        if pr.get("imitates_system_dialog") is True:
            fails.append("N-9 primer imitates the system dialog (deceptive; the primer prepares the decision, the OS prompt grants it)")
        if pr.get("generic_copy") is True or pr.get("names_specific_value") is False:
            fails.append("N-9 primer copy is generic (it must name the specific notification tied to the user's own just-completed action)")
        elif pr.get("names_specific_value") is None:
            unknowns.append("N-9 whether the primer names a specific value is unknown")
        if pr.get("buttons_direct_choice") is False:
            fails.append("N-9 primer buttons are not a direct choice (e.g. 'Get <specific alerts>' / 'Not now')")
        elif pr.get("buttons_direct_choice") is None:
            unknowns.append("N-9 primer button form unknown")
    else:
        unknowns.append("N-9 primer copy not recorded")
    # N-10 permission protection
    pt = d.get("protection") or {}
    if pt:
        cap = pt.get("weekly_cap_nontransactional")
        if cap is None:
            unknowns.append("N-10 weekly non-transactional cap unknown (an uncapped channel burns the permission)")
        elif cap > 6:
            fails.append(f"N-10 weekly non-transactional cap {cap} exceeds 6 (>6/week = 3.4x uninstall risk within 30 days; safe band is 3-5)")
        elif cap == 6:
            warns.append("N-10 weekly cap 6 is the outer edge (safe band is 3-5 non-transactional per week)")
        if pt.get("cap_per_user") is False:
            fails.append("N-10 cap is not per-user (users experience total volume across campaigns, not per-campaign volume)")
        elif pt.get("cap_per_user") is None:
            unknowns.append("N-10 whether the cap is per-user is unknown")
        if pt.get("quiet_hours_defined") is False:
            fails.append("N-10 no quiet hours defined (default floor 21:00-09:00 local unless the user sets a window)")
        elif pt.get("quiet_hours_defined") is None:
            unknowns.append("N-10 quiet hours unknown")
        if pt.get("transactional_exempt") is False:
            warns.append("N-10 transactional tier is not separated from the capped tiers (transactional is exempt; promotional is capped first)")
        elif pt.get("transactional_exempt") is None:
            unknowns.append("N-10 transactional-tier separation unknown")
        if pt.get("suppress_if_action_done_24h") is False:
            warns.append("N-10 no suppression when the target action was already completed within 24h (pushing for a done action trains ignoring)")
        elif pt.get("suppress_if_action_done_24h") is None:
            unknowns.append("N-10 completion suppression unknown")
    else:
        unknowns.append("N-10 send protection (cap / quiet hours) not recorded")
    # N-11 segmentation & control
    ct = d.get("control") or {}
    if ct:
        segs = ct.get("segments")
        if segs is None:
            unknowns.append("N-11 cohort segmentation unknown (minimum: new / activated / at-risk / dormant)")
        elif len(segs) < 4:
            fails.append(f"N-11 only {len(segs)} cohort(s) defined (minimum viable segmentation is 4: new, activated, at-risk, dormant; each gets its own triggers and cap)")
        if ct.get("preference_center") is False:
            fails.append("N-11 no preference center (permission becomes all-or-nothing, so a user who dislikes one category opts out of everything)")
        elif ct.get("preference_center") is None:
            unknowns.append("N-11 preference center unknown")
        if ct.get("categories_separable") is False:
            fails.append("N-11 notification categories are not separable (transactional and promotional must not share one setting)")
        elif ct.get("categories_separable") is None:
            unknowns.append("N-11 category separability unknown")
    else:
        unknowns.append("N-11 segmentation / preference center not recorded")
    # N-12..N-14 provisional adoption & upgrade (iOS only)
    pv = d.get("provisional") or {}
    if platform == "ios":
        if pv:
            if pv.get("enabled") is False:
                fails.append("N-12 provisional authorization is not the iOS starting point (OneSignal: provisional is the default starting point and often the highest-conversion path; users judge real content, not a hypothetical)")
            elif pv.get("enabled") is None:
                unknowns.append("N-12 provisional adoption unknown")
            sends = pv.get("first_week_sends")
            if sends is None:
                unknowns.append("N-13 first-week provisional sends unknown (source form: 2-3 high-quality in week 1)")
            elif sends == 0:
                fails.append("N-13 zero provisional notifications in the first week (users get no real content to judge Keep on)")
            elif sends >= 4:
                warns.append(f"N-13 {sends} provisional sends in week 1 exceeds the 2-3 source form (even quiet delivery can crowd the judgement)")
            if pv.get("upgrade_trigger_high_signal") is False:
                fails.append("N-14 upgrade ask is not tied to a high-signal action (opening/acting on a provisional notification, or a completed value action)")
            elif pv.get("upgrade_trigger_high_signal") is None:
                unknowns.append("N-14 upgrade trigger unknown")
            if pv.get("upgrade_reshow_capped") is False:
                fails.append("N-14 upgrade re-show has no cap/gap (source form: max 20 shows, 2-week gap)")
            elif pv.get("upgrade_reshow_capped") is None:
                unknowns.append("N-14 upgrade re-show cap unknown")
            if pv.get("cohort_measured_separately") is False:
                fails.append("N-14 provisional cohort is mixed into the full-permission cohort (headline opt-in becomes uninterpretable; state honesty is quiet-check's job, separation is this gate's)")
            elif pv.get("cohort_measured_separately") is None:
                unknowns.append("N-14 provisional cohort separation unknown")
        else:
            unknowns.append("N-12..N-14 provisional adoption/upgrade not recorded (iOS)")
    # Reachable estimate per 100 installs
    reachable_per_100 = round(rate, 1)
    gap_users_per_100 = round(bench - rate, 1) if eligible else None
    if fails:
        verdict = "FAIL"
        code = 1
    elif unknowns:
        verdict = "PARTIAL"
        code = 2
    elif warns:
        verdict = "PASS_WITH_WARNINGS"
        code = 0
    else:
        verdict = "PASS"
        code = 0
    out = {
        "platform": platform, "benchmark_median_pct": bench,
        "eligible": eligible, "granted": granted,
        "headline_optin_pct": round(rate, 2),
        "prompt_accept_pct": round(prompt_rate, 2) if prompt_rate is not None else None,
        "reachable_per_100_installs": reachable_per_100,
        "gap_to_median_per_100_installs": gap_users_per_100,
        "rate_verdict": verdict_rate,
        "fails": fails, "warnings": warns, "unknowns": unknowns,
        "verdict": verdict,
    }
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return code

if __name__ == "__main__":
    sys.exit(main())
