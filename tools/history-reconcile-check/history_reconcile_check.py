#!/usr/bin/env python3
"""history-reconcile-check: deterministic gate for the HISTORY
RECONCILIATION surface (App Store Server API history endpoints used
to recover missed server notifications and backfill entitlements).
Stdlib only, offline, free.
Sources (read in full via live browser, 2026-11-17):
- Apple "Get Notification History" (API 1.5+):
  POST /inApps/v1/notifications/history. Body NotificationHistory-
  Request requires startDate/endDate (ms). Window: last 180 days
  production, 30 days sandbox. Pages of max 20; follow paginationToken
  with the SAME request body while hasMore. onlyFailures=true returns
  notifications that did not reach the server (incl. in-retry).
  transactionId and notificationType are mutually exclusive filters.
  Each item carries sendAttempts (max 6) and the signedPayload (JWS).
  History reflects state at first send time, NOT current state.
- Apple "Get Transaction History" (API 1.12+):
  GET /inApps/v2/history/{anyTransactionId}; anyTransactionId may be
  an originalTransactionId, transactionId, or appTransactionId.
  Pages of max 20; revision token required on every request after the
  first, with the same query parameters, while hasMore. Response is
  signedTransactions (JWS) + environment + bundleId.
- Apple "Get All Subscription Statuses" (API 1.0+):
  GET /inApps/v1/subscriptions/{anyTransactionId}; status values
  1 active / 2 expired / 3 billing retry / 4 grace period / 5 revoked.
  This is the CURRENT-state arbiter for auto-renewable subscriptions;
  notification history is not.
- RevenueCat webhook guidance (docs/community, secondary): webhooks
  are a trigger to re-read current subscriber state via the REST API
  (GET /subscribers), not the state itself; a polling/sync system is
  the recommended robust shape, because a missed delivery otherwise
  becomes permanent drift.
This gate is the RECOVERY/BACKFILL layer. It is not the live-receipt
server-notifications gate (server-notifications-check, 2026-11-16)
and not the transaction-verification gate (txn-verification-check).
Exit 0=PASS, 1=FAIL.
"""
import json, sys
def check(d):
    f=[]
    dec=d.get("decision") or {}
    if not dec.get("decision_recorded"): f.append("HR-0 how missed notifications / entitlement drift will be recovered (direct App Store Server API history endpoints, or a RevenueCat subscriber sync) is not recorded as a decision - live delivery alone is treated as lossless, which Apple does not guarantee")
    if not dec.get("owner_recorded"): f.append("HR-0 no single reconciliation owner is recorded")
    if not dec.get("cadence_recorded"): f.append("HR-0 no reconciliation cadence is recorded - the notification-history window is finite (180 days production / 30 days sandbox), so an unscheduled sweep can age out of recoverability entirely")
    fou=d.get("foundation") or {}
    if not fou.get("transaction_id_retrievable"): f.append("HR-1 no transaction identifier is stored retrievably per customer - both history endpoints are keyed by an anyTransactionId (originalTransactionId / transactionId / appTransactionId), so without one no backfill call can even be addressed")
    if not fou.get("credentials_verified"): f.append("HR-1 the calling credentials for the chosen route (App Store Server API signing key, or RevenueCat secret API key for the sync function) are not verified as present and working - a reconciliation job that cannot authenticate fails silently on its first real run")
    if not fou.get("environment_separated"): f.append("HR-1 production and sandbox are not kept separated in reconciliation (history windows, endpoints, and responses differ by environment; a sandbox record reconciled into production state, or vice versa, corrupts entitlements)")
    notif=d.get("notification_history") or {}
    if not notif.get("sweep_scheduled_within_window"): f.append("HR-2 no scheduled Get Notification History sweep runs inside the retention window (production 180 days / sandbox 30 days) - failures older than the window are unrecoverable by design")
    if not notif.get("only_failures_checked"): f.append("HR-2 failed deliveries are not specifically swept (onlyFailures=true) and their sendAttempt results are not reviewed - the sweep that matters most is the one listing what never arrived")
    if not notif.get("pagination_followed"): f.append("HR-2 notification-history pagination is not followed to completion (max 20 per page; reuse the paginationToken with the same request body while hasMore) - a first-page-only sweep silently drops the rest of the failure record")
    back=d.get("backfill") or {}
    if not back.get("transaction_history_backfill"): f.append("HR-3 affected customers are not backfilled with Get Transaction History (revision token on every request after the first, same query parameters, until hasMore is false) - a missed REFUND or renewal cannot be reconstructed from the notification alone")
    if not back.get("statuses_as_current_arbiter"): f.append("HR-3 current subscription state is not arbitrated by Get All Subscription Statuses (1 active / 2 expired / 3 billing retry / 4 grace / 5 revoked) - Apple states history items reflect state at first send time, not current state, so replaying history as current truth re-applies stale states")
    if not back.get("signed_payloads_verified"): f.append("HR-3 signed payloads recovered from history (signedPayload / signedTransactions, JWS) are not verified before being applied - unverified replay trusts data whose signature was never checked")
    app=d.get("application") or {}
    if not app.get("idempotent_replay"): f.append("HR-4 recovered events are not applied idempotently (deduplicated by event/transaction identity, order-independent) - replaying a history page twice, or out of order, double-applies or resurrects old states")
    if not app.get("drift_measured"): f.append("HR-4 reconciliation drift is not measured (how many customers differed, which event types were missed, how often) - without a drift count the team cannot tell whether live delivery is healthy or quietly leaking entitlements and revenue")
    if not app.get("entitlement_reflects_reconciled"): f.append("HR-4 the reconciled state does not flow into the entitlement state the app reads - a backfill that updates a server table the app never reads changes nothing for the customer")
    ver=d.get("verification") or {}
    if not ver.get("sandbox_missed_event_tested"): f.append("HR-5 no sandbox end-to-end test recovers a deliberately missed notification through the history path (miss -> sweep -> backfill -> entitlement corrected) - the first real run is a real outage")
    if not ver.get("pagination_unit_tested"): f.append("HR-5 pagination/revision handling is not unit-tested (paginationToken for notifications, revision for transaction history, same parameters on follow-ups, stop at hasMore=false) - page-handling bugs surface as silently incomplete backfills")
    if not ver.get("out_of_order_tested"): f.append("HR-5 out-of-order / duplicate replay is not unit-tested (an older recovered event must not overwrite a newer live state) - reconciliation itself becomes a source of stale-state bugs")
    return f
if __name__=="__main__":
    data=json.load(open(sys.argv[1])); fails=check(data)
    if fails:
        print(f"FAIL ({len(fails)}):")
        [print(" -",x) for x in fails]; sys.exit(1)
    print("PASS")
