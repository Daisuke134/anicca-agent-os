#!/usr/bin/env python3
"""metrickit-check: deterministic gate for the DIAGNOSTICS surface
(crash / hang / CPU / disk-write / launch diagnostics and the daily
performance metrics the OS collects on real devices -- MetricKit --
plus the triage and measurement loop that must consume them).
Stdlib only, offline, free.
Sources (read 2026-11-16):
- Apple WWDC26 session 222 "Meet the new MetricKit"
  https://developer.apple.com/videos/play/wwdc2026/222/
  MetricKit is the collection piece of the performance workflow. It
  provides two kinds of data: metrics (ongoing health signal: launch
  time, hang time/rate, CPU, memory, disk, network -- collected
  continuously and delivered in a daily report) and diagnostics
  (which code path caused a problem: crash diagnostics carry a
  backtrace, a termination reason, and an exception type; hang,
  CPU-exception, disk-write-exception, app-launch, and (iOS 27)
  memory-exception diagnostics). When something goes wrong the
  system captures the diagnostic on device and delivers it to the
  app; the workflow is monitor -> triage to root cause -> fix ->
  monitor again.
- Apple WWDC20/21 MetricKit sessions (apple-docs mirror)
  https://apple-docs.everest.mt/docs/wwdc/wwdc2020-10081/
  https://apple-docs.everest.mt/docs/wwdc/wwdc2021-10181/
  Diagnostics arrive by implementing the MXMetricManagerSubscriber
  didReceive methods; a hang is unresponsiveness of at least 250ms;
  since iOS 15 diagnostics are delivered promptly (in practice on
  the next launch after the event), while metric payloads batch to
  roughly the prior 24 hours, at most once per day. Exit reasons are
  part of the metric set. MetricKit reports only from real devices,
  never the Simulator, and diagnostic data comes only from users
  who opted in to sharing analytics with developers -- coverage is
  a sample, never a census.
Exit 0 = PASS, 1 = FAIL.
Input JSON: {app,
 inventory:{decision_recorded, surfaces_enumerated,
   optin_sampling_fact_recorded, organizer_readback_recorded},
 subscription:{subscriber_registered_at_launch,
   subscriber_retained_for_lifetime, both_callbacks_implemented},
 handling:{payloads_persisted_before_processing,
   payloads_forwarded_to_store, past_payloads_handled},
 funnel:{crash_distinguished_from_abandonment,
   diagnostics_joined_to_version, hang_on_critical_path_is_failure},
 triage:{triage_cadence_recorded, top_signature_owned,
   per_release_regression_compared},
 measurement:{crash_free_measured, hang_rate_measured,
   coverage_share_stated}}
"""
import json, sys

def check(d):
    fails = []
    inv = d.get("inventory") or {}
    if not inv.get("decision_recorded"):
        fails.append("MK-0 no diagnostics-channel decision is recorded (MetricKit in-app, a third-party crash SDK, Organizer-only, or knowingly none -- an unrecorded channel means crashes and hangs reach the team only when a user happens to complain)")
    if not inv.get("surfaces_enumerated"):
        fails.append("MK-0 the diagnostic surfaces are not enumerated: crash, hang (>=250ms main-thread unresponsiveness), CPU exception, disk-write exception, app-launch, and the daily metrics (launch histogram, hang rate, memory, exit reasons) -- a surface nobody enumerated is a failure mode nobody looks for")
    if not inv.get("optin_sampling_fact_recorded"):
        fails.append("MK-0 the coverage fact is not recorded: MetricKit diagnostics and Organizer data come only from users who opted in to sharing analytics, and only from real devices -- treating a sampled channel as a census understates every rate derived from it")
    if not inv.get("organizer_readback_recorded"):
        fails.append("MK-0 the Xcode Organizer / App Store Connect metrics readback has no recorded cadence or owner (Apple collects the platform-side metrics whether or not anyone reads them; an unread Organizer is a crash signal that exists and is ignored)")
    sub = d.get("subscription") or {}
    if not sub.get("subscriber_registered_at_launch"):
        fails.append("MK-1 no MXMetricManager subscriber is registered early at launch (diagnostics are delivered to a subscriber the app registered with MXMetricManager.shared.add; without one the OS has nowhere in-process to deliver crash and hang payloads)")
    if not sub.get("subscriber_retained_for_lifetime"):
        fails.append("MK-1 the metric subscriber is not retained for the process lifetime (a subscriber that is deallocated after registration silently stops receiving payloads -- delivery failure with no error anywhere)")
    if not sub.get("both_callbacks_implemented"):
        fails.append("MK-1 both payload callbacks are not implemented (didReceive for metric payloads AND didReceive for diagnostic payloads -- metrics without diagnostics shows that something regressed but never which code path caused it)")
    hnd = d.get("handling") or {}
    if not hnd.get("payloads_persisted_before_processing"):
        fails.append("MK-2 received payloads are not persisted before processing (payloads arrive at most once per day and diagnostics describe events that already terminated the app; an in-memory-only handler loses the only copy when processing fails)")
    if not hnd.get("payloads_forwarded_to_store"):
        fails.append("MK-2 payloads are not forwarded to a durable store or analytics backend evidenced by reading the forwarding code (a payload that stays on one device is a report nobody can triage, aggregate, or compare across releases)")
    if not hnd.get("past_payloads_handled"):
        fails.append("MK-2 past payloads are not handled (the subscriber contract includes the backlog of payloads generated before registration; ignoring them blinds the first days after the channel is switched on, exactly when the baseline is set)")
    fun = d.get("funnel") or {}
    if not fun.get("crash_distinguished_from_abandonment"):
        fails.append("MK-3 a crash is not distinguished from voluntary abandonment in the funnel (a crash mid-onboarding or mid-paywall produces neither completion nor a distinguishable exit signal, so the funnel reads a stability failure as a persuasion failure and the team optimizes copy for a crash)")
    if not fun.get("diagnostics_joined_to_version"):
        fails.append("MK-3 diagnostics are not joined to app version (and, where the payload allows, build and OS version) -- an unjoined crash count cannot be attributed to the release that introduced or fixed it")
    if not fun.get("hang_on_critical_path_is_failure"):
        fails.append("MK-3 a hang on the critical path (first launch, onboarding, paywall, the first-value moment) is not treated as a product failure (a >=250ms main-thread stall at the moment of first value is indistinguishable from rejection to the person experiencing it, and hangs leave no other trace)")
    tri = d.get("triage") or {}
    if not tri.get("triage_cadence_recorded"):
        fails.append("MK-4 no triage cadence is recorded for diagnostics (Apple's workflow is monitor -> triage to root cause -> fix -> monitor; payloads nobody triages on a cadence accumulate as decoration)")
    if not tri.get("top_signature_owned"):
        fails.append("MK-4 the top crash/hang signature has no recorded owner (an unowned top signature is a known failure that repeats for every new user until someone is named; ownership is one person, recorded)")
    if not tri.get("per_release_regression_compared"):
        fails.append("MK-4 releases are not compared on stability (crash-free and hang rate per version, before/after each release -- a regression shipped to 100% of users is otherwise discovered from reviews)")
    ms = d.get("measurement") or {}
    if not ms.get("crash_free_measured"):
        fails.append("MK-5 crash-free users/sessions are not measured (the headline stability number of every consumer app; unmeasured, a crash problem has no size and a fix has no effect size)")
    if not ms.get("hang_rate_measured"):
        fails.append("MK-5 hang rate is not measured (seconds of hang per hour of use, from the daily metric payloads or Organizer -- hangs are the silent half of stability: the app never dies, it just feels broken)")
    if not ms.get("coverage_share_stated"):
        fails.append("MK-5 the coverage share is not stated next to the stability numbers (diagnostics cover only opted-in users on real devices; a crash-free figure printed without its denominator's coverage is a census claim built on a sample)")
    return fails

def main():
    if len(sys.argv) != 2:
        print("usage: metrickit_check.py <state.json>")
        return 2
    with open(sys.argv[1]) as f:
        d = json.load(f)
    fails = check(d)
    app = d.get("app", "?")
    if fails:
        print(f"FAIL {app}: {len(fails)} gate failures")
        for x in fails:
            print(" -", x)
        return 1
    print(f"PASS {app}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
