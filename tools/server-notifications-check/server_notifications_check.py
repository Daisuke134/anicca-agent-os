#!/usr/bin/env python3
"""server-notifications-check: deterministic gate for the APP STORE
SERVER NOTIFICATIONS V2 / server-side entitlement truth surface
(which path carries server truth, JWS verification before trust,
durable ack + idempotency + ordering, missed-notification recovery,
event coverage incl. refund/revoke, client verification mode, and
reconciliation/measurement).
Stdlib only, offline, free.
Sources (read 2026-11-15):
- Apple, App Store Server Notifications V2 (developer.apple.com/
  documentation/appstoreservernotifications and linked V2 pages,
  via search + secondary full reads where the official JS page could
  not be text-fetched): Apple POSTs {signedPayload} to the URL set in
  App Store Connect (separate production and sandbox URLs); the
  payload and the nested signedTransactionInfo / signedRenewalInfo
  are JWS (ES256, x5c chain to an Apple root) and must be VERIFIED
  before they are trusted -- decoding without verification lets
  anyone who finds the endpoint forge entitlements. Without a 200
  response Apple retries V2 notifications five times (1, 12, 24, 48,
  72 hours, production only; sandbox tries once); missed
  notifications are recoverable via the App Store Server API Get
  Notification History endpoint. Apple's open-source App Store
  Server Library verifies and decodes.
- RevenueCat (docs + community + implementation guides faithful to
  the official docs, read 2026-11-15): RevenueCat receives the store
  server notifications itself and normalizes them into webhooks;
  webhook handlers must verify the signature, be idempotent on the
  event id, persist before acking, NOT order by arrival or by the
  per-attempt signature timestamp, re-read the authoritative current
  customer/entitlement state, and reconcile periodically because
  deliveries can arrive out of order, be retried, or be missed.
Exit 0 = PASS, 1 = FAIL.
Input JSON: {app,
 inventory:{server_truth_path_decided, asc_or_dashboard_state_evidenced,
   relay_to_own_backend_evidenced, sandbox_and_production_both_covered},
 verification:{signatures_verified_before_trust,
   nested_transaction_and_renewal_verified, environment_checked,
   no_decode_only_path_in_production},
 delivery:{ack_only_after_durable_persist, event_id_dedup_idempotent,
   out_of_order_safe_via_authoritative_reread,
   missed_recovered_via_history_or_reconciliation},
 coverage:{renew_expire_billing_grace_handled,
   refund_and_revoke_remove_access, price_and_offer_changes_handled,
   test_notification_verified_end_to_end},
 client_honesty:{verification_mode_enforced_or_gap_recorded,
   access_follows_live_entitlement, offline_cache_bounded},
 measurement:{server_events_logged_with_ids,
   reconciliation_scheduled, client_server_divergence_measured}}
"""
import json, sys

def check(d):
    fails = []
    inv = d.get("inventory") or {}
    if not inv.get("server_truth_path_decided"):
        fails.append("SN-0 no server-truth path is decided and recorded (direct App Store Server Notifications V2 to an own endpoint, RevenueCat receiving them and relaying webhooks, or an explicit client-only acceptance -- an unrecorded delegation is not a decision, and nobody can say who learns that a subscription expired, was refunded, or was revoked when the app is not running)")
    if not inv.get("asc_or_dashboard_state_evidenced"):
        fails.append("SN-0 the configured state is not evidenced (the production and sandbox notification URLs in App Store Connect, and the RevenueCat dashboard's store-notification / webhook configuration, live outside the repo; until they are read back and recorded, 'the server knows' is an assumption, not a fact)")
    if not inv.get("relay_to_own_backend_evidenced"):
        fails.append("SN-0 no relay from the notification receiver to the app's own backend is evidenced (RevenueCat normalizing a renewal is not the same as the company's own entitlement/usage server learning it; the app's own server endpoint is read for usage counts only and explicitly does not change entitlement state)")
    if not inv.get("sandbox_and_production_both_covered"):
        fails.append("SN-0 sandbox and production are not both covered and separated (Apple keeps separate notification URLs per environment and retries only in production; a setup verified only in sandbox proves nothing about the production path that carries real revenue)")
    ver = d.get("verification") or {}
    if not ver.get("signatures_verified_before_trust"):
        fails.append("SN-1 signatures are not verified before trust on every hop that grants or removes access (the outer signedPayload and any webhook signature must be checked against the raw bytes / Apple chain before state changes; decode-only handling lets anyone who discovers the endpoint POST a forged renewal or refund)")
    if not ver.get("nested_transaction_and_renewal_verified"):
        fails.append("SN-1 the nested signedTransactionInfo and signedRenewalInfo are not independently verified (V2 nests signed payloads inside the signed payload; verifying only the outer envelope leaves the money-bearing inner transaction unverified)")
    if not ver.get("environment_checked"):
        fails.append("SN-1 the notification environment is not checked (payloads carry Sandbox vs Production; applying a sandbox event to a production user -- or ignoring the distinction -- corrupts entitlement and revenue state)")
    if not ver.get("no_decode_only_path_in_production"):
        fails.append("SN-1 a decode-without-verify path can reach production (useful in development for logging shape, fatal as a grant path: the signature check is the only thing separating Apple from an attacker)")
    dl = d.get("delivery") or {}
    if not dl.get("ack_only_after_durable_persist"):
        fails.append("SN-2 success is acknowledged before the event is durably persisted (Apple retries a V2 notification only five times over ~6.5 days and RevenueCat retries webhooks on a short ladder; an ack-then-crash handler loses the event forever once retries are exhausted)")
    if not dl.get("event_id_dedup_idempotent"):
        fails.append("SN-2 processing is not idempotent on the event/notification id (retries reuse the same event id by design; a handler without a unique-id record applies renewals, refunds and expirations twice)")
    if not dl.get("out_of_order_safe_via_authoritative_reread"):
        fails.append("SN-2 state is applied in arrival order instead of by re-reading the authoritative current state (deliveries and retries arrive out of order; the per-attempt signature timestamp is recomputed on every retry and is not an ordering key -- last-arriving stale state must not overwrite newer state)")
    if not dl.get("missed_recovered_via_history_or_reconciliation"):
        fails.append("SN-2 permanently missed notifications are never recovered (after the retry ladder ends, only Get Notification History / a periodic reconciliation against the store or RevenueCat can find the gap; without it, a multi-day outage becomes permanent entitlement and revenue drift)")
    cov = d.get("coverage") or {}
    if not cov.get("renew_expire_billing_grace_handled"):
        fails.append("SN-3 the lifecycle core is not all handled (DID_RENEW, EXPIRED, DID_FAIL_TO_RENEW and grace-period expiry each change access differently; handling purchase but not expiry keeps cancelled users premium and misstates retention)")
    if not cov.get("refund_and_revoke_remove_access"):
        fails.append("SN-3 refunds and revocations do not remove access (REFUND / REVOKE are the events where the store takes money back; a server that only ever grants turns refunds into free premium and inflates revenue that was returned)")
    if not cov.get("price_and_offer_changes_handled"):
        fails.append("SN-3 price-increase and offer events are not handled (price-increase consent outcomes and promotional/intro transitions change what renews and at what price; unhandled, the server's price and eligibility state silently diverges from the store's)")
    if not cov.get("test_notification_verified_end_to_end"):
        fails.append("SN-3 the path was never verified end to end with Apple's test notification (Request a Test Notification exists precisely to prove endpoint, verification and handling before real money depends on them; an untested endpoint is a hope, not a pipeline)")
    ch = d.get("client_honesty") or {}
    if not ch.get("verification_mode_enforced_or_gap_recorded"):
        fails.append("SN-4 the client's entitlement verification mode gap is not recorded (StoreKit verification set to informational means a failed verification is surfaced as information, not enforced as a block; that may be a deliberate tradeoff, but unrecorded it reads as 'verified' while access can follow an unverified transaction)")
    if not ch.get("access_follows_live_entitlement"):
        fails.append("SN-4 client access does not follow the live entitlement (access cached from a past flag survives server-side expiry, refund and revocation; the client must re-derive access from the current CustomerInfo/entitlement whenever it changes)")
    if not ch.get("offline_cache_bounded"):
        fails.append("SN-4 offline/stale entitlement cache is unbounded (a device that never revalidates keeps premium indefinitely after a server-side revocation; a staleness bound or revalidation-on-launch rule is the minimum honesty)")
    me = d.get("measurement") or {}
    if not me.get("server_events_logged_with_ids"):
        fails.append("SN-5 server notification events are not logged with their ids (without an event ledger -- id, type, environment, resulting state -- a missed, duplicated or misapplied event cannot be found, counted or replayed)")
    if not me.get("reconciliation_scheduled"):
        fails.append("SN-5 no reconciliation is scheduled (client state, own-server state and store/RevenueCat state drift independently; only a scheduled comparison turns silent drift into a counted, fixable number)")
    if not me.get("client_server_divergence_measured"):
        fails.append("SN-5 client-vs-server divergence is not measured (the share of users whose app shows premium while the server says expired -- or the reverse -- is the surface's health metric; unmeasured, every other gate's failure stays invisible)")
    return fails

def main():
    if len(sys.argv) != 2:
        print("usage: server_notifications_check.py <state.json>"); return 2
    with open(sys.argv[1]) as f:
        d = json.load(f)
    fails = check(d)
    print(f"app: {d.get('app','?')}")
    if fails:
        print(f"FAIL ({len(fails)})")
        for x in fails:
            print(f" - {x}")
        return 1
    print("PASS")
    return 0

if __name__ == "__main__":
    sys.exit(main())
