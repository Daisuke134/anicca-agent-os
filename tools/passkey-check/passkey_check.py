#!/usr/bin/env python3
"""passkey-check: deterministic gate for the PASSKEY / PASSWORDLESS AUTH surface.
Stdlib only, offline, free.
Source (Apple Developer, Passkeys Overview https://developer.apple.com/passkeys/):
- Passkeys replace passwords with cryptographic key pairs (FIDO/W3C); servers
  keep only public keys, credentials are bound to the app/website (phishing
  resistant), synced via iCloud Keychain, used via AutoFill + Face ID/Touch ID.
- Passkeys work alongside passwords / existing sign-in, so adoption does not
  require removing the existing auth path.
- An app may only create/use a passkey for a domain it declares via the
  webcredentials associated-domain entitlement, matched by the domain's
  apple-app-site-association file naming the app; the server's relying-party
  identifier must be that domain.
Exit 0=PASS, 1=FAIL.
"""
import json, sys
def check(d):
    f=[]
    dec=d.get("decision") or {}
    if not dec.get("rp_id_recorded"): f.append("PK-0 relying-party identifier is not recorded as a decision (which domain passkeys are bound to is undecided, and changing it later orphans every existing passkey)")
    if not dec.get("passkey_owner_recorded"): f.append("PK-0 no single passkey/auth owner is recorded")
    if not dec.get("adoption_decision_recorded"): f.append("PK-0 no recorded adoption decision for passkeys (supported / deferred with reason) - the surface is absent by drift, not by decision")
    asc=d.get("association") or {}
    if not asc.get("webcredentials_entitlement_present"): f.append("PK-1 no webcredentials associated-domain entitlement (the app does not declare the domain it may create passkeys for)")
    if not asc.get("aasa_published_and_verified"): f.append("PK-1 apple-app-site-association for webcredentials is not published and verified on the RP domain (the domain side of the association is missing, so passkey creation fails silently)")
    if not asc.get("rp_id_matches_associated_domain"): f.append("PK-1 the server relying-party ID does not provably match the associated domain")
    reg=d.get("registration") or {}
    if not reg.get("server_challenge_for_registration"): f.append("PK-2 no server-issued single-use challenge for passkey registration (registration without a server challenge is replayable)")
    if not reg.get("registration_request_implemented"): f.append("PK-2 no ASAuthorizationPlatformPublicKeyCredential registration request is implemented in the app")
    if not reg.get("server_stores_public_key_only"): f.append("PK-2 the server does not store the credential public key (ID + public key) as the passkey record")
    asr=d.get("assertion") or {}
    if not asr.get("assertion_request_implemented"): f.append("PK-3 no passkey assertion (sign-in) request is implemented")
    if not asr.get("conditional_autofill_ui"): f.append("PK-3 no conditional / AutoFill passkey UI on the sign-in field (passkeys are surfaced through AutoFill; a separate buried flow loses the seamless path Apple specifies)")
    if not asr.get("coexists_with_existing_auth"): f.append("PK-3 passkeys do not coexist with the existing sign-in path (Apple's model is alongside, not a forced migration)")
    life=d.get("lifecycle") or {}
    if not life.get("revocation_and_signout_handled"): f.append("PK-4 credential revocation / sign-out handling for passkeys is not implemented or recorded")
    if not life.get("recovery_path_without_passkey"): f.append("PK-4 no account-recovery path that does not rely on the passkey itself (a lost device must not mean a lost account)")
    if not life.get("deletion_removes_credentials"): f.append("PK-4 account deletion does not remove stored passkey public keys")
    ver=d.get("verification") or {}
    if not ver.get("registration_assertion_e2e_tested"): f.append("PK-5 registration + assertion are not end-to-end tested (association failures are silent, so untested passkeys are assumed-broken)")
    if not ver.get("replay_protection_checked"): f.append("PK-5 server challenge single-use / sign-count or replay protection is not checked")
    if not ver.get("adoption_metrics_measured"): f.append("PK-5 passkey adoption / sign-in success is not measured (no way to know whether the passwordless path is used or failing)")
    return f
if __name__=="__main__":
    data=json.load(open(sys.argv[1])); fails=check(data)
    if fails:
        print(f"FAIL ({len(fails)}):")
        [print(" -",x) for x in fails]; sys.exit(1)
    print("PASS")
