#!/usr/bin/env python3
"""analytics-check: deterministic gate for the ANALYTICS INSTRUMENTATION
surface (whether the events a product claims to measure are actually
sent, carry consistent properties, keep identity straight, leave the
device at terminal moments, and can actually be read back).
Stdlib only, offline, free.
Sources (read 2026-11-16):
- Mixpanel "Embed Analytics into Your Product Development Cycle"
  https://docs.mixpanel.com/guides/guides-by-workflow/embed-data
  Define before building; write a tracking plan (trigger, properties,
  naming) as part of the spec; use Lexicon as the central schema
  registry; enable Event Approval to catch unplanned events; verify
  events fire and required properties are populated before shipping;
  review new events for PII; keep Lexicon descriptions current.
- Mixpanel "Events and Properties"
  https://docs.mixpanel.com/docs/data-structure/events-and-properties
  Events are actions; use one consistent naming convention (snake_case,
  Object-Verb); never create event or property names dynamically;
  standardise shared properties so the same concept means the same
  thing on every event.
Exit 0 = PASS, 1 = FAIL.
"""
import json, sys

def check(d):
    fails = []
    inv = d.get("inventory") or {}
    if not inv.get("tracking_plan_recorded"):
        fails.append("AI-0 no tracking plan is recorded where the code lives (Mixpanel's form is a structured list per feature: event, trigger, properties, naming -- an unrecorded plan means the schema is whatever the oldest call site happens to send)")
    if not inv.get("every_event_has_consumer_and_owner"):
        fails.append("AI-0 not every declared event has a recorded consumer and owner (an event nobody reads is cost and noise; an event with no owner rots silently when the screen that sent it changes)")
    if not inv.get("lexicon_governance_recorded"):
        fails.append("AI-0 Lexicon governance is not recorded (no named governor, no Event Approval / description practice -- new or renamed events will drift into the project unreviewed and duplicate the concepts already there)")
    em = d.get("emission") or {}
    if not em.get("no_dead_events"):
        fails.append("AI-1 declared events exist that are never sent (an enum/catalogue entry with no emitter reads as a measured step in every funnel discussion while sending nothing -- the funnel silently loses that step)")
    if not em.get("dead_events_disposition_recorded"):
        fails.append("AI-1 unsent events have no recorded disposition (each must be marked emitted, server-owned, or retired; unmarked, nobody can tell a broken emitter from an intentional server event)")
    if not em.get("funnel_steps_all_emitted"):
        fails.append("AI-1 not every step of the primary funnel is actually emitted (a missing middle step makes the steps around it look like the leak)")
    pr = d.get("properties") or {}
    if not pr.get("same_concept_same_property_name"):
        fails.append("AI-2 the same concept travels under different property names on different events (e.g. a step identified as screen_id on the view event and step_id on the completion event -- every cross-event funnel join then needs a hand mapping that breaks silently when either side changes)")
    if not pr.get("funnel_events_carry_answers"):
        fails.append("AI-2 funnel completion events do not carry the answers that explain them (a step count without the person's answer cannot be broken down, personalised against, or improved -- the step can only be watched, not fixed)")
    if not pr.get("pii_safe_vocabulary"):
        fails.append("AI-2 event properties are not restricted to a privacy-safe vocabulary (raw names, birth dates or free text in analytics turn the measurement system into a second, ungoverned store of personal data)")
    if not pr.get("context_properties_on_every_event"):
        fails.append("AI-2 common context (app version, build, environment, flow version, session) is not attached to every event (without it, a behaviour change cannot be separated from a release, a flow version, or test traffic)")
    idn = d.get("identity") or {}
    if not idn.get("identify_on_login"):
        fails.append("AI-3 identify is not called at login (pre-login anonymous activity and post-login activity stay two people in every funnel)")
    if not idn.get("identify_on_launch_with_stored_credentials"):
        fails.append("AI-3 a returning signed-in user is not re-identified at launch (sessions after the first open are attributed to a fresh anonymous id until some later screen happens to identify)")
    if not idn.get("reset_on_signout"):
        fails.append("AI-3 analytics identity is not reset at sign-out (the next person on the device inherits the previous person's distinct id and history)")
    if not idn.get("reset_on_account_deletion"):
        fails.append("AI-3 analytics identity is not reset at account deletion (deletion that wipes local data but keeps the analytics identity keeps measuring a person the company claims to have forgotten)")
    de = d.get("delivery") or {}
    if not de.get("flush_at_terminal_moments"):
        fails.append("AI-4 queued events are not flushed at terminal moments (abandonment, purchase, deletion are exactly the events most likely to sit in an on-device queue while the process is suspended or killed; flushing at only one of them loses the others preferentially -- the most valuable events are the ones most often missing)")
    if not de.get("event_id_and_timestamp_for_dedup"):
        fails.append("AI-4 events carry no per-event id and timestamp for deduplication (double-fires from lifecycle surfaces that legitimately overlap cannot be told apart from real repeats)")
    if not de.get("payload_logging_disabled"):
        fails.append("AI-4 event payloads are written to device logs (analytics logging left on turns every property -- including answer ids -- into log content readable by anything that can read logs)")
    if not de.get("decision_records_leave_device"):
        fails.append("AI-4 the full decision records (which stimulus was chosen, with what probability, and what happened) do not leave the device (an ids-only analytics event can count decisions but cannot rebuild the case dataset the model and eval are supposed to learn from; on-device-only rows are lost with every reinstall)")
    rb = d.get("readback") or {}
    if not rb.get("pre_ship_verification_recorded"):
        fails.append("AI-5 no pre-ship verification of the instrumentation is recorded (Mixpanel's form is to verify in staging that events fire and required properties are populated and not null before production; unrecorded, 'instrumented' means 'code exists', not 'data arrives')")
    if not rb.get("planned_vs_actual_audit_scheduled"):
        fails.append("AI-5 no planned-vs-actual audit is scheduled (declared vs sent vs received is compared by nobody on a cadence, so dead events and renamed properties accumulate until a funnel question exposes them by accident)")
    if not rb.get("read_path_verified_alive"):
        fails.append("AI-5 the read path is not verified alive (if every route that would read the data back is skipped, unauthenticated or blocked, events are being written into a void -- the failure is invisible precisely because nothing is ever read)")
    if not rb.get("environment_separation_in_analysis"):
        fails.append("AI-5 test, simulator and sandbox traffic cannot be separated from production in analysis (an environment property or an equivalent separation must exist, or internal testing inflates installs, funnels and purchases)")
    return fails

def main():
    if len(sys.argv) != 2:
        print("usage: analytics_check.py <state.json>"); return 2
    with open(sys.argv[1]) as f: d = json.load(f)
    fails = check(d)
    print(f"app: {d.get('app','?')}")
    if fails:
        print(f"FAIL {len(fails)}")
        for x in fails: print(f" - {x}")
        return 1
    print("PASS"); return 0

if __name__ == "__main__":
    sys.exit(main())
