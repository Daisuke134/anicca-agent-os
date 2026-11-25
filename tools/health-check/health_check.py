#!/usr/bin/env python3
"""health-check: deterministic gate for the HealthKit measured-state stack
(sleep analysis read -> derived wake/sleep state -> timing and
personalization), as used by a behaviour app whose problems are
sleep-bound. Stdlib only, offline, free.
Sources (read 2026-11-15):
- Rise Science FAQ (the fixed winner for Sleep Reset, and the canon for
  measured-state personalization) https://www.risescience.com/faq
  RISE is integrated with Apple's HealthKit and receives phone movement
  and steps data; wearables feed it through HealthKit too. It learns the
  person's unique sleep biology -- sleep need, energy peaks and dips are
  unique per person -- and customizes the entire experience accordingly.
  It checks Apple Health each morning for the previous night's sleep
  data and falls back to phone motion when no wearable data exists.
- BitBakery, How to Use Apple HealthKit Data in an App (production
  integration postmortem) https://www.bitbakery.co/blog/how-to-use-apple-healthkit-data-in-an-app
  Consent is per data type and explicit. Sleep is category data, not
  quantity data: values include in-bed / asleep / REM / core / deep, and
  overlapping samples must be merged by the app to compute actual
  seconds asleep. Sleep is tracked on an 18:00 -> next-day 06:00 window,
  so the query range must reach into the previous evening. If the person
  denies permission the app is never told: HealthKit returns an empty
  response with no error and no status, and the app may not prompt again.
- Tessl swift-ios-skills HealthKit reference (background delivery)
  https://tessl.io/registry/dpearson2699/swift-ios-skills/3.9.1/files/skills/healthkit/SKILL.md
  Register HKObserverQuery plus enableBackgroundDelivery so new samples
  wake the app; the observer completion handler must always be called or
  future deliveries stall. Request only the types the feature uses --
  broad permission sheets are an App Review risk.
Exit 0 = PASS, 1 = FAIL. Warnings do not fail.
Input JSON: {app,
 inventory:{recorded, sleep_problems_named, timing_basis_recorded},
 authorization:{entitlement_present, usage_description_present,
   availability_checked, authorization_requested,
   read_types_minimum_sleep_only, requested_at_value_moment_not_launch,
   denial_empty_handled_honestly},
 reading:{sleep_query_implemented, overlapping_samples_merged,
   evening_window_range_handled, wake_and_duration_derived,
   background_delivery_registered, observer_completion_handler_called},
 use:{measured_state_feeds_scheduling, fixed_slots_only_as_fallback,
   measured_state_feeds_personalization, no_measured_claim_without_data},
 privacy:{read_only, raw_samples_never_leave_device,
   health_data_not_in_analytics, no_advertising_use},
 measurement:{event_defined, event_fired, authorization_funnel_counted,
   coverage_counted, joinable_to_outcome}}
"""
import json, sys

def check(d):
    fails, warns = [], []
    inv = d.get("inventory") or {}
    if not inv.get("recorded"):
        fails.append("HK-0 the HealthKit measured-state is not inventoried (which sleep-bound problems exist, what timing basis is used today, and what is actually read are nowhere recorded; an unrecorded surface cannot be audited)")
    if not inv.get("sleep_problems_named"):
        fails.append("HK-0 no sleep-bound problem is named (a measured sleep state is justified only by a problem whose shape depends on when the person actually slept and woke; with no such problem named, the honest decision may be not to build it, but that decision must be recorded, not drifted into)")
    if not inv.get("timing_basis_recorded"):
        fails.append("HK-0 the current timing basis is not recorded (whether nudge times come from fixed population slots, self-reported answers, or measured state is the fact this gate exists to make explicit; code that silently hardcodes slots is a basis nobody chose on the record)")
    auth = d.get("authorization") or {}
    if not auth.get("entitlement_present"):
        fails.append("HK-1 the HealthKit entitlement (com.apple.developer.healthkit) is absent from every entitlements file, so no code path in this app can ever request or read health data")
    if not auth.get("usage_description_present"):
        fails.append("HK-1 no NSHealthShareUsageDescription exists (without the purpose string the authorization sheet cannot be shown at all; the string is also where the person learns this is read-only sleep timing, in their own language)")
    if not auth.get("availability_checked"):
        fails.append("HK-1 HKHealthStore.isHealthDataAvailable() is never checked (HealthKit is unavailable on some devices and restricted by managed-device policy; an unchecked request path fails silently exactly on the devices that need the fallback most)")
    if not auth.get("authorization_requested"):
        fails.append("HK-1 HealthKit authorization is never requested (without the person's own grant the store returns nothing forever; the measured state cannot exist)")
    if auth.get("authorization_requested") and not auth.get("read_types_minimum_sleep_only"):
        fails.append("HK-1 the request asks for more than the sleep types the feature uses (broad permission sheets are an App Review risk and a trust cost: a person asked for their heart rate to fix their wake-up words says no to everything)")
    if auth.get("authorization_requested") and not auth.get("requested_at_value_moment_not_launch"):
        fails.append("HK-1 authorization is requested at launch or in a settings corner, not at the value moment (the ask belongs inside the sleep problem's own setup -- 'may we read your actual sleep so your morning words arrive when you wake, not at 7:30?' -- a launch-time ask reads as data harvesting and is denied)")
    if not auth.get("denial_empty_handled_honestly"):
        fails.append("HK-1 denial is not handled honestly (HealthKit never reports a denial: a denied or empty store just returns no samples, and the app may not prompt again. The app must treat empty as 'use the declared fallback' and must never present self-reported or fixed times as measured sleep)")
    rd = d.get("reading") or {}
    q = bool(rd.get("sleep_query_implemented"))
    if not q:
        fails.append("HK-2 no sleepAnalysis query is ever executed (HKCategoryType sleepAnalysis is the only sanctioned source of when this person actually slept; without a query there is no measured state, only answers and clocks)")
    if q and not rd.get("overlapping_samples_merged"):
        fails.append("HK-2 overlapping sleep samples are not merged (sleep is category data -- in-bed, asleep, REM, core, deep arrive as overlapping samples from multiple sources; summing them raw double-counts the night and fabricates durations)")
    if q and not rd.get("evening_window_range_handled"):
        fails.append("HK-2 the query window does not reach into the previous evening (sleep is tracked 18:00 -> next-day 06:00; a calendar-day query cuts the night in half and the wake time it derives is wrong on exactly the late nights that matter)")
    if not rd.get("wake_and_duration_derived"):
        fails.append("HK-2 no wake time or sleep duration is derived from samples (raw samples are not a state; the product needs 'woke at 06:12 after 5h40m' as one derived value the scheduler and the synthetic user can consume)")
    if not rd.get("background_delivery_registered"):
        fails.append("HK-2 background delivery is not registered (no HKObserverQuery + enableBackgroundDelivery for sleepAnalysis: the app only learns last night's sleep when opened, which is after the morning intervention it was supposed to time)")
    if rd.get("background_delivery_registered") and not rd.get("observer_completion_handler_called"):
        fails.append("HK-2 the observer query's completion handler is not always called (a missed completion delays or stops future background deliveries; the morning wake-up is a one-shot event and a stalled delivery misses it permanently)")
    use = d.get("use") or {}
    feeds = bool(use.get("measured_state_feeds_scheduling"))
    if not feeds:
        fails.append("HK-3 the measured state never feeds scheduling (nudge times remain fixed per-problem clock slots chosen for a population -- e.g. 20:30/22:30/23:45 -- so a person who woke at 05:00 and a person who woke at 09:30 receive their 'morning' words at the same minute; data that is read but never moves a time is decoration)")
    if feeds and not use.get("fixed_slots_only_as_fallback"):
        fails.append("HK-3 fixed slots still compete with the measured state instead of serving only as its fallback (two timing authorities produce incoherent days; the winner's shape is measured-first with an explicit fallback -- RISE falls back to phone motion when the wearable is absent, never to a population clock)")
    if not use.get("measured_state_feeds_personalization"):
        fails.append("HK-3 the measured state never feeds personalization (last night's duration belongs in the synthetic user: a 4-hour night changes which problem leads today and how hard to push; without that join the 'personalized' timing is personalized in copy only)")
    if not use.get("no_measured_claim_without_data"):
        fails.append("HK-3 the product claims measured sleep it does not have (copy or UI that says 'based on your sleep' while the state came from a questionnaire or a fixed slot is a false capability claim; what is shown outside must exist inside)")
    pv = d.get("privacy") or {}
    if not pv.get("read_only"):
        fails.append("HK-4 the integration writes health data it does not need (a timing feature is read-only; every write type widens the permission sheet, the review surface, and the harm if the account is compromised)")
    if not pv.get("raw_samples_never_leave_device"):
        fails.append("HK-4 raw health samples leave the device (samples are the person's body data at minute resolution; only derived, coarse state -- woke hour, duration band -- may ever be transmitted, and only if the product discloses it)")
    if not pv.get("health_data_not_in_analytics"):
        fails.append("HK-4 health data appears in analytics payloads (analytics is a third-party surface with its own retention; a sleep timestamp in an event stream is health data sharing regardless of the field's name)")
    if not pv.get("no_advertising_use"):
        fails.append("HK-4 health data can reach advertising or targeting (Apple prohibits using HealthKit data for advertising; beyond the rule, a person who learns their worst night targeted an ad never grants anything again)")
    ms = d.get("measurement") or {}
    if ms.get("event_defined") and not ms.get("event_fired"):
        fails.append("HK-5 the measured-state event is defined but fired from 0 call sites (a defined-but-unfired event reads as 'personalization works' forever, indistinguishable from the truth)")
    if not ms.get("event_defined"):
        fails.append("HK-5 no measured-state measurement event exists at all (authorization funnel, data coverage, and timing shifts are unknowable in principle)")
    if not ms.get("authorization_funnel_counted"):
        fails.append("HK-5 the authorization funnel is not counted (requested -> sheet shown -> data present/empty is the surface's conversion funnel; note HealthKit cannot distinguish denial from no-data, so the honest metric is 'samples present', never 'granted')")
    if not ms.get("coverage_counted"):
        fails.append("HK-5 data coverage is not counted (what share of active users actually have sleep samples decides whether measured timing is the product or a demo for a minority; without coverage the fixed-slot majority is invisible)")
    if not ms.get("joinable_to_outcome"):
        fails.append("HK-5 measured-state events cannot be joined to outcome (woke-relative delivery -> opened / acted, versus fixed-slot delivery), so whether measured timing earns its permission ask is a matter of opinion")
    return fails, warns

def main():
    d = json.load(open(sys.argv[1]))
    fails, warns = check(d)
    for w in warns: print("WARN:", w)
    for f in fails: print("FAIL:", f)
    print(f"{'PASS' if not fails else 'FAIL'}: {len(fails)} fail(s), {len(warns)} warning(s) -- {d.get('app')}")
    sys.exit(0 if not fails else 1)

if __name__ == "__main__":
    main()
