#!/usr/bin/env python3
"""habit-loop-check: gate for cue-routine-reward habit formation design.
Lally, van Jaarsveld, Potts & Wardle (2010), Eur J Soc Psychol 40:998-1009:
96 volunteers chose a daily eating/drinking/activity behaviour performed in
the same context for 84 days; automaticity (SRHI automaticity items) followed
an asymptotic curve; of 82 analysed, model fitted 62 and fitted well for 39,
whose median time to 95% of asymptote was 66 days, range 18-254. A single
missed occasion did not materially affect formation. Repetition must be in a
stable context for the cue-response link to form; streak length is not
automaticity. Distinct from streak-check (owns streak display/representation)
and repetition-schedule-check (owns spacing): this gate owns the loop itself -
one stable cue, one small same-form routine, an immediate experienced reward,
automaticity measurement, and honest formation windows. Stdlib only, offline,
free. Exit 0=PASS, 1=FAIL.
"""
import json, sys
CHECKS=[
 ("habit_loops_recorded_per_app","HL-0 no target behaviour is recorded per app as a full cue-routine-reward loop, so habit formation cannot be audited"),
 ("target_behaviour_single_and_specific","HL-0 the target is not one single specific behaviour; a bundle of behaviours cannot attach to one cue or reach automaticity as a unit"),
 ("cue_is_existing_daily_context","HL-0 the cue is not an existing daily context (meal, commute, waking, an existing routine); an invented cue the user must remember adds a second habit to form first"),
 ("cue_stable_same_context_each_repetition","HL-1 the cue/context varies between repetitions; Lally's protocol repeats in the same context - varying contexts slow or prevent the cue-response link"),
 ("cue_fires_before_routine","HL-1 the prompt arrives after or unrelated to the routine moment instead of at the cue; a late notification trains ignoring, not the loop"),
 ("one_primary_cue_not_competing_cues","HL-1 several competing cues/triggers are used for the same behaviour; one primary cue must own the loop or no single association strengthens"),
 ("routine_small_and_low_friction","HL-2 the routine is not small and low-friction (completable in minutes, friction audited); complex routines stay effortful decisions and do not automatise"),
 ("routine_same_form_each_repetition","HL-2 the routine's form is redesigned between repetitions; changing the response resets the association the repetition was building"),
 ("single_miss_not_catastrophic","HL-2 a single missed occasion resets progress to zero or triggers shame; Lally found one miss did not materially affect formation - catastrophic resets punish exactly the normal case"),
 ("reward_immediate_after_routine","HL-3 the reward is not delivered immediately after the routine; delayed rewards reinforce whatever happened in between, not the routine"),
 ("reward_is_experienced_value","HL-3 the only reward is points/badges/streak counts with no experienced value in the routine itself; extrinsic counters alone leave nothing when the counter breaks"),
 ("reward_not_only_weekly_summary","HL-3 reinforcement exists only in a weekly summary/recap; a once-a-week signal cannot close a daily cue-routine loop"),
 ("automaticity_measured_directly","HL-4 automaticity is not measured directly (SRHI/SRBAI automaticity items or equivalent); opens and streak length measure exposure, not whether the behaviour runs without deliberation"),
 ("formation_window_from_evidence_range","HL-4 the formation window is promised as a fixed short deadline (e.g. 21 days); the evidence range is 18-254 days with median 66 for well-fitted cases - a fixed promise is false for most users"),
 ("context_change_plan_exists","HL-4 there is no plan for context disruption (travel, moving, schedule change); habits are context-bound, so a broken context silently kills the loop without a re-anchoring path"),
 ("primary_numbers_quoted_with_design","HL-5 Lally numbers are quoted without design (96 volunteers, 82 analysed, 39 good fits, median 66 days, range 18-254, 84-day protocol) - the bare '66 days' strips its conditions"),
 ("repetition_counted_only_in_cue_context","HL-5 repetitions are counted from raw opens/sessions regardless of context; only repetitions performed at the cue in its context build this loop"),
 ("revenue_claim_tied_to_automaticity_chain","HL-5 any retention/revenue claim is not tied to the source chain - stable cue -> repeated same-form routine -> immediate reward -> automaticity -> retention - instead of asserting habit design directly causes purchases"),
]
def main(p):
    s=json.load(open(p)); fails=[m for k,m in CHECKS if s.get(k) is not True]
    for f in fails: print("FAIL",f)
    print(f"RESULT {'PASS' if not fails else 'FAIL'} pass={len(CHECKS)-len(fails)}/{len(CHECKS)} fails={len(fails)}")
    return 0 if not fails else 1
if __name__=="__main__":
    if len(sys.argv)!=2: print("usage: habit_loop_check.py <state.json>"); sys.exit(2)
    sys.exit(main(sys.argv[1]))
