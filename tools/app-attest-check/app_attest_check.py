#!/usr/bin/env python3
"""app-attest-check: deterministic gate for the APP ATTEST / DEVICECHECK
integrity surface (DCAppAttestService + DCDevice).
Stdlib only, offline, free.
Sources (Apple Developer, DeviceCheck):
- Establishing your app's integrity / Validating apps that connect to your
  server: check DCAppAttestService.shared.isSupported first; generate a
  Secure-Enclave key once (generateKey), attest it once against a fresh
  server challenge (attestKey with SHA256 of the challenge as
  clientDataHash), and have the SERVER validate the attestation object
  (Apple App Attest root CA chain, credential certificate nonce ==
  SHA256(authData || SHA256(challenge)), key ID == SHA256(public key),
  RP ID == TeamID + BundleID) and store the public key + receipt.
- Every later protected request is signed with generateAssertion over a
  hash that binds the actual request payload; the server verifies the
  signature with the stored public key and requires the assertion sign
  counter to strictly increase (replay protection).
- The appattest-environment entitlement must match the build (development
  vs production); attestation outside critical flows, with backoff on
  failure. Keys are invalidated by reinstall / device restore.
- DCDevice (DeviceCheck proper) issues a per-device token the server
  exchanges with Apple to read/update two per-device bits that survive
  reinstall (the canonical use is one-per-device promo / trial state).
- App Attest proves app-instance integrity only: it does not replace user
  authentication, TLS, or authorization, and unsupported devices need a
  recorded fallback / risk decision rather than a silent pass or a hard
  block decided by drift.
Exit 0=PASS, 1=FAIL.
"""
import json, sys
def check(d):
    f=[]
    dec=d.get("decision") or {}
    if not dec.get("protected_operations_recorded"): f.append("AT-0 the operations App Attest will protect (which server requests require an attested key) are not recorded as a decision - integrity is unscoped, so either nothing is protected or protection is improvised per endpoint")
    if not dec.get("owner_recorded"): f.append("AT-0 no single App Attest / device-integrity owner is recorded")
    if not dec.get("adoption_decision_recorded"): f.append("AT-0 no recorded adoption decision for App Attest (adopt, or defer with a reason) - the surface is absent by drift, not by decision")
    rdy=d.get("readiness") or {}
    if not rdy.get("is_supported_checked"): f.append("AT-1 DCAppAttestService.isSupported is not checked before key generation (on unsupported devices/extensions the flow fails opaquely instead of taking a designed path)")
    if not rdy.get("environment_entitlement_matches_build"): f.append("AT-1 the com.apple.developer.devicecheck.appattest-environment entitlement is not set correctly per build (development vs production) - attestations from release builds are rejected or development keys leak into production")
    if not rdy.get("unsupported_fallback_recorded"): f.append("AT-1 no recorded fallback / risk decision for unsupported devices (a silent pass defeats the gate; a hard block by drift locks out legitimate users Apple expects to be handled)")
    att=d.get("attestation") or {}
    if not att.get("server_challenge_single_use"): f.append("AT-2 no server-issued single-use challenge for attestation (attestation without a fresh server challenge is replayable and proves nothing about this session)")
    if not att.get("attest_flow_implemented"): f.append("AT-2 the generateKey + attestKey flow is not implemented in the app (no Secure-Enclave key is ever created or attested)")
    if not att.get("server_validates_and_stores_key"): f.append("AT-2 the server does not validate the attestation object (Apple root chain, certificate nonce, key ID, RP ID = TeamID + BundleID) and store the public key + receipt - client-side attestation without server validation is theatre")
    asr=d.get("assertion") or {}
    if not asr.get("assertion_signs_protected_requests"): f.append("AT-3 protected requests are not signed with generateAssertion using the attested key (attestation alone, done once, does not protect any later request)")
    if not asr.get("hash_binds_request_payload"): f.append("AT-3 the assertion clientDataHash does not bind the actual request (method/path/body/challenge) - a captured assertion can be replayed against a different payload")
    if not asr.get("server_checks_counter_increasing"): f.append("AT-3 the server does not require the assertion sign counter to strictly increase (replayed assertions are accepted, so replay protection does not exist)")
    dcb=d.get("devicecheck_bits") or {}
    if not dcb.get("bits_use_decision_recorded"): f.append("AT-4 no recorded decision on the two per-device DeviceCheck bits (the canonical one-per-device promo/trial state that survives reinstall) - per-device abuse state is undecided")
    if not dcb.get("token_flow_present"): f.append("AT-4 the DCDevice token flow is not present (the app never generates a device token for the server to exchange with Apple)")
    if not dcb.get("server_reads_updates_bits"): f.append("AT-4 the server does not read/update the per-device bits via Apple's DeviceCheck API - device state, if any, is local and resets on reinstall")
    ver=d.get("verification") or {}
    if not ver.get("e2e_and_replay_tested"): f.append("AT-5 attestation + assertion are not end-to-end tested including replay / counter regression (integrity failures are silent, so untested attestation is assumed-broken)")
    if not ver.get("failure_and_fraud_metrics_measured"): f.append("AT-5 attestation/assertion failures and the receipt-based fraud metric are not measured (no way to know whether integrity checks pass, fail, or are being probed)")
    if not ver.get("key_lifecycle_reinstall_handled"): f.append("AT-5 the key lifecycle on reinstall / device restore (keys are invalidated; re-attestation is required) is not handled or recorded - restored users hit a dead key with no recovery path")
    return f
if __name__=="__main__":
    data=json.load(open(sys.argv[1])); fails=check(data)
    if fails:
        print(f"FAIL ({len(fails)}):")
        [print(" -",x) for x in fails]; sys.exit(1)
    print("PASS")
