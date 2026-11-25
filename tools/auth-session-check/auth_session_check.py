#!/usr/bin/env python3
"""auth-session-check: deterministic gate for the AUTH SESSION
LIFECYCLE surface (whether a signed-in session stays alive honestly:
the token-refresh path is actually wired into API calls, refresh
fires before expiry even when the stored expiry is missing, refresh
failures land somewhere explicit instead of silently attaching a dead
token, concurrent refreshes cannot race a rotating refresh token,
and the end of a session -- sign-out, deletion, terminal failure --
is a recorded state, not a silent degradation).
Stdlib only, offline, free.
Sources (read in full / relevant sections 2026-11-16):
- RFC 9700 "Best Current Practice for OAuth 2.0 Security" (IETF,
  January 2025) https://www.rfc-editor.org/rfc/rfc9700.html
  Section 2.2: "Refresh tokens for public clients MUST be
  sender-constrained or use refresh token rotation as described in
  Section 4.14." Section 4.14: with rotation the server issues a new
  refresh token with every refresh response and invalidates the
  previous one, retaining the relationship so a replayed invalidated
  token reveals a breach and the active token is revoked (forcing a
  fresh authorization grant); refresh tokens SHOULD expire after
  inactivity; servers MAY revoke on logout. Client-side consequence:
  a replacement refresh token in a refresh response must be persisted
  and the old one never presented again, and two concurrent refreshes
  presenting the same token are indistinguishable from a replay
  unless the client single-flights its refresh.
Exit 0 = PASS, 1 = FAIL.
"""
import json, sys

def check(d):
    fails = []
    dec = d.get("decision") or {}
    if not dec.get("lifecycle_decision_recorded"):
        fails.append("AS-0 no auth-session lifecycle decision is recorded (no document fixes the access/refresh lifetimes, the refresh endpoint contract, or what 'the session is over' means -- the lifecycle exists only as scattered code)")
    if not dec.get("bearer_vs_deviceid_surfaces_recorded"):
        fails.append("AS-0 which API surfaces authenticate with the Bearer token and which with device/user id headers is not recorded (both patterns coexist in the tree with no record of which is authoritative -- a surface can silently sit outside the session lifecycle entirely)")
    if not dec.get("server_rotation_or_sender_constraint_recorded"):
        fails.append("AS-0 no record that the server rotates refresh tokens (or sender-constrains them) with replay detection (RFC 9700 sec.2.2/4.14: public clients MUST use one of the two; the client already persists a replacement token when one arrives, but whether rotation/revocation actually happens server-side is unverified and unrecorded)")
    reach = d.get("reach") or {}
    if not reach.get("auth_header_helper_called_by_api_sites"):
        fails.append("AS-1 the auth-header/refresh helper is never called (zero call sites in the tree -- the only Bearer header in the app is set inside the helper itself, so the refresh path is dead code and no request ever benefits from it)")
    if not reach.get("all_authenticated_surfaces_use_helper"):
        fails.append("AS-1 not every authenticated surface goes through the session path (several services attach device-id/user-id headers directly, so their requests neither refresh nor fail with the session -- the app has two unconnected notions of 'signed in')")
    trig = d.get("refresh_trigger") or {}
    if not trig.get("proactive_refresh_with_skew"):
        fails.append("AS-2 there is no proactive refresh before expiry with a safety skew (requests ride the token to the exact expiry instant and fail mid-flight)")
    if not trig.get("expiry_recorded_at_signin"):
        fails.append("AS-2 the access-token expiry is not recorded at sign-in (without a stored expiry no proactive refresh can ever be scheduled)")
    if not trig.get("refresh_when_expiry_missing"):
        fails.append("AS-2 a missing stored expiry disables refresh forever (the trigger is guarded on the expiry existing; when the sign-in response omits expiresAt the token is never refreshed and never retried -- the fallback of refreshing on a 401 or decoding the token's own exp claim does not exist)")
    fail = d.get("failure") or {}
    if not fail.get("refresh_failure_kinds_distinguished"):
        fails.append("AS-3 refresh failures are not distinguished (no-refresh-token, network error, non-2xx and malformed body all collapse into the same silent return -- a revoked session and a tunnel outage are indistinguishable, in the logs and to the user)")
    if not fail.get("expired_token_not_attached_after_failed_refresh"):
        fails.append("AS-3 after a failed refresh the expired token is attached anyway (the helper falls through and sends the request with the dead credential, converting a refresh problem into a guaranteed 401 at the resource)")
    if not fail.get("single_refresh_and_retry_on_401"):
        fails.append("AS-3 a 401 does not trigger one refresh and one retry (the normalized unauthorized error type exists but has zero handling sites -- the first expired-token request is simply lost)")
    if not fail.get("terminal_failure_moves_to_explicit_state"):
        fails.append("AS-3 a terminal refresh failure (invalid/revoked refresh token) does not move the app to an explicit signed-out / re-auth state (the app stays 'signed in' holding a dead token, retrying the same corpse on every launch)")
    conc = d.get("concurrency") or {}
    if not conc.get("single_flight_refresh"):
        fails.append("AS-4 refresh is not single-flight (no in-flight guard exists; concurrent callers each POST the same refresh token -- under server rotation the second presentation is a replay, which RFC 9700 servers answer by revoking the active token: the race logs the user out)")
    if not conc.get("rotated_refresh_token_persisted_before_use"):
        fails.append("AS-4 a replacement refresh token from a refresh response is not persisted before further use (rotation makes the previous token single-use; losing the replacement -- or using the old one once more -- strands the session)")
    meas = d.get("measurement") or {}
    if not meas.get("refresh_attempts_and_outcomes_measured"):
        fails.append("AS-5 refresh attempts and outcomes are not measured by kind (no analytics or ledger distinguishes refreshed / failed-network / failed-revoked / skipped-no-expiry, so a fleet-wide session die-off would be invisible until it arrives as churn)")
    if not meas.get("signout_and_deletion_discard_refresh_token"):
        fails.append("AS-5 sign-out and account deletion do not discard the stored refresh token (the keychain delete path has zero call sites in the tree, so the long-lived credential survives the session it belonged to -- see also the Credential Storage Gate)")
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
