#!/usr/bin/env python3
"""txn-verification-check: deterministic gate for the TRANSACTION
VERIFICATION surface (StoreKit signed transactions + RevenueCat Trusted
Entitlements). Stdlib only, offline, free.
Sources:
- Apple (WWDC, StoreKit): after a purchase, check the transaction
  IsVerified before delivering content and calling finish(); listen to
  Transaction.updates for transactions created/updated outside the app;
  Transaction.currentEntitlements is the source of truth for
  non-consumables and subscriptions and already filters refunded,
  revoked and expired states - grant access only once the transaction
  is verified. StoreKit 2 transactions are signed (JWS); the payload
  carries product, environment (Sandbox vs Production) and bundle
  identity that must match the app before the payload is trusted.
- RevenueCat Handbook, Ch.15 Security (Trusted Entitlements): the
  default trusts CustomerInfo responses without cryptographic
  verification. INFORMATIONAL enables response signature verification -
  failures are logged but do NOT block access. ENFORCED makes
  EntitlementInfo.isActive return false for any response that fails
  signature verification. Even with ENFORCED, server-side access
  decisions must not rest solely on what the client reports: verify
  entitlement on the server via the RevenueCat REST API or a
  webhook-updated database. Enabling the mode alone protects nothing
  unless code reads the verification result and acts on it.
Exit 0=PASS, 1=FAIL.
"""
import json, sys
def check(d):
    f=[]
    dec=d.get("decision") or {}
    if not dec.get("authority_recorded"): f.append("TV-0 the verification authority is not recorded as a decision (who verifies the signed transaction: RevenueCat backend, own server via the App Store Server API, or on-device StoreKit 2 verification - and for which surfaces)")
    if not dec.get("owner_recorded"): f.append("TV-0 no single transaction-verification owner is recorded")
    if not dec.get("mode_rationale_recorded"): f.append("TV-0 no recorded rationale for the verification mode actually in use (informational vs enforced, and what happens on failure) - the mode is drift or a copied default, not a decision")
    cm=d.get("client_mode") or {}
    if not cm.get("mode_set_explicitly"): f.append("TV-1 entitlement verification is not set explicitly at SDK configuration (the default trusts CustomerInfo responses without cryptographic verification)")
    if not cm.get("verification_result_read"): f.append("TV-1 no code reads the verification result attached to the entitlement info (enabling a mode protects nothing until code reads the result and acts on it; in informational mode a failed verification is invisible to the app)")
    if not cm.get("failure_policy_implemented"): f.append("TV-1 no implemented failure policy (enforced mode, or informational mode plus a recorded and implemented handling for failed verification - block, alert, or metric; a log line inside the vendor SDK that nobody reads is not a policy)")
    sk=d.get("storekit_signed") or {}
    if not sk.get("direct_verified_handling_present"): f.append("TV-2 no verified-only handling of signed StoreKit transactions is present in the app (any direct transaction path must grant only on a verified result; a fully delegated path must record that delegation instead of leaving the surface unexamined)")
    if not sk.get("jws_handling_recorded"): f.append("TV-2 how the signed transaction (JWS) reaches its verifier is not recorded (sent to the vendor backend by the SDK, forwarded to the own server, or verified on device) - the signed payload's route is unexamined")
    if not sk.get("environment_bundle_checked"): f.append("TV-2 environment (Sandbox vs Production) and bundle identity are not checked where transaction data is consumed (a sandbox transaction or another app's transaction must never grant production access)")
    sa=d.get("server_authority") or {}
    if not sa.get("server_decides_premium_access"): f.append("TV-3 the server does not decide premium access from verified entitlement state (client-reported plan/status remains the authority for server-gated value such as delivery volume or premium content)")
    if not sa.get("webhook_signature_verified"): f.append("TV-3 incoming subscription webhooks / server notifications are not signature-verified on the server (an unsigned lifecycle event can forge renewals, cancellations or refunds into the entitlement database)")
    if not sa.get("server_rechecks_via_api"): f.append("TV-3 the server does not recheck entitlement through the vendor REST API or the App Store Server API (the server's record is whatever the client last reported, never independently confirmed)")
    gb=d.get("grant_binding") or {}
    if not gb.get("binds_to_configured_entitlement"): f.append("TV-4 access is not bound to the configured entitlement identifier (gating on product IDs or local flags is brittle and drifts from the catalog)")
    if not gb.get("no_loose_fallback"): f.append("TV-4 a loose fallback grants from any active entitlement when the configured entitlement is absent (any product's entitlement silently becomes the premium gate)")
    if not gb.get("offline_cache_policy_recorded"): f.append("TV-4 no recorded policy for cached entitlement staleness (the SDK disk cache works offline with last-known state; how long stale access may persist is undecided)")
    ver=d.get("verification") or {}
    if not ver.get("unverified_case_tested"): f.append("TV-5 the unverified / tampered case is not tested (verification failures are silent, so an untested failure path is assumed-broken)")
    if not ver.get("failure_metrics_measured"): f.append("TV-5 verification failures are not counted or alerted (no way to know whether verification passes, fails, or is being probed)")
    if not ver.get("sandbox_production_e2e_tested"): f.append("TV-5 verification is not end-to-end tested in sandbox and production shapes (environment mix-ups surface only in production)")
    return f
if __name__=="__main__":
    data=json.load(open(sys.argv[1])); fails=check(data)
    if fails:
        print(f"FAIL ({len(fails)}):")
        [print(" -",x) for x in fails]; sys.exit(1)
    print("PASS")
