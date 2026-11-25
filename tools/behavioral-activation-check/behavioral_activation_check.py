#!/usr/bin/env python3
"""behavioral-activation-check: deterministic gate. Stdlib only, offline, free.
Primary sources (read via browser.search this run, 2026-11-25):
- Ekers et al. (2014) PLoS ONE 9(6):e100100, DOI 10.1371/journal.pone.0100100 -- 26 RCTs, N=1524; BA superior to controls SMD -0.74 (CI -0.91 to -0.56, k=25, N=1088) and medication SMD -0.42; majority of studies low quality, follow-ups short; severity subgroup: moderate-severe ~0.82 vs mild-moderate ~0.41.
- Cuijpers et al. (2007) Clin Psychol Rev -- activity scheduling, 16 studies, N=780, effect 0.87 vs control.
- Jacobson et al. (1996) component analysis, N=150 -- activity scheduling alone as effective as full cognitive therapy; held at 2-year follow-up (Gortner et al. 1998).
- Protocol (Martell, Addis & Jacobson 2001; Martell et al. 2010): activity monitoring with pleasure/mastery ratings, values-linked (not busywork) activity selection, graded scheduling, action precedes motivation, avoidance/withdrawal is the target.
Boundary: behavioral activation owns ONLY values-linked scheduled rewarding activity + avoidance reduction for low mood/withdrawal. NOT generic to-do/productivity, habit-loop cue design (habit-loop-check), WOOP contrasting (woop-check), if-then plans alone (ifthen-check), or prosocial giving (prosocial-check). Evidence is therapist-delivered clinical treatment for diagnosed depression; an app prompt is not that treatment.
Exit 0=PASS, 1=FAIL."""
import json, sys
def check(d):
    f=[]
    inv=d.get("inventory") or {}
    if not inv.get("behavioral_activation_surfaces_inventoried"): f.append("BA-0 behavioral-activation surfaces are not inventoried per app (any prompt that schedules an activity for a low/withdrawn user)")
    if not inv.get("behavioral_activation_defined_as_values_linked_scheduled_rewarding_activity_and_avoidance_reduction_distinct_from_todo_habit_woop"): f.append("BA-0 behavioral activation is not defined as values-linked scheduled rewarding activity plus avoidance/withdrawal reduction, distinct from generic to-do/productivity, habit-loop cue design, WOOP and if-then plans alone")
    if not inv.get("severity_and_safety_limits_audited"): f.append("BA-0 severity and safety limits are not audited (evidence is clinical treatment for diagnosed depression; effect roughly half in mild-moderate vs moderate-severe, Ekers 2014; an app surface is not a treatment and must not hold a severely unwell user in-app)")
    des=d.get("design") or {}
    if not des.get("activity_monitoring_with_pleasure_and_mastery_ratings"): f.append("BA-1 activity monitoring with pleasure and mastery ratings is not specified (the protocol learns from monitored activity-mood data, not from a static activity list)")
    if not des.get("activities_selected_from_user_values_not_generic_busywork"): f.append("BA-1 activities are not selected from the user's own values/life domains (busywork, scrolling and errands are activity but not activation; only values-linked rewarding activity carries the tested mechanism)")
    if not des.get("graded_scheduling_specific_time_smallest_step_action_before_motivation"): f.append("BA-1 graded scheduling is not specified (a specific activity at a specific time, broken to its smallest doable step, done on schedule rather than when motivation arrives -- action precedes motivation)")
    pro=d.get("prohibitions") or {}
    if pro.get("motivation_required_before_activity"): f.append("BA-2 activity is gated on feeling motivated first (that reverses the protocol: in withdrawal, motivation follows scheduled action, it does not precede it)")
    if pro.get("missed_activity_shamed_punished_or_streak_broken"): f.append("BA-2 a missed scheduled activity is shamed, punished or breaks a streak (a miss is data for re-grading the step smaller, never a failure verdict on the user)")
    if pro.get("generic_busywork_or_scrolling_counted_as_activation"): f.append("BA-2 generic busywork or phone scrolling is counted as activation (it maintains avoidance while looking active; the protocol counts contact with valued, rewarding activity)")
    mea=d.get("measurement") or {}
    if not mea.get("counts_recorded_not_rates_only"): f.append("BA-3 counts are not recorded (activities offered, scheduled, started, completed, avoided/rescheduled) -- rates alone hide whether any activation happened")
    if not mea.get("predicted_and_actual_pleasure_mastery_measured_separately"): f.append("BA-3 predicted vs actual pleasure/mastery are not measured separately (withdrawal systematically under-predicts enjoyment; the prediction gap is a core learning signal of the protocol)")
    if not mea.get("outcomes_measured_at_followup_separately_from_same_day_mood"): f.append("BA-3 outcomes are not measured at a follow-up window separately from same-day mood (effects attenuate over months, Ekers 2014 6-9 month SMD ~-0.35; same-day mood alone overstates the result)")
    cit=d.get("citation") or {}
    if not cit.get("source_numbers_cited_with_design"): f.append("BA-4 source claims are not cited with their design (Ekers 2014: 26 RCTs, N=1524, SMD -0.74 vs control, majority low quality, short follow-up; Cuijpers 2007 activity scheduling 0.87)")
    if cit.get("effect_claimed_as_cure_or_app_equivalent_to_therapy"): f.append("BA-4 the effect is claimed as a cure, or the app surface is claimed equivalent to therapist-delivered BA (the trials are clinical treatment for diagnosed depression; no app prompt has that evidence)")
    if not cit.get("revenue_chain_recorded"): f.append("BA-4 the revenue chain is not recorded (values-linked activity scheduled -> completed at graded size -> prediction gap and follow-up read locally; no chain may be asserted from the meta-analysis alone)")
    eth=d.get("ethics") or {}
    if eth.get("clinical_claim_made"): f.append("BA-5 a clinical claim is made (treats/cures depression) -- this is a structured treatment's evidence, not an app claim")
    if not eth.get("core_scheduling_available_to_free_users"): f.append("BA-5 core activity scheduling is not available to free users")
    if not eth.get("review_cadence_recorded"): f.append("BA-5 no review cadence is recorded for re-auditing behavioral-activation surfaces")
    return f
def main():
    d=json.load(open(sys.argv[1])); fails=check(d)
    for x in fails: print("FAIL:",x)
    print(f"{'PASS' if not fails else 'FAIL'}: {len(fails)} fail(s) -- {d.get('app')}")
    sys.exit(0 if not fails else 1)
if __name__=="__main__": main()
