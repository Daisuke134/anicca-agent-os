#!/usr/bin/env python3
"""siwa-check: deterministic gate for the Sign in with Apple surface.
Stdlib only, offline, free.
Sources (read 2026-11-15):
- Apple TN3194, "Handling account deletions and revoking tokens for
  Sign in with Apple" (developer.apple.com technote, first published
  2025-10-03, updated 2026-11-01): securely transmit the identity token
  AND authorization code to the app server; verify the identity token
  and validate the authorization code via /auth/token; securely store
  the token response (identity, refresh, access tokens); observe
  ASAuthorizationAppleIDProvider.credentialRevokedNotification and use
  getCredentialState(forUserID:) to respond to revocation -- on
  revocation delete all user-related data (server, Keychain, local)
  and revert the client to an unauthenticated state.
- Apple ASAuthorizationAppleIDCredential documentation (quoted in
  practitioner references) and WWDC22: email, fullName and
  realUserStatus are returned only on the first authorization;
  subsequent sign-ins may return nil, so the app must cache them at
  first grant and never let a later nil overwrite the stored values.
Exit 0 = PASS, 1 = FAIL.
Input JSON: {app,
 inventory:{signin_surfaces_recorded, credential_states_defined,
   backend_token_flow_recorded},
 entry:{entitlement_present, ui_entry_reachable},
 mechanism:{nonce_hashed_and_sent, scopes_requested,
   authorization_code_transmitted, server_verification_evidenced},
 lifecycle:{credential_state_checked_on_launch,
   revoked_notification_observed, revocation_reverts_and_clears},
 first_grant:{name_email_captured_when_present,
   nil_grant_preserves_stored, tokens_stored_securely},
 errors_measurement:{cancellation_distinguished,
   signin_outcomes_counted}}
"""
import json, sys

def check(d):
    fails, warns = [], []
    inv = d.get("inventory") or {}
    if not inv.get("signin_surfaces_recorded"):
        fails.append("SA-0 the sign-in surfaces are not recorded (coordinator, presentation path, stored-session restore and sign-out must be enumerated before SIWA coverage can be audited)")
    if not inv.get("credential_states_defined"):
        fails.append("SA-0 the Apple credential states are not defined as a set (authorized / revoked / notFound / transferred are four different answers from getCredentialState; an undefined state set means at least one of them has no designed result)")
    if not inv.get("backend_token_flow_recorded"):
        fails.append("SA-0 the backend token flow is not recorded (TN3194: identity token + authorization code to the server, /auth/token validation, secure storage of the token response; an unrecorded backend is an unverified half of the sign-in)")
    en = d.get("entry") or {}
    if not en.get("entitlement_present"):
        fails.append("SA-1 the Sign in with Apple entitlement (com.apple.developer.applesignin) is missing (without it the authorization controller cannot run at all)")
    if not en.get("ui_entry_reachable"):
        fails.append("SA-1 no view can reach sign-in (a coordinator whose start/configure entry points have zero callers is a sign-in that exists in code but not in the product; a returning or new user has no way to invoke it)")
    me = d.get("mechanism") or {}
    if not me.get("nonce_hashed_and_sent"):
        fails.append("SA-2 no hashed nonce is set on the request and sent for verification (the nonce binds the identity token to this request; without it the token is replayable)")
    if not me.get("scopes_requested"):
        fails.append("SA-2 the request does not ask for the fullName/email scopes (without requestedScopes the credential returns neither, and the first-grant capture can never happen)")
    if not me.get("authorization_code_transmitted"):
        fails.append("SA-2 the authorization code is never transmitted to the server (TN3194 step 1-2: transmit identity token AND authorization code, validate the code via /auth/token; an identity-token-only flow never obtains Apple's refresh token, so later revocation and session-lifetime validation have nothing to work with)")
    if not me.get("server_verification_evidenced"):
        fails.append("SA-2 server-side verification of the identity token is not evidenced (the client sending a token is not verification; TN3194 expects the server to validate the token and Apple's public key before granting access)")
    li = d.get("lifecycle") or {}
    if not li.get("credential_state_checked_on_launch"):
        fails.append("SA-3 getCredentialState is never called (a stored local session is restored on launch without asking Apple whether the authorization still exists; a user who revoked the app in Settings keeps a signed-in app)")
    if not li.get("revoked_notification_observed"):
        fails.append("SA-3 credentialRevokedNotification is not observed (TN3194: observe it and use getCredentialState to respond to revocation and account-deletion events; without the observer the app learns about revocation never)")
    if not li.get("revocation_reverts_and_clears"):
        fails.append("SA-3 revocation does not revert the client and clear user data (TN3194: on revocation delete user data on server, in Keychain and locally, and revert to an unauthenticated state)")
    fg = d.get("first_grant") or {}
    if not fg.get("name_email_captured_when_present"):
        fails.append("SA-4 name/email are not captured when Apple provides them (they are provided only on the first authorization; a flow that ignores them at that moment can never recover them from Apple)")
    if not fg.get("nil_grant_preserves_stored"):
        fails.append("SA-4 a later sign-in's nil name/email can overwrite the stored values (Apple returns name/email only at first grant; rebuilding the stored credentials unconditionally from the latest credential erases the person's name and email on their second sign-in)")
    if not fg.get("tokens_stored_securely"):
        fails.append("SA-4 session tokens are not stored securely (TN3194: securely store user credentials -- tokens belong in the Keychain; a credential record carrying an access token in UserDefaults is readable by anything that can read the defaults plist)")
    em = d.get("errors_measurement") or {}
    if not em.get("cancellation_distinguished"):
        fails.append("SA-5 a user cancellation is not distinguished from a failure (dismissing the Apple sign-in sheet is ASAuthorizationError.canceled, not an error; treating it as failure signs the person out and records a failure that never happened)")
    if not em.get("signin_outcomes_counted"):
        fails.append("SA-5 sign-in starts and outcomes are not counted (without started / succeeded / cancelled / failed counts, a dead sign-in entry is indistinguishable from an unused one)")
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
