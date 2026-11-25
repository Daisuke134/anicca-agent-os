#!/usr/bin/env python3
"""Personalized nudge Gate checker (PN-0..PN-7). Stdlib only, deterministic, offline.
Sources (all full-read 2026-11-14 unless noted):
- Airship Optimal Send Time docs: per-user best hour from app opens localized to
  the user's timezone over the last 60 days, balancing the individual pattern
  with a generalized audience model; the general best hour is the fallback for
  dormant / low-activity users; predictions update weekly (Thursdays);
  new users may have no prediction for the first 1-2 weeks and are DROPPED
  if the sender does not handle the missing tag (house rule: never drop,
  always fall back).
- CleverTap 'Personalized Push Notifications: 7 Steps': six tailorable parts
  (content, recommendation, timing, trigger, offer, destination/deep link);
  send-time optimization delivers around each user's usual active hours,
  not one broadcast time per timezone; frequency caps and quiet hours are
  strict boundaries; personalization beyond a first name (behavior-based).
  Duolingo bandit note inside the same article: the best reminder template
  varied by language/segment, so copy choice is per-segment, not global.
- PushPilot teardown of Duolingo (practitioner teardown, secondary):
  state-based orchestration (active / wobbling / at-risk / dormant), tone
  by state, primary reminder in the user's normal session hour, one backup
  90-120 min before the day-end cutoff only if same-day recovery is still
  possible, then cooldown; no late-night pushes unless the user opted in;
  weekly budget = base 2-3 + engagement bonus - fatigue penalty;
  safe baseline 2-4 campaign pushes/week; after 4-5 consecutive ignores,
  reduce cadence and switch to recovery mode; judge on habit recovery +
  opt-out + 30-day retention beside CTR, never CTR alone.
- JITAI framework (Nahum-Shani et al. 2018, via the 2024 scoping review
  PMC11583291, full-read in search + abstract): six components (distal
  outcome, proximal outcome, decision points, tailoring variables,
  intervention options, decision rules); the aim is the right type/amount
  of support at the right time, including providing NOTHING at the wrong
  times; receptivity is the transient ability/willingness to receive and
  use support. HeartSteps (Klasnja et al. 2019, via Levelr summary):
  suggestions raised 30-min step counts by 66% early, then faded --
  habituation must be monitored, not assumed away.
House product direction (2026-11-14, MEMORY): the target form is a nudge
tailored per person -- timing AND wording differ by person -- tailored from
(1) the person's measured reaction history and (2) their onboarding answers.
House rule (2026-11-14): a found best practice beats an original idea,
including the founder's; this checker encodes the found practices above.
"""
import json, sys

REQUIRED_STATES = {"active", "wobbling", "at-risk", "dormant"}

def check(d):
    fails, warns = [], []
    # PN-0 existence + JITAI six components recorded
    if d.get("personalized_implemented") is not True:
        fails.append("PN-0: per-person personalized nudge is not implemented")
    jitai = d.get("jitai") or {}
    for k, label in [("distal_outcome_recorded", "distal outcome"),
                     ("proximal_outcome_recorded", "proximal outcome"),
                     ("decision_points_defined", "decision points"),
                     ("tailoring_variables_recorded", "tailoring variables"),
                     ("intervention_options_recorded", "intervention options"),
                     ("decision_rules_recorded", "decision rules")]:
        if jitai.get(k) is not True:
            fails.append(f"PN-0: JITAI component not recorded: {label}")
    # PN-1 tailoring sources: BOTH onboarding answers and reaction history
    t = d.get("tailoring") or {}
    if t.get("onboarding_answers_used") is not True:
        fails.append("PN-1: onboarding answers do not affect later nudges (collected but unused, or never collected)")
    if t.get("reaction_history_used") is not True:
        fails.append("PN-1: measured reaction history (opens / continues / dismissals per person) does not affect later nudges")
    qc = t.get("onboarding_question_count")
    if qc is None:
        fails.append("PN-1: onboarding question count not recorded")
    elif not (3 <= qc <= 5):
        fails.append(f"PN-1: onboarding question count {qc} outside the 3-5 best-practice range (OB-2) -- too few to tailor on, or too many to finish")
    if t.get("onboarding_answers_stored_per_user") is not True:
        fails.append("PN-1: onboarding answers are not stored per user (cannot tailor without a per-user record)")
    # PN-2 per-user timing (Airship form)
    tm = d.get("timing") or {}
    if tm.get("mode") != "per_user_best_hour":
        fails.append(f"PN-2: send-time mode is {tm.get('mode')!r}, not per_user_best_hour (one broadcast time, or timezone-only, is not per-person timing)")
    w = tm.get("history_window_days")
    if w is None:
        fails.append("PN-2: engagement-history window for best-hour estimation not recorded")
    elif w < 60:
        warns.append(f"PN-2: history window {w}d shorter than the Airship 60-day form (estimate noisier; acceptable only while the user base is young, and must be recorded as such)")
    fb = tm.get("fallback_for_new_or_dormant")
    if fb == "drop":
        fails.append("PN-2: users without a prediction are DROPPED from delivery (Airship documents this failure mode; house rule is to fall back, never drop)")
    elif fb != "general_best_hour":
        fails.append("PN-2: no general-best-hour fallback recorded for new / dormant / low-activity users")
    if tm.get("updates_at_least_weekly") is not True:
        fails.append("PN-2: per-user best-hour predictions do not update at least weekly (Airship form updates weekly)")
    if tm.get("quiet_hours_respected") is not True:
        fails.append("PN-2: local quiet hours are not respected")
    if tm.get("late_night_only_if_opted") is not True:
        fails.append("PN-2: late-night sends are not restricted to users who opted into that schedule")
    # PN-3 per-user content (CleverTap six parts, beyond first name)
    c = d.get("content") or {}
    if c.get("varies_by_user") is not True:
        fails.append("PN-3: message wording is the same for every user (broadcast copy is not a personalized nudge)")
    if c.get("beyond_first_name") is not True:
        fails.append("PN-3: personalization stops at first-name insertion (basic personalization only; behavior-based tailoring is the best-practice form)")
    if c.get("uses_onboarding_goal") is not True:
        fails.append("PN-3: wording does not use the person's onboarding goal / answers")
    if c.get("uses_recent_behavior") is not True:
        fails.append("PN-3: wording does not use the person's recent behavior / state")
    if c.get("destination_deep_link_per_user") is not True:
        fails.append("PN-3: tap destination is not a per-user deep link to the exact content the message refers to")
    # PN-4 decision / state orchestration (Duolingo + JITAI no-send)
    dec = d.get("decision") or {}
    states = set(dec.get("states_defined") or [])
    missing = REQUIRED_STATES - states
    if missing:
        fails.append(f"PN-4: user states missing from the orchestration: {sorted(missing)} (required: active / wobbling / at-risk / dormant)")
    if dec.get("tone_varies_by_state") is not True:
        fails.append("PN-4: tone does not vary by user state (same pressure for fragile and active users creates fatigue and silent disengagement)")
    if dec.get("includes_no_send_option") is not True:
        fails.append("PN-4: decision rule has no 'send nothing' option (JITAI: provide nothing at the wrong times; a system that must always send will send at wrong times)")
    if dec.get("backup_only_if_same_day_recovery_possible") is not True:
        fails.append("PN-4: backup reminder is not limited to cases where same-day recovery is still possible (one primary + one backup, then cooldown)")
    # PN-5 cadence / fatigue guardrails
    cad = d.get("cadence") or {}
    cap = cad.get("weekly_cap_per_user")
    if cap is None:
        fails.append("PN-5: no per-user weekly send cap recorded")
    elif not (2 <= cap <= 4):
        fails.append(f"PN-5: weekly cap {cap}/user outside the 2-4 campaign-push baseline (Duolingo teardown; base allowance 2-3 plus engagement bonus)")
    if cad.get("cooldown_after_consecutive_ignores") is not True:
        fails.append("PN-5: no cooldown / recovery-mode switch after consecutive ignores (4-5 ignored in a row must reduce cadence)")
    if cad.get("fatigue_penalty_applied") is not True:
        fails.append("PN-5: weekly budget has no fatigue penalty (budget = base + engagement bonus - fatigue penalty)")
    # PN-6 measurement: denominators, comparison, harm side
    m = d.get("measurement") or {}
    if m.get("denominator_is_eligible_users") is not True:
        fails.append("PN-6: headline rates do not use eligible users as the denominator")
    if m.get("compares_personalized_vs_broadcast") is not True:
        fails.append("PN-6: personalized sends are never compared against a broadcast / fixed-time control (no evidence the tailoring itself helps)")
    if m.get("tracks_optout_and_retention_with_opens") is not True:
        fails.append("PN-6: judgement reads opens/CTR alone, without opt-out and retention beside it (high CTR with falling retention means over-optimization)")
    if m.get("habituation_monitored") is not True:
        fails.append("PN-6: habituation is not monitored (HeartSteps: the same suggestion faded over weeks; an unmonitored system cannot see its own fade)")
    if m.get("per_user_timing_distribution_recorded") is not True:
        warns.append("PN-6: distribution of per-user best hours across the audience is not recorded (cannot verify timing actually differs by person)")
    # PN-7 causal judgement + ground truth discipline
    ev = d.get("evaluation") or {}
    if ev.get("method") not in ("mrt_wcls", "controlled_cohort"):
        fails.append("PN-7: tailoring effect is not judged by a causal method (MRT with WCLS, or a controlled cohort comparison); naive per-send averages are biased when send probability varies by context")
    if ev.get("real_reaction_is_ground_truth") is not True:
        fails.append("PN-7: simulated / predicted reactions are treated as ground truth (house rule: real measured reactions are ground truth; simulation is scaffolding only)")
    return fails, warns

def main():
    if len(sys.argv) != 2:
        print("usage: personalized_nudge_check.py <fixture.json>"); return 2
    with open(sys.argv[1], encoding="utf-8") as f:
        d = json.load(f)
    fails, warns = check(d)
    for w in warns:
        print(f"WARN: {w}")
    for x in fails:
        print(f"FAIL: {x}")
    print(f"RESULT: {'PASS' if not fails else 'FAIL'} fails={len(fails)} warns={len(warns)}")
    return 0 if not fails else 1

if __name__ == "__main__":
    sys.exit(main())
