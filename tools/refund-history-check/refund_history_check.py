#!/usr/bin/env python3
"""refund-history-check: deterministic gate for REFUND HISTORY reconciliation
(enumerating a customer's Apple-approved refunds via Get Refund History and
reconciling them against the live REFUND notification stream). Stdlib only,
offline, free.
Sources (read 2026-11-17):
- Apple "Get Refund History" (App Store Server API 1.6+), full read via live
  browser after browser.open failed: GET
  https://api.storekit.apple.com/inApps/v2/refund/lookup/{anyTransactionId}
  (sandbox host api.storekit-sandbox.apple.com). anyTransactionId is any
  originalTransactionId / transactionId / appTransactionId of the customer.
  Response RefundHistoryResponse: revision + hasMore + signedTransactions
  (up to 20 JWS transactions, sorted ascending by revocationDate, empty array
  when the customer has no approved refunds). While hasMore is true, call
  again with the response's revision token; the final page's token can be
  stored per customer and reused later so only new refunds are fetched.
  Only App-Store-approved refunds are returned (consumable, non-consumable,
  auto-renewable and non-renewing subscriptions), carrying the same
  information as REFUND server notifications - i.e. the recovery path for
  missed notifications. Refund date/reason live in the decoded payload's
  revocationDate / revocationReason. Errors: 400 invalid transaction id or
  revision, 401 invalid JWT, 404 transaction not found, 429 rate limit,
  500 general (one form retryable). No expiry period for revision tokens is
  stated on the pages read; invalid revisions surface as 400.
Exit 0=PASS, 1=FAIL.
"""
import json, sys
def check(d):
    f=[]
    dec=d.get("decision") or {}
    if not dec.get("decision_recorded"): f.append("RH-0 refund-history reconciliation (enumerating each customer's approved refunds from Apple and reconciling them against the live notification stream) is not recorded as a decided surface - refunds are handled only if a notification happens to arrive")
    if not dec.get("owner_recorded"): f.append("RH-0 no single refund-history owner is recorded (the sweep, the ledger and the drift count are ongoing work, not a one-time lookup)")
    if not dec.get("canonical_source_recorded"): f.append("RH-0 the canonical source for refund enumeration is not recorded (Apple Get Refund History, GET /inApps/v2/refund/lookup/{anyTransactionId}) - every reader invents their own partial view of who was refunded")
    fou=d.get("foundation") or {}
    if not fou.get("original_transaction_id_stored"): f.append("RH-1 no per-customer transaction identifier (originalTransactionId / transactionId / appTransactionId) is stored - the lookup is addressed by exactly that key, so the recovery call cannot even be addressed")
    if not fou.get("server_api_credentials_verified"): f.append("RH-1 the App Store Server API credentials (key, issuer, bundle for the JWT) are not verified as working - a 401 on the day the sweep is first needed is the failure mode, not a check")
    if not fou.get("jws_signature_verified"): f.append("RH-1 returned signedTransactions (JWS) are not signature-verified before being trusted - refund records that move entitlements and revenue must not be accepted on an unverified payload")
    if not fou.get("revocation_fields_read"): f.append("RH-1 revocationDate / revocationReason from the decoded payload are not read - a refund without its date and reason code cannot be attributed, segmented, or acted on")
    enu=d.get("enumeration") or {}
    if not enu.get("pagination_follows_revision_until_has_more_false"): f.append("RH-2 pagination does not follow the revision token until hasMore is false - a customer with more than 20 refunds silently loses every refund past the first page")
    if not enu.get("final_revision_token_stored_per_customer"): f.append("RH-2 the final page's revision token is not stored per customer - every sweep re-fetches the customer's whole refund history instead of only the refunds since the last sweep (Apple's documented incremental form)")
    if not enu.get("sweep_cadence_recorded"): f.append("RH-2 no sweep cadence is recorded (which customers, how often) - missed REFUND notifications are recovered by accident, if ever, instead of on a schedule")
    if not enu.get("dedup_by_transaction_id"): f.append("RH-2 refunds are not deduplicated by transactionId across the notification stream and the lookup - the same refund counted twice corrupts the refund rate and the ledger")
    rec=d.get("reconciliation") or {}
    if not rec.get("entitlement_reflects_refunds"): f.append("RH-3 a granted refund does not reach the entitlement state (no CustomerInfo stream / server state reflecting revocation) - a refunded customer can keep the access they were refunded for")
    if not rec.get("refund_ledger_recorded"): f.append("RH-3 no per-transaction refund ledger is recorded (transaction, product, revocationDate, revocationReason) - refunds exist only as an aggregate revenue dip with no auditable rows")
    if not rec.get("refunds_attributed_to_original_period"): f.append("RH-3 refunds are not attributed back to the original transaction's period - cohort refund rates are read in the processing month and every cohort looks better than it is")
    if not rec.get("drift_vs_notifications_measured"): f.append("RH-3 drift between the notification-derived refund set and the lookup-derived refund set is not measured - a silently dropped REFUND notification is indistinguishable from a customer who was never refunded")
    ver=d.get("verification") or {}
    if not ver.get("sandbox_lookup_e2e_tested"): f.append("RH-4 no sandbox end-to-end lookup walk exists (sandbox host, sandbox refund, enumerated, ledgered, entitlement reflected) - the production recovery path is first exercised during a real incident")
    if not ver.get("pagination_unit_tested"): f.append("RH-4 pagination is not unit-tested (multi-page, hasMore transitions, invalid revision 400 handled by restart, 429/500 retry policy) - the enumeration's completeness rests on reading the docs once")
    if not ver.get("empty_history_handled"): f.append("RH-4 the empty-history case is not handled as a success (signedTransactions is an empty array when a customer has no approved refunds) - 'no refunds' risks being recorded as a lookup failure and retried or alarmed forever")
    return f
if __name__=="__main__":
    data=json.load(open(sys.argv[1])); fails=check(data)
    if fails:
        print(f"FAIL ({len(fails)}):")
        [print(" -",x) for x in fails]; sys.exit(1)
    print("PASS")
