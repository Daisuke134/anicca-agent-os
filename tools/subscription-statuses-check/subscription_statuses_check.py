#!/usr/bin/env python3
"""subscription-statuses-check: deterministic gate for the SUBSCRIPTION
STATUSES surface (enumerating a customer's current auto-renewable
subscription statuses via Apple Get All Subscription Statuses and acting
on the five status codes). Stdlib only, offline, free.
Endpoint semantics (Apple App Store Server API, Get All Subscription
Statuses): GET https://api.storekit.apple.com/inApps/v1/subscriptions/
{transactionId} (sandbox host api.storekit-sandbox.apple.com), addressed
by any transactionId of the customer. Response StatusResponse carries
environment + data[] grouped by subscriptionGroupIdentifier; each group
holds lastTransactions[] with, per product, the LAST transaction only:
originalTransactionId, status, signedTransactionInfo, signedRenewalInfo
(both JWS, to be verified before trust). Status codes: 1 active,
2 expired, 3 billing retry period, 4 grace period, 5 revoked. An
optional status query filter exists server-side. A customer with no
auto-renewable subscriptions returns an empty data array (success, not
an error). Errors: 400 / 401 / 404 / 429 / 500.
NOTE: the developer.apple.com page itself could not be text-fetched in
the 2026-11-17 16:07 run (browser-service failure, not retried per
run rules); semantics above are the endpoint's documented shape as
carried in this workspace's prior server-API gate work and must be
re-verified against the live page on the next successful read.
Exit 0=PASS, 1=FAIL.
"""
import json, sys
def check(d):
    f=[]
    dec=d.get("decision") or {}
    if not dec.get("decision_recorded"): f.append("SS-0 subscription-status enumeration (reading every current subscription status of a customer from Apple, grouped by subscription group) is not recorded as a decided surface - subscriber state is inferred only from the client entitlement flag")
    if not dec.get("owner_recorded"): f.append("SS-0 no single subscription-status owner is recorded (status reads, the code mapping and the distribution count are ongoing work, not a one-time lookup)")
    if not dec.get("canonical_source_recorded"): f.append("SS-0 the canonical source for subscription statuses is not recorded (Apple Get All Subscription Statuses, GET /inApps/v1/subscriptions/{transactionId}) - every reader invents their own partial view of who is active, in grace, in billing retry, expired or revoked")
    fou=d.get("foundation") or {}
    if not fou.get("transaction_key_stored"): f.append("SS-1 no per-customer transaction identifier (transactionId / originalTransactionId) is stored - the statuses call is addressed by exactly that key, so the read cannot even be addressed")
    if not fou.get("server_api_credentials_verified"): f.append("SS-1 the App Store Server API credentials (key, issuer, bundle for the JWT) are not verified as working - a 401 on the day a status read is first needed is the failure mode, not a check")
    if not fou.get("jws_verified_both"): f.append("SS-1 the returned signedTransactionInfo and signedRenewalInfo (JWS) are not both signature-verified before being trusted - status records that drive access, support answers and win-back targeting must not be accepted on an unverified payload, and the environment (Sandbox vs Production) must be checked")
    rea=d.get("reading") or {}
    if not rea.get("all_groups_and_products_iterated"): f.append("SS-2 the response's data[] is not fully iterated (every subscription group, every product's lastTransactions entry) - reading only the first group or the configured entitlement's product misses second products, crossgrades and legacy plans")
    if not rea.get("all_five_status_codes_mapped"): f.append("SS-2 not all five status codes are mapped to a meaning and an action (1 active / 2 expired / 3 billing retry / 4 grace period / 5 revoked) - an unmapped code is silently read as inactive or active, and a client-side string like trialing/active/canceled/expired is not the server's five-code state")
    if not rea.get("last_transaction_semantics_recorded"): f.append("SS-2 the endpoint's semantics are not recorded: it returns the LAST transaction per product, not a transaction history - treating it as history invents renewals that were never read, and full history belongs to the transaction-history surface")
    use=d.get("use") or {}
    if not use.get("billing_retry_grace_acted_distinctly"): f.append("SS-3 billing retry (3) and grace period (4) are not acted on distinctly - both are saveable windows with different clocks and different messages; conflating them (or reading neither) wastes the only interval where a failing payment method can still be fixed before expiry")
    if not use.get("revoked_expired_remove_access"): f.append("SS-3 revoked (5) and expired (2) statuses do not reach the access state - a customer Apple says is revoked keeping premium is both a revenue leak and a false subscriber count")
    if not use.get("support_lookup_uses_statuses"): f.append("SS-3 support and win-back lookups do not read subscription statuses - 'am I subscribed, why did it stop' is answered from a client-cached flag instead of the store's current per-product state")
    mea=d.get("measurement") or {}
    if not mea.get("status_distribution_counted"): f.append("SS-4 the subscriber base is not counted by status code (how many are in grace, in billing retry, revoked) - the saveable population is invisible, so no save effort can be sized or judged")
    if not mea.get("status_transitions_tracked"): f.append("SS-4 status transitions are not tracked over time (active -> billing retry -> grace -> expired/revoked, and recoveries back) - without transitions, dunning and grace outcomes cannot be told apart from churn that was never at risk")
    if not mea.get("divergence_vs_entitlement_measured"): f.append("SS-4 divergence between the server statuses and the client/RevenueCat entitlement view is not measured - the two views disagree exactly at refunds, revocations and cross-device cases, and unmeasured the disagreement is read as truth")
    ver=d.get("verification") or {}
    if not ver.get("sandbox_e2e_tested"): f.append("SS-5 no sandbox end-to-end status walk exists (sandbox host, sandbox subscription in each reachable state, statuses read, mapped, acted on) - the production read is first exercised on a real subscriber incident")
    if not ver.get("five_code_mapping_unit_tested"): f.append("SS-5 the five-code mapping is not unit-tested (all five codes, plus unknown/future codes failing safe) - the mapping's correctness rests on reading the docs once")
    if not ver.get("no_subscriptions_empty_handled"): f.append("SS-5 the no-subscriptions case is not handled as a success (a customer with no auto-renewable subscriptions returns an empty data array) - 'no subscriptions' risks being recorded as a read failure and retried or alarmed forever, and lifetime/non-renewing purchases must not be misread as missing")
    return f
if __name__=="__main__":
    data=json.load(open(sys.argv[1])); fails=check(data)
    if fails:
        print(f"FAIL ({len(fails)}):")
        [print(" -",x) for x in fails]; sys.exit(1)
    print("PASS")
