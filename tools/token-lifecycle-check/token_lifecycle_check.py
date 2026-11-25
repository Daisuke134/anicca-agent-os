#!/usr/bin/env python3
"""token-lifecycle-check: deterministic gate for the APNS DEVICE TOKEN
LIFECYCLE surface (how a device token is obtained, forwarded, replaced,
retired and pruned -- the registration contract that decides whether a
remote nudge can reach a device at all).
Stdlib only, offline, free.
Sources (read 2026-11-16):
- Apple "Registering Your App with APNs" (Apple Developer Documentation)
  https://developer.apple.com/documentation/usernotifications/registering-your-app-with-apns
  Registration happens on every launch; APNs issues the token through
  application(_:didRegisterForRemoteNotificationsWithDeviceToken:) and
  the app must forward it to its provider server. Tokens can change
  (new device, restored backup, OS reinstall), so the token must be
  requested and forwarded every launch, never cached as permanent, and
  registration failure arrives through
  application(_:didFailToRegisterForRemoteNotificationsWithError:).
- Apple APNs provider guidance: a token is specific to one app on one
  device in one environment (sandbox vs production are different
  worlds); sending to a token APNs reports as unregistered (HTTP 410,
  reason Unregistered) means the token is dead and must be removed from
  the server's records instead of retried forever.
Exit 0 = PASS, 1 = FAIL.
Input JSON: {app,
 inventory:{lifecycle_decision_recorded, token_owner_recorded,
   environment_mapping_recorded},
 forwarding:{register_called_on_every_launch_when_authorized,
   token_forwarded_on_every_callback,
   token_not_assumed_fixed_length, token_change_handled},
 failure:{did_fail_handler_records_and_measures,
   did_fail_restores_local_fallback,
   failed_server_registration_retried},
 server:{server_replaces_old_token, server_prunes_on_apns_410,
   server_environment_separation_recorded},
 exit:{token_deregistered_on_signout,
   token_deregistered_on_account_deletion,
   token_deregistered_on_permission_loss},
 measurement:{registration_result_measured_by_outcome,
   token_coverage_measured, stale_token_age_measured}}
"""
import json, sys

def check(d):
    fails = []
    inv = d.get("inventory") or {}
    if not inv.get("lifecycle_decision_recorded"):
        fails.append("DT-0 the token lifecycle is not recorded as a decision (which component registers, which endpoint receives the token, what happens on change / failure / exit -- an unrecorded lifecycle is whatever the oldest code path happens to do)")
    if not inv.get("token_owner_recorded"):
        fails.append("DT-0 the token's owner is not recorded (client forwards, server stores keyed by device or user -- if the keying is nowhere recorded, a token change cannot be told apart from a second device)")
    if not inv.get("environment_mapping_recorded"):
        fails.append("DT-0 the environment mapping is not recorded (a token is valid only in the APNs environment of the entitlement that produced it -- development builds mint sandbox tokens, distribution builds mint production tokens; with no recorded mapping and no environment sent or derived server-side, sandbox tokens silently enter the production send list and fail one device at a time)")
    fw = d.get("forwarding") or {}
    if not fw.get("register_called_on_every_launch_when_authorized"):
        fails.append("DT-1 registration is not requested on every launch once authorized (Apple's contract is register on launch and forward what APNs returns; registering only at the permission prompt means a token rotated while the app was closed is never learned)")
    if not fw.get("token_forwarded_on_every_callback"):
        fails.append("DT-1 the token is not forwarded on every registration callback (suppressing the forward because a locally cached token string looks unchanged breaks exactly when the cache and the server disagree -- the server, not the cache, is the record)")
    if not fw.get("token_not_assumed_fixed_length"):
        fails.append("DT-1 the token's length is assumed fixed (APNs does not guarantee a permanent token size; rejecting any token whose hex length is not exactly 64 turns a future APNs change into a total, silent registration failure for every device)")
    if not fw.get("token_change_handled"):
        fails.append("DT-1 a token change is not handled end to end (the new token must replace the old one under the same device/user key; a change that is forwarded but appended leaves the server choosing between a live token and a dead one)")
    fa = d.get("failure") or {}
    if not fa.get("did_fail_handler_records_and_measures"):
        fails.append("DT-2 the registration-failure callback does not record and measure the failure (didFailToRegister is the only signal APNs gives when no token will exist; an unmeasured failure path reads as 'no users' downstream)")
    if not fa.get("did_fail_restores_local_fallback"):
        fails.append("DT-2 the registration-failure path does not restore the local fallback the server-failure path restores (two failure doors into the same state must land in the same place; a didFail path that only flips a flag while the POST-failure path reschedules local delivery leaves the two doors disagreeing about whether the person still gets nudged)")
    if not fa.get("failed_server_registration_retried"):
        fails.append("DT-2 a failed server registration is not retried (a one-shot POST lost to a tunnel or a sleeping radio is permanent until reinstall unless the next launch or foregrounding re-registers and re-forwards)")
    sv = d.get("server") or {}
    if not sv.get("server_replaces_old_token"):
        fails.append("DT-3 the server does not replace the old token under the same key (accumulating tokens per device makes every send a lottery between live and dead tokens and inflates the apparent reachable audience)")
    if not sv.get("server_prunes_on_apns_410"):
        fails.append("DT-3 dead tokens are not pruned on APNs' unregistered signal (HTTP 410 / Unregistered is APNs saying the app is gone from that device; keeping the token means paying send cost and counting phantom reach forever)")
    if not sv.get("server_environment_separation_recorded"):
        fails.append("DT-3 sandbox and production tokens are not separated as a recorded server behaviour (the client payload carries no environment and no derivation from topic or entitlement is recorded, so the separation the entitlements create on device is lost at the server door)")
    ex = d.get("exit") or {}
    if not ex.get("token_deregistered_on_signout"):
        fails.append("DT-4 the token is not deregistered at sign-out (the server keeps addressing a person who left; on a shared or resold device the next person inherits the previous person's nudges)")
    if not ex.get("token_deregistered_on_account_deletion"):
        fails.append("DT-4 the token is not deregistered at account deletion (deletion that erases the account record but leaves a live device address keeps a delivery channel to a person the company claims to have forgotten)")
    if not ex.get("token_deregistered_on_permission_loss"):
        fails.append("DT-4 permission loss does not retire the token (when authorization is revoked the client simply stops registering, but the server's stored token stays sendable; the retirement must be an explicit deregistration, not the absence of a refresh)")
    me = d.get("measurement") or {}
    if not me.get("registration_result_measured_by_outcome"):
        fails.append("DT-5 registration outcomes are not measured by kind (registered / server-failed / APNs-failed / invalid-token must be separable, or a broken registration path hides inside aggregate notification metrics)")
    if not me.get("token_coverage_measured"):
        fails.append("DT-5 token coverage is not measured (the share of active devices holding a fresh, server-confirmed token is the ceiling of the whole remote funnel; unmeasured, a registration break looks like a content problem)")
    if not me.get("stale_token_age_measured"):
        fails.append("DT-5 stale-token age is not measured (without the age of the token each send uses, rotation failures and accumulating dead tokens have no number and therefore no owner)")
    return fails

def main():
    if len(sys.argv) != 2:
        print("usage: token_lifecycle_check.py <state.json>"); return 2
    with open(sys.argv[1]) as f:
        d = json.load(f)
    fails = check(d)
    print(f"app: {d.get('app','?')}")
    if fails:
        print(f"FAIL {len(fails)}")
        for x in fails:
            print(f" - {x}")
        return 1
    print("PASS")
    return 0

if __name__ == "__main__":
    sys.exit(main())
