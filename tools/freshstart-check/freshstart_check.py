#!/usr/bin/env python3
"""freshstart-check: gate for the fresh start effect (temporal landmarks)
in a behaviour app - a recorded landmark calendar, landmarks named as new
periods that close the old one, begin-asks timed to landmarks with a
begin-at-the-next-landmark option, no invented landmarks, a guard against
an anticipated landmark pausing action now, a post-start carry plan, and
reads that claim initiation only. Stdlib only, offline, free.
Exit 0=PASS, 1=FAIL.
Sources (read 2026-11-24):
- Dai, Milkman & Riis (2014), Management Science, "The Fresh Start
  Effect": diet searches +14.4% at a new week, +3.7% new month, +82.1%
  new year, +10.2% after holidays; gym visits (11,912 members) +33.4%
  new week, +14.4% new month, +11.6% new year, +47.1% new semester,
  +24.3% after breaks, +7.5% after birthdays; stickK commitments
  (43,012 users) +62.9% new week, +145.3% new year. Mechanism proposed:
  landmarks open a new mental accounting period, relegating past
  imperfections to the old period and inducing a big-picture view.
- Dai, Milkman & Riis (2015), Psychological Science: the same date
  (March 20) labelled "first day of spring" drew 25.6% sign-ups vs
  7.2% as "the third Thursday in March" - the label, not the date,
  carries the effect.
- Koo, Dai et al. (2020), OBHDP: anticipating an upcoming landmark can
  UNDERMINE motivation to keep pursuing a goal now - a future fresh
  start must never be sold as a reason to pause.
- Beshears, Dai, Milkman & Benartzi (2021), OBHDP: fresh-start framing
  (start after an upcoming birthday / landmark) raised real retirement
  savings contributions vs identical mailers without the framing.
Separation: seasonal-campaign owns holiday offer windows and prices;
second-session-bridge owns day-2 return; ifthen-check owns the plan
formed at the start. This gate owns only the landmark layer: which
landmarks exist, how they are named, when begin-asks fire, and how the
initiation lift is read.
NOT adopted: invented/fake landmarks or fake scarcity (the label must
name a real period boundary), and claiming maintenance/retention
effects - the evidence is about initiation and commitment, not upkeep.
"""
import json, sys
CHECKS=[
 ("per_app_landmark_calendar_recorded","FS-0 no per-app landmark calendar is recorded (without a calendar of real period boundaries - week, month, year, season, return from break - there is nothing to time a begin-ask to)"),
 ("landmark_types_distinguished","FS-0 calendar landmarks and personal landmarks (birthday, anniversary, return from a break) are not distinguished (Dai 2014 measures both, with different sizes - birthdays +7.5% gym visits vs semesters +47.1% - and personal ones need the person's own date)"),
 ("start_offers_mapped_to_landmarks","FS-0 begin-asks / start offers are not mapped to specific landmarks (an unmapped 'start today' ask spends the same copy on a mid-period day, where the measured lift is absent)"),
 ("landmark_named_as_new_period","FS-1 the landmark is not named as the start of a new period (Dai 2015: the same date labelled 'first day of spring' drew 25.6% vs 7.2% unlabelled - an unnamed boundary does not open a new mental accounting period)"),
 ("past_period_closed_in_frame","FS-1 the frame does not close the past period (the proposed mechanism relegates past imperfections to the previous period; a frame that drags the old failures into the new period removes the clean-ledger effect)"),
 ("big_picture_goal_prompt_at_landmark","FS-1 no big-picture goal prompt sits at the landmark (landmarks induce a big-picture view of one's life - Dai 2014 - so the moment is spent on a trivial ask instead of the aspirational goal it actually motivates)"),
 ("begin_ask_timed_to_landmark","FS-2 the main begin-ask is not timed to land at the landmark (the spikes are measured AT the outset of the new week / month / year, and decay as the period wears on; a Thursday-evening ask for a Monday-sized decision wastes the window)"),
 ("begin_at_next_landmark_offered","FS-2 a person who declines mid-period is not offered 'begin at the next landmark' (Beshears 2021: inviting a start after an upcoming landmark raised real contributions vs identical mailers; 'now or never' discards the strongest remaining start date)"),
 ("no_invented_landmarks_or_scarcity","FS-2 landmarks or scarcity are invented (a labelled boundary must be a real period boundary; a fake 'new chapter ends tonight' is a dark pattern of the same family as the fake timers already banned in this company)"),
 ("upcoming_landmark_not_a_reason_to_pause","FS-3 an upcoming landmark is used in a way that licenses pausing now (Koo 2020: anticipating a fresh start undermines current goal pursuit - 'start Monday' copy that excuses stopping today converts the effect into its opposite)"),
 ("action_available_in_current_period","FS-3 no action is available in the current period while waiting for the landmark (the landmark is a start line for the new commitment, not a waiting room; a person ready now must be able to act now)"),
 ("post_start_carry_plan_exists","FS-3 there is no carry plan for after the start (the 2014 evidence measures initiation and commitment, not maintenance; a landmark start with nothing carrying week two spends the lift and reads the fade as failure)"),
 ("personal_landmark_collected_with_consent","FS-4 a personal landmark (e.g. birthday) is used without the person's own date given with consent (a birthday effect cannot be timed to a guessed or scraped date, and using one silently is a privacy breach, not a nudge)"),
 ("personal_landmark_frame_not_shaming","FS-4 the personal-landmark frame shames the past self (the mechanism is distance from past imperfections, not indictment of them; shaming copy contradicts the clean-ledger frame and this product's promise on hard days)"),
 ("landmark_calendar_refreshed_yearly","FS-4 the landmark calendar is not refreshed as periods roll (holidays, seasons and semester-like boundaries move each year; a stale calendar times asks to boundaries that no longer exist)"),
 ("initiation_measured_not_maintenance_claimed","FS-5 maintenance / retention is claimed from landmark timing (the evidence supports initiation and commitment starts only; claiming upkeep from Dai 2014 overstates the source)"),
 ("landmark_cohort_read_separately","FS-5 landmark starters are not read as a separate cohort (mixing landmark and mid-period starters hides both the initiation lift and the post-start fade the carry plan is meant to fix)"),
 ("effect_sizes_quoted_from_primary_source","FS-5 effect sizes are not quoted from the primary source (gym visits +33.4% at a new week, commitments +62.9% - Dai 2014 field data; rounded-up retellings turn a real, bounded effect into a promise it never made)"),
]
def main(p):
    s=json.load(open(p)); fails=[m for k,m in CHECKS if s.get(k) is not True]
    for f in fails: print("FAIL",f)
    print(f"RESULT {'PASS' if not fails else 'FAIL'} pass={len(CHECKS)-len(fails)}/{len(CHECKS)} fails={len(fails)}")
    return 0 if not fails else 1
if __name__=="__main__":
    if len(sys.argv)!=2: print("usage: freshstart_check.py <state.json>"); sys.exit(2)
    sys.exit(main(sys.argv[1]))
