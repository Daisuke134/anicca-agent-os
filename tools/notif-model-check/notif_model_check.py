#!/usr/bin/env python3
"""notif-model-check: deterministic gate for the NOTIFICATION MODEL-DECISION surface
(who decides timing / quantity / wording of pushes, how the words are generated,
whether the full text displays, whether comedy taste is present, and whether the
chosen word is logged). Stdlib only, offline, free.
Owns the DECISION-OWNERSHIP + GENERATION layer. Not permission/caps/segments
(notif-permission-check N-1..N-14), not per-person timing/wording tailoring mechanics
(personalized-nudge-check PN-0..PN-7), not quiet delivery (quiet-check), not rich
media format (rich-push-check), not trial reminders (trial-check T-7..T-10).
Sources (read 2026-11-22):
- Airbridge, "Push Notification Strategy for Subscription Apps"
  https://www.airbridge.io/en/blog/push-notification-strategy-for-subscription-apps
  (read in full; cites Airship benchmark of 63M users / 1,500 apps and RevenueCat
  SOSA over 75,000+ apps): pushes built on lifecycle stages + behavioral triggers,
  not broadcast schedules, raise 90-day retention up to 190%; personalized pushes
  get up to 4x the open rate of generic broadcasts; "not enough usage" is the top
  cancellation reason at 37.2%; 1 push/week already disables 10% of users and
  2-5/week disables 40%+ (Business of Apps via Airship) -- so volume has BOTH a
  floor problem (too few / none = no intervention happens) and a ceiling problem;
  caps: max 1/day per user across types, none 22:00-07:00 local, hard limit 5 per
  7 days, coordination so one user never stacks exit-intent + trial + re-engagement
  in 24h; re-engagement must name the specific pickup point, not "we miss you";
  peak-window timing gives up to 50% higher opens; the churn test is pushed vs
  non-pushed 30-day subscription retention (5+ points = working), beside in-app
  action after push and the opt-in trend as an early guardrail. Duolingo case in
  the same article: notification optimization +21% current-user retention and
  40%+ lower daily churn among best users, with one foundational rule -- protect
  the opt-in list.
- Duolingo notification practice (secondary teardowns read 2026-11-22):
  https://thedock.beehiiv.com/p/how-duolingo-used-push-notifications-to-build-a-10b-brand
  and https://dontsnooze.io/blog/duolingo-guilt-notification-teardown/ --
  copy is triggered per user state (missed days escalate, hot streaks are
  celebrated), a bandit rotates templates for novelty so the same words do not
  repeat into fatigue, humor/persona makes notifications screenshot-shared, and
  the decisive send is timed to the last actionable window before the loss lands.
- House rules (founder, 2026-11-22, primary): notification timing, quantity AND
  wording are decided by the model (Manager), never asked to the user in
  onboarding ("when do you want notifications?" is the wrong form); the words
  users receive are still mostly pre-written catalogue copy and must move to
  model generation (correction recorded 2026-11-20); quantity is currently too
  low (founder experience: notifications almost never arrive); every surface
  carries comedy taste, and the first acceptance condition is the founder
  himself -- a notification must make him laugh and ease his hard day; push
  text must fit in full (the 2026-11-22 screenshot showed a banner cut off
  mid-text); the known logging gap -- the app does not yet log which word was
  chosen with what probability -- is the biggest hole for ManagerBench.
Exit 0=PASS, 1=FAIL.
"""
import json, sys
def check(d):
    f=[]
    own=d.get("decision_ownership") or {}
    if not own.get("decision_recorded"): f.append("NM-0 the notification decision is not recorded (who decides timing, quantity and wording -- model, fixed schedule, or the user -- is nowhere written; an unrecorded decision defaults to whoever built the catalogue)")
    if not own.get("model_decides_timing_and_quantity"): f.append("NM-0 timing and quantity are not model-decided (a fixed broadcast schedule or a user-picked clock time cannot react to state; the model sets when and how many, inside the caps)")
    if not own.get("model_decides_wording"): f.append("NM-0 wording is not model-decided (the notification-giver is Manager himself, not a catalogue or rules -- if a human picked the sentence from a list, the model decided nothing)")
    if not own.get("onboarding_does_not_ask_preferred_time"): f.append("NM-0 onboarding asks the user when they want notifications (asking is the wrong form: the send time is the model's decision, informed by the person's pattern -- a preference question freezes a guess the user made on day zero)")
    gen=d.get("generation") or {}
    if not gen.get("words_generated_per_person_not_catalogue"): f.append("NM-1 the words are pre-written catalogue copy (generic broadcasts are the measured loser: personalized pushes reach up to 4x their open rate; the sentence must be generated for this person)")
    if not gen.get("generated_from_synthetic_user_and_reaction_history"): f.append("NM-1 generation is not grounded in the person's synthetic user (onboarding answers) and measured reaction history (a generated sentence with no person-model behind it is a catalogue with extra steps)")
    if not gen.get("novelty_rotation_no_repeat_template"): f.append("NM-1 the same wording can repeat to the same person (novelty is a fatigue control: the winner rotates templates via a bandit so a person never gets the identical nudge twice in a row)")
    if not gen.get("fallback_recorded_and_personal"): f.append("NM-1 the fallback when generation is unavailable is not recorded and personal (the prior model serves meanwhile; silently falling back to a generic template hides a generation outage as a quality drop)")
    vol=d.get("volume_and_protection") or {}
    if not vol.get("delivered_volume_measured_per_user_week"): f.append("NM-2 delivered volume is not measured per user per week (scheduled is not delivered: quiet delivery, caps and token failures eat sends invisibly -- the founder's 'notifications almost never arrive' is only checkable in delivered counts)")
    if not vol.get("volume_floor_and_ceiling_both_checked"): f.append("NM-2 volume is checked on one side only (too few = the intervention never happens; too many = the channel dies: 2-5/week already disables 40%+ -- the model's quantity decision must be audited against both a floor and the winner caps)")
    if not vol.get("caps_and_quiet_hours_enforced"): f.append("NM-2 winner caps are not enforced under the model's quantity (max 1 push/day per user across types, hard limit 5 per 7 days, no sends 22:00-07:00 local -- protect the opt-in list is the foundational rule)")
    if not vol.get("coordination_no_stacking_same_day"): f.append("NM-2 push types are not coordinated per user (an exit-intent, a trial warning and a re-engagement landing in the same 24h read as one desperate app, whatever each says alone)")
    tri=d.get("lifecycle_triggers") or {}
    if not tri.get("triggers_are_behavioral_not_broadcast"): f.append("NM-3 sends run on a broadcast schedule, not behavioral triggers (the retention lift belongs to lifecycle/behavior-triggered pushes; a calendar slot is not a reason in the user's life)")
    if not tri.get("lifecycle_stage_determines_message"): f.append("NM-3 lifecycle stage does not determine the message (a Day-5 trial user and a 4-month subscriber silent for 10 days are different audiences; one template for both is a targeting failure, not a copy failure)")
    if not tri.get("reengagement_names_specific_pickup_point"): f.append("NM-3 re-engagement copy does not name the specific pickup point ('we miss you' is noise; the working form names exactly where the person left off and what happens next)")
    if not tri.get("peak_window_timing_per_user"): f.append("NM-3 send time is not the person's peak window (sending at the user's own active hour is worth up to 50% higher opens; the decisive copy is the one sent in the last actionable window, not the morning advice version)")
    dsp=d.get("display_and_taste") or {}
    if not dsp.get("full_text_fits_banner_length_budget_checked"): f.append("NM-4 push text length is not checked against full banner display (a banner cut off mid-sentence delivers half an intervention; every generated text passes a length budget before it can be sent)")
    if not dsp.get("comedy_taste_present_in_copy"): f.append("NM-4 notifications carry no comedy taste (company rule: comedy taste goes into everything; for a hard-day/stress product the notification is opened because it is funny -- a humourless reminder is a spreadsheet talking)")
    if not dsp.get("founder_first_gate_laugh_hard_day_test"): f.append("NM-4 the founder first-gate is not run on notifications (first acceptance condition: the notification makes the founder laugh and eases his hard day, measured on the production experience -- a gate that exists for the home but not for pushes leaves the highest-frequency surface untested)")
    mea=d.get("measurement") or {}
    if not mea.get("chosen_word_logged_with_probability"): f.append("NM-5 the chosen word is not logged with its probability (without word + probability per send there is no intervention-to-response data, ManagerBench real cases stay at zero, and no notification can ever be learned from)")
    if not mea.get("pushed_vs_nonpushed_30d_retention_compared"): f.append("NM-5 pushed vs non-pushed 30-day subscription retention is not compared (open rate grades the message, not the subscription; a 5+ point retention gap is the test that a push type actually reduces churn)")
    if not mea.get("optout_trend_watched_as_guardrail"): f.append("NM-5 the opt-in/opt-out trend is not watched as a guardrail (a declining opt-in rate surfaces frequency and relevance damage weeks before it appears in cancellations -- by then the channel is already burned)")
    return f
if __name__=="__main__":
    data=json.load(open(sys.argv[1])); fails=check(data)
    if fails:
        print(f"FAIL ({len(fails)}):")
        [print(" -",x) for x in fails]; sys.exit(1)
    print("PASS"); sys.exit(0)
