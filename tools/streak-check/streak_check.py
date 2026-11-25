#!/usr/bin/env python3
"""streak-check: deterministic gate for daily-return / streak design in subscription apps.
Stdlib only, offline, free. Sources (read in full 2026-11-13):
- RevenueCat, Curse of the first renewal (State of Subscription Apps 2026 data):
  first renewal is where most subscribers are lost (weekly drop 42-65%, monthly 39-58%,
  annual 60-77%); activation windows are weekly=first 5 days, monthly=first 2 weeks,
  annual=first month (embed by day 90); find the First Renewal Predictor (FRP) by
  comparing early behaviour of survivors vs churners; Duolingo's 7-day streak is its FRP;
  re-engagement at 23.5h after last session beat other timings; messages must be
  value-oriented (celebrate / next achievement), never generic "please come back".
  https://www.revenuecat.com/blog/growth/first-renewal-churn
- Therr, The Gamification of Habits (2026-08-25, summarising Duolingo's published A/B):
  lowering the streak bar to ONE lesson: D14 retention +3.3%, daily learners on a streak
  +10.5% (+19% new learners); 7-day streak holders return next day at 2.4x; streak freezes /
  earn-back absorb a miss; points economies farmable without the behaviour backfire
  (overjustification, d~-0.36). Six rules: bar at floor / streak not score / build in the
  miss / visible to 2-5 specific people / metric inseparable from behaviour / renew on a cycle.
  https://www.therr.app/blog/2026/8_25_2026_gamification_of_habits.html
- In-house affirmation-streak-habit-spec-2026-11-05 encodes the same rules for Anicca
  (1 completed affirmation/day, free weekly skip, no paid freeze, no points economy).
Exit 0 = PASS, 1 = FAIL. Warnings do not fail.
Extension S-8..S-13 (2026-11-21, post-break / compassionate streak):
- DuolingoGuides, Super Duolingo Streak Repair (updated 2026-11): freeze is BEFORE a miss,
  repair is AFTER a break, repair window is short (a day or two), short streaks get a free
  lesson offer, Super gets one free repair/month, Revival Event restored a lost 30+ streak
  for 3 consecutive lessons free. Anicca takes the shape, not the price: repair must be free
  and earned back with the core action, never paid/gems (suffering app; paid freeze already
  banned in S-3). https://duolingoguides.com/super-duolingo-streak-repair/
- Pheidi, Fitness App Streaks (full read 2026-11-21): loss aversion ~2x, JMIR 2024 shame/guilt,
  BJHP 2025 (Sheen et al.) guilt/anxiety/compulsive checking, Duolingo freezes -21% churn in
  at-risk users, consistency windows (5 of 7) beat daily chains, never punish a broken streak,
  celebrate the activity not the chain, progress must accumulate not reset.
  https://pheidi.training/articles/streak-systems-fitness-apps/
New input section "post_break" is optional for backward compatibility: absent = WARN
(PARTIAL, not recorded), present = S-8..S-13 are judged deterministically.
Input JSON: {app, streak_implemented, qualifying_action, full_goal_required,
 counter_visible_on_home, increments_without_core_action, forgiveness:{type, paid},
 reminder:{timing_basis, hours_after_last, message_style},
 activation_window_days_by_plan:{weekly, monthly, annual},
 frp:{defined, measured_from_survivors_vs_churners, denominator},
 milestones_days:[...], points_economy_farmable, store_copy_claims_no_streaks}
"""
import json, sys

def check(d):
    fails, warns = [], []
    if not d.get("streak_implemented"):
        fails.append("S-0 no streak / daily-return counter implemented in code (a spec since 2026-11-05 without code retains nobody)")
    if d.get("qualifying_action") != "one_core_action_complete":
        fails.append(f"S-1 qualifying action is {d.get('qualifying_action')!r}, not one completed core action (Duolingo A/B: bar at the floor — one lesson — D14 +3.3%)")
    if d.get("full_goal_required"):
        fails.append("S-1 full daily goal is required to extend the streak (the exact pre-A/B Duolingo design that lost; goal progress must be shown separately)")
    if not d.get("counter_visible_on_home"):
        fails.append("S-2 streak counter is not visible on the home / core screen (an unseen counter recruits no loss aversion)")
    if d.get("increments_without_core_action"):
        fails.append("S-2 counter can increment without completing the core action (metric separated from behaviour = farmable, overjustification risk)")
    f = d.get("forgiveness") or {}
    if not f.get("type") or f.get("type") == "none":
        fails.append("S-3 no forgiveness mechanic (freeze / earn-back / weekly skip): one miss resets to zero and the break day becomes the quit day")
    if f.get("paid"):
        fails.append("S-3 forgiveness is paid (monetising the miss splits the habit by paywall; in-house spec forbids paid freeze)")
    r = d.get("reminder") or {}
    if r.get("message_style") == "generic_please_return" or not r.get("message_style"):
        fails.append("S-4 reminder is generic ('please come back') or undefined (RevenueCat: value-oriented only — celebrate progress / name the streak / next achievement)")
    h = r.get("hours_after_last")
    if r.get("timing_basis") == "hours_after_last" and h is not None and not (20 <= h <= 26):
        fails.append(f"S-4 reminder fires {h}h after last session (Duolingo's tested optimum is ~23.5h, just before the habit's natural repeat time)")
    if r.get("timing_basis") not in ("hours_after_last", "user_chosen_time", "streak_end_of_day"):
        fails.append(f"S-4 reminder timing basis {r.get('timing_basis')!r} is not anchored (use ~23.5h after last completion, the user's chosen time, or end-of-streak-day)")
    w = d.get("activation_window_days_by_plan") or {}
    for plan, want in (("weekly", 5), ("monthly", 14), ("annual", 30)):
        if w.get(plan) != want:
            fails.append(f"S-5 activation window for {plan} is {w.get(plan)!r}, not {want} days (RevenueCat: weekly 5d / monthly 14d / annual 30d, embed by day 90)")
    frp = d.get("frp") or {}
    if not frp.get("defined"):
        fails.append("S-5 no First Renewal Predictor defined (for a daily app: the 7-day streak — Duolingo's FRP, 2.4x next-day return)")
    if not frp.get("measured_from_survivors_vs_churners"):
        fails.append("S-5 FRP is not derived by comparing survivors vs churners (a guessed activation metric is not a predictor)")
    if frp.get("denominator") != "activated_users":
        fails.append(f"S-5 FRP denominator is {frp.get('denominator')!r}, not activated users (rating the streak over all installs hides the predictor in onboarding drop-off)")
    ms = d.get("milestones_days") or []
    if 7 not in ms:
        fails.append("S-6 no 7-day milestone (the first meaningful streak milestone and the FRP threshold itself)")
    if d.get("points_economy_farmable"):
        fails.append("S-6 a points/XP economy can be farmed without the core action (metric replaces the goal; overjustification d~-0.36)")
    if d.get("store_copy_claims_no_streaks") and d.get("streak_implemented"):
        fails.append("S-7 store copy claims 'no streaks' while the product implements a streak (positioning and product contradict; pick one and make both surfaces agree)")
    pb = d.get("post_break")
    if pb is None:
        warns.append("S-8..S-13 post_break section not recorded (repair / consistency window / no-punishment / hard-day grace / timezone honesty / opt-out are unjudged, PARTIAL)")
    else:
        if not pb.get("repair_offered_after_break"):
            fails.append("S-8 no repair offered after a break (Duolingo: freeze is before, repair is after; a break with no way back is final by design)")
        if pb.get("repair_paid"):
            fails.append("S-8 repair is paid / gem-priced (for a hard-days app repair must be free; monetising the break is the paid-freeze ban of S-3 applied after the break)")
        if pb.get("repair_method") != "earn_back_core_action":
            fails.append(f"S-8 repair method is {pb.get('repair_method')!r}, not earn_back_core_action (Duolingo's free form: do the lesson / 3 lessons and the streak is restored)")
        w = pb.get("repair_window_hours")
        if w is None or w < 48:
            fails.append(f"S-8 repair window is {w!r}h, under 48h (Duolingo's 1-2 day window is already short; a suffering app must not make the ambulance expire faster)")
        if not pb.get("consistency_window_shown"):
            fails.append("S-9 no consistency window shown alongside the streak (Pheidi: 5-of-7 / this-month count survives a missed day; a lone daily chain does not)")
        if not pb.get("cumulative_progress_preserved"):
            fails.append("S-9 cumulative progress resets with the streak (progress must accumulate, not reset: the record of what was done survives the break)")
        if not pb.get("longest_streak_record_preserved"):
            fails.append("S-9 longest streak record is not preserved after a break (Duolingo keeps the longest streak as a dated personal record; losing the chain must not erase the record)")
        if pb.get("break_copy_style") != "encouragement_no_shame":
            fails.append(f"S-10 break copy style is {pb.get('break_copy_style')!r}, not encouragement_no_shame (JMIR 2024 / BJHP 2025: shame and guilt after a break drive abandonment; 'you lost your streak' is destructive)")
        if pb.get("punishment_on_break"):
            fails.append("S-10 a broken streak is punished (badges/levels removed or escalating rescue pressure; Pheidi: never punish a broken streak)")
        cap = pb.get("rescue_notifications_after_break")
        if cap is None or cap > 1:
            fails.append(f"S-10 rescue notifications after a break are {cap!r}, over the cap of 1 (one encouragement, then silence; rescue spam converts a hard day into a guilt loop)")
        if pb.get("grace_paywalled"):
            fails.append("S-11 grace / freeze protection is paywalled (Pheidi healthy form: grace days are built in, not a premium feature to buy)")
        if not pb.get("hard_day_declaration_protects"):
            fails.append("S-11 declaring a hard / rest day does not protect the streak (for a hard-days app the worst day is exactly the day the chain must not be held hostage)")
        if pb.get("day_boundary") != "device_local_timezone":
            fails.append(f"S-12 day boundary is {pb.get('day_boundary')!r}, not device_local_timezone (the streak day must end at midnight where the person is, travel included)")
        if not pb.get("offline_completion_counts_on_sync"):
            fails.append("S-12 an offline completion does not count on sync (a completed core action that reached the device must not be lost to connectivity)")
        if not pb.get("outage_protection"):
            fails.append("S-12 no outage protection (when the service fails, the day is protected for everyone affected; the user must not pay for our outage with their streak)")
        if not pb.get("streak_display_opt_out"):
            fails.append("S-13 the streak display cannot be hidden / opted out of (a counter that cannot be turned off is pressure, not support; opt-out is the exit from streak anxiety)")
    if d.get("store_copy_claims_no_streaks") and not d.get("streak_implemented"):
        warns.append("S-7 store copy 'no streaks' matches today's product but contradicts the in-house streak spec (2026-11-05): the contradiction is between store copy and spec, resolve it explicitly before building")
    return fails, warns

def main():
    with open(sys.argv[1]) as fh:
        d = json.load(fh)
    fails, warns = check(d)
    for w in warns:
        print(f"WARN {w}")
    for f in fails:
        print(f"FAIL {f}")
    print(f"{'PASS' if not fails else 'FAIL'} {d.get('app','?')}: {len(fails)} fail(s), {len(warns)} warning(s)")
    sys.exit(0 if not fails else 1)

if __name__ == "__main__":
    main()
