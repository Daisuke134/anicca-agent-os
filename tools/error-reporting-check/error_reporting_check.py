#!/usr/bin/env python3
"""error-reporting-check: deterministic gate for the ERROR REPORTING
surface (whether failures in the shipped app ever become visible to
the team: a crash/error SDK is decided and started early, handled
errors at catch sites are captured -- not only unhandled crashes,
events are symbolicated and tagged by release/environment, sensitive
content is scrubbed before anything leaves the device, and delivery
is verified with a test error and a test crash read back in Issues).
Stdlib only, offline, free.
Sources (read 2026-11-16):
- Sentry iOS guide https://docs.sentry.io/platforms/apple/guides/ios/
  Error Monitoring starts as soon as the SDK is initialized; init as
  early as possible on the main thread in
  application(_:didFinishLaunchingWithOptions:) or the SwiftUI App
  initializer; upload dSYMs so stack traces show function names;
  verify with SentrySDK.capture(error:) for a handled error, and for
  a crash run without a debugger, trigger a test crash, then relaunch
  so the SDK can send the report.
- Sentry scrubbing guide
  https://docs.sentry.io/platforms/apple/guides/ios/data-management/sensitive-data/
  Use beforeSend / beforeBreadcrumb to scrub data before it is sent;
  user context should use a controlled internal identifier instead of
  email/PII; do not log PII if logs become breadcrumbs.
Distinct from the MetricKit Diagnostics Gate (2026-11-16 04:07):
MetricKit is Apple's sampled, opt-in diagnostics delivery; this gate
is the app-chosen error-reporting channel for handled errors,
breadcrumbs, release tagging and issue workflow.
Exit 0 = PASS, 1 = FAIL.
"""
import json, sys

def check(d):
    fails = []
    dec = d.get("decision") or {}
    if not dec.get("org_and_ios_project_recorded"):
        fails.append("ER-0 no recorded Sentry organization + iOS project for this app (the organization exists with only a javascript-nextjs project; no iOS project is recorded, so even a correct SDK would have nowhere app-specific to send events)")
    if not dec.get("dsn_and_config_source_recorded"):
        fails.append("ER-0 the DSN / configuration source is not recorded (which project the app reports to, and where the DSN value lives, exists nowhere -- the reporting destination is undecided, not just unimplemented)")
    if not dec.get("release_environment_strategy_recorded"):
        fails.append("ER-0 no release/environment strategy is recorded (how release, dist and environment distinguish production from debug/simulator is undecided, so a future stream of events could not be read per release)")
    init = d.get("initialization") or {}
    if not init.get("sdk_dependency_present"):
        fails.append("ER-1 no error-reporting SDK dependency exists (project package references are RevenueCat / Mixpanel / Singular / ComponentsKit / WebRTC / Rive only; Sentry appears zero times in the project, the sources and the resolved packages)")
    if not init.get("sdk_started_early_in_launch"):
        fails.append("ER-1 the SDK is never started (SentrySDK.start appears zero times; AppDelegate configures RevenueCat, Mixpanel and Singular at launch but no error reporter, so Error Monitoring -- which starts at initialization -- never starts)")
    if not init.get("debug_flag_off_in_production_config"):
        fails.append("ER-1 there is no production configuration separating debug behaviour from release (no SDK config exists at all, so the guide's 'set debug to false and reduce sampling before production' step has no object to apply to)")
    cap = d.get("capture") or {}
    if not cap.get("unhandled_crash_capture_enabled"):
        fails.append("ER-2 unhandled crash capture is not enabled in-app (no crash SDK and no MetricKit subscriber -- a crash on a user's device produces no event the team chose, named or can query; only Apple's anonymized Organizer aggregates exist outside the repo, unverified)")
    if not cap.get("handled_errors_captured_at_catch_sites"):
        fails.append("ER-2 handled errors are never captured (capture(error:) appears zero times; the tree's 21 catch blocks and 47 try? sites resolve errors locally or silently, so a backend outage, a decode failure or a failed nudge fetch that does not crash is invisible as an error)")
    if not cap.get("oslog_errors_routed_or_breadcrumbed"):
        fails.append("ER-2 the existing OSLog error stream is not routed anywhere (27 logger.error sites write to the on-device log under subsystem com.anicca.ios only; nothing attaches them as breadcrumbs or forwards them, so the one disciplined error stream the app has dies on the device)")
    if not cap.get("structured_local_logging_present"):
        fails.append("ER-2 there is not even a structured local logging base (no consistent Logger subsystem/categories to attach as breadcrumbs later)")
    sym = d.get("symbolication") or {}
    if not sym.get("dsym_upload_in_build_or_ci"):
        fails.append("ER-3 no dSYM upload exists in the build or CI (no upload build phase, no Sentry fastlane lane, no SENTRY_AUTH_TOKEN in CI -- even captured crashes would arrive as addresses, not function names and source locations)")
    if not sym.get("release_and_dist_tagged_on_events"):
        fails.append("ER-3 events are not tagged with release and dist (no reporter exists to tag them, so stability could not be compared release over release from the reporting channel)")
    if not sym.get("simulator_and_debug_excluded_or_tagged"):
        fails.append("ER-3 simulator/debug traffic is not excluded or tagged in the reporting channel (product analytics already suffers simulator contamination; the error channel has no recorded separation at all)")
    priv = d.get("privacy") or {}
    if not priv.get("send_default_pii_disabled_or_justified"):
        fails.append("ER-4 sendDefaultPii is not disabled or justified (no SDK config exists, so the PII posture of a future integration is undecided; the guide's example turns it on, which this app -- holding onboarding answers and nudge text -- must not copy by default)")
    if not priv.get("beforesend_and_breadcrumb_scrubbing_present"):
        fails.append("ER-4 no beforeSend / beforeBreadcrumb scrubbing exists (nothing strips tokens, email or user content from events or breadcrumbs before they would leave the device)")
    if not priv.get("user_context_anonymous_id_only"):
        fails.append("ER-4 user context is not fixed to an anonymous/internal identifier only (no scope/user configuration exists; the scrubbing guide's controlled-identifier form is unimplemented)")
    if not priv.get("secrets_and_user_content_absent_from_logs"):
        fails.append("ER-4 log content is not clean for future breadcrumb use (LLMNudgeService logs the full server response body at error level and several sites interpolate messages with privacy .public, so wiring today's logs into breadcrumbs as-is would ship user-facing nudge content off-device)")
    ver = d.get("verification") or {}
    if not ver.get("test_handled_error_verified_in_issues"):
        fails.append("ER-5 no handled test error has been verified in Issues (the guide's capture(error:) verification has never been run for this app; delivery is unproven, not merely unconfigured)")
    if not ver.get("test_crash_verified_after_relaunch"):
        fails.append("ER-5 no test crash has been verified after a relaunch without a debugger (crash delivery -- which only sends on the next launch -- is unproven)")
    if not ver.get("alert_owner_routing_recorded"):
        fails.append("ER-5 no alert/owner routing is recorded for new issues (no record of who or which loop owns a new fatal issue, so an event stream, once it exists, would arrive to nobody)")
    if not ver.get("crash_free_rate_readback_recorded"):
        fails.append("ER-5 no crash-free readback is recorded (no cadence reads crash-free users/sessions per release from the reporting channel; stability is not a number the team sees)")
    return fails

if __name__ == "__main__":
    with open(sys.argv[1]) as f:
        data = json.load(f)
    failures = check(data)
    if failures:
        print(f"FAIL ({len(failures)}):")
        for x in failures:
            print(" -", x)
        sys.exit(1)
    print("PASS")
