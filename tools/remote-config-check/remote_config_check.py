#!/usr/bin/env python3
"""remote-config-check: deterministic gate for the REMOTE CONFIGURATION
/ MINIMUM VERSION surface (whether the shipped app can be steered from
the cloud without a store release: a remote-config provider and its
parameters are decided and recorded, every parameter has a safe in-app
default so the app works offline, values are fetched and activated on
a recorded strategy, the installed version is compared against a
remotely-set minimum/latest at startup with a forced blocking update
and a flexible prompt, a maintenance / kill switch and feature rollout
can disable a broken surface remotely, the one remote surface that
already exists -- RevenueCat Offerings -- is actually honoured rather
than overridden by a hardcoded local decision, and fetch outcomes and
the version distribution are measured and verified on a real device).
Stdlib only, offline, free.
Sources (read 2026-11-16):
- Firebase Remote Config, Enforce a minimum app version
  https://firebase.google.com/docs/remote-config/use-cases/minimum-version
  Define minimum_version / latest_version / update_url in the template;
  set safe in-app defaults so the app operates normally offline or when
  the first fetch fails; fetch and activate at startup; compare the
  installed version; below minimum show a non-dismissible blocking
  modal to the store, below latest show a dismissible prompt; add a
  real-time listener so urgent version requirements take effect
  immediately; test with a limited group before raising the minimum.
- Firebase Remote Config loading strategies
  https://firebase.google.com/docs/remote-config/loading
  Fetch/activate on load, behind a loading screen with a timeout, or
  load-for-next-startup; never rely on connectivity -- always set
  in-app defaults and keep them in sync with the backend template;
  use real-time updates instead of mass simultaneous fetches.
- RevenueCat Experiments overview
  https://www.revenuecat.com/docs/tools/experiments-v1/experiments-overview-v1
  Experiments and remote paywall control work only as long as the app
  displays the `current` Offering fetched from the SDK; hardcoding an
  offering identifier (or overriding the assignment locally) silently
  disables them.
Distinct from the Paywall Experiment Gate and the Offerings specs:
those govern what is tested; this gate governs whether ANY remotely
delivered decision -- version floor, maintenance, feature rollout,
offering assignment -- can reach the installed base at all.
Exit 0 = PASS, 1 = FAIL.
"""
import json, sys

def check(d):
    fails = []
    dec = d.get("decision") or {}
    if not dec.get("provider_and_template_recorded"):
        fails.append("RC-0 no remote-config provider / template is recorded (RemoteConfig and Firebase appear zero times in the sources and the resolved packages; every value the app runs on is compiled into the binary or its Info.plist, so no decision about a cloud-steered surface was ever taken, let alone recorded)")
    if not dec.get("parameters_recorded"):
        fails.append("RC-0 no parameter set is recorded (minimum_version, latest_version, update_url, maintenance/kill and feature-rollout parameters appear zero times in the tree -- there is no list of what the cloud is allowed to change)")
    if not dec.get("change_owner_and_rollback_recorded"):
        fails.append("RC-0 no change owner, template history or rollback path is recorded (nobody is named as able to publish or roll back a remote change, so an urgent change would have no operator and a bad one no undo)")
    dfl = d.get("defaults") or {}
    if not dfl.get("inapp_defaults_for_every_parameter"):
        fails.append("RC-1 no in-app defaults exist for remote parameters (there are no parameters; the closest existing pattern, AppConfig, fatalErrors on a missing or empty Info.plist value instead of falling back to a safe default -- the opposite of the guide's offline-safe form)")
    if not dfl.get("app_operates_offline_or_fetch_failure"):
        fails.append("RC-1 offline / first-fetch-failure behaviour for remotely-steered values is not established (nothing fetches, so nothing defines what the app does when a fetch fails; the version floor and any kill switch would simply not exist on an offline or first-launch device)")
    if not dfl.get("defaults_kept_in_sync_with_template"):
        fails.append("RC-1 no defaults-sync practice is recorded (no downloaded template defaults, no sync step -- even a future integration would drift between the bundled defaults and the console template with no check)")
    fet = d.get("fetch") or {}
    if not fet.get("sdk_dependency_present"):
        fails.append("RC-2 no remote-config SDK dependency exists (Package.resolved and the project references contain RevenueCat / Mixpanel / Singular / Rive / ComponentsKit / WebRTC only; Firebase is zero)")
    if not fet.get("fetch_and_activate_on_launch"):
        fails.append("RC-2 no fetch-and-activate happens at launch for configuration (AppDelegate configures RevenueCat, Mixpanel and Singular and refreshes Offerings, but no config fetch exists -- a published change could never reach a running install)")
    if not fet.get("fetch_interval_and_strategy_recorded"):
        fails.append("RC-2 no loading strategy or minimum fetch interval is recorded (none of the guide's three strategies -- on load, behind a loading screen, or load-for-next-startup -- was chosen, and the production 12-hour default interval is nowhere acknowledged)")
    if not fet.get("realtime_listener_for_urgent_changes"):
        fails.append("RC-2 no real-time config listener exists (an urgent minimum-version raise for a security or backend-breaking change would wait for the next scheduled fetch or restart instead of taking effect on active devices, which the guide names as the reason to add the listener)")
    ver = d.get("version_enforcement") or {}
    if not ver.get("current_version_read_from_bundle"):
        fails.append("RC-3 the installed version is not even read on device (no CFBundleShortVersionString read exists to compare against a floor)")
    if not ver.get("version_compared_at_startup"):
        fails.append("RC-3 no version comparison happens at startup (AppConfig.appVersion is read only for schedule-map selection, analytics properties and an X-App-Version header; it is never compared against any minimum or latest value anywhere in the tree)")
    if not ver.get("forced_blocking_update_below_minimum"):
        fails.append("RC-3 there is no forced blocking update (a version made incompatible by a backend change, a deprecated service or a security fix keeps running with no non-dismissible modal and no way to move its user -- the failure surfaces as broken behaviour, not as an update instruction)")
    if not ver.get("flexible_prompt_below_latest"):
        fails.append("RC-3 there is no flexible update prompt (users on older-but-supported versions are never told an update exists, so the installed base fragments silently and every backend must support every shipped version forever)")
    if not ver.get("store_link_taken_from_parameter"):
        fails.append("RC-3 no store update link is wired to a parameter or a constant (update_url appears zero times; even a hand-built prompt would have nowhere recorded to send the user)")
    ctl = d.get("remote_control") or {}
    if not ctl.get("maintenance_or_kill_switch_present"):
        fails.append("RC-4 no maintenance mode or kill switch exists (maintenance appears zero times as a control; a broken backend, a bad nudge model or a harmful feature cannot be stopped remotely -- the only remedy is an emergency store release and its review wait)")
    if not ctl.get("feature_rollout_remote_control_present"):
        fails.append("RC-4 no feature can be rolled out or rolled back by percentage or remotely at all (percentage rollouts and limited testing groups -- the guide's safe-release form -- have no mechanism; every feature ships to 100% of users in the binary or not at all)")
    if not ctl.get("revenuecat_current_offering_honoured"):
        fails.append("RC-4 the one remote surface that exists is overridden locally (SubscriptionManager does fetch Offerings at launch, but PaywallGateVariant.resolve() ignores its argument and always returns .soft and showsCloseButton always returns true, so a RevenueCat experiment assignment or a remote offering change cannot change what the paywall does -- the exact hardcoding the Experiments docs warn silently disables experiments)")
    mea = d.get("measurement") or {}
    if not mea.get("fetch_and_activate_outcomes_measured"):
        fails.append("RC-5 config fetch/activate outcomes are not measured (no fetch exists to measure; a throttled, failed or stale configuration would be invisible, and staleness age is nowhere recorded)")
    if not mea.get("version_distribution_measured"):
        fails.append("RC-5 the installed-version distribution is not measured (without app_version on events, raising a minimum version would be a blind guess about how many users it blocks)")
    if not mea.get("test_change_verified_on_device"):
        fails.append("RC-5 no test parameter change has ever been verified reaching a device (no limited-testing-group run, no record that a published template value changed behaviour on a real install -- delivery is unproven, not merely unconfigured)")
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
