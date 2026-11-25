#!/usr/bin/env python3
"""consumption-response-check: deterministic gate for the CONSUMPTION
INFORMATION RESPONSE surface (App Store Server API Send Consumption
Information / RevenueCat Refund Control). Stdlib only, offline, free.
Sources:
- Apple App Store Server API "Send Consumption Information"
  (read in full via live browser, 2026-11-17): when a customer
  requests a refund, Apple sends a CONSUMPTION_REQUEST server
  notification; the developer may respond within 12 hours via
  PUT /inApps/v2/transactions/consumption/{transactionId}.
  Success is HTTP 202. The current ConsumptionRequest (v2, API 1.19+)
  has five fields: customerConsented (required, must be true - any
  other value is InvalidCustomerConsentedError), deliveryStatus
  (required, string enum DELIVERED / UNDELIVERED_*), sampleContent-
  Provided (required), consumptionPercentage (optional, 0-100000
  milliunits; must be 0 when not DELIVERED, and must NOT be sent
  for auto-renewable subscriptions, which Apple calculates itself),
  refundPreference (optional: GRANT_FULL / GRANT_PRORATED / DECLINE;
  GRANT_PRORATED requires 0 < percentage < 100000 where a percentage
  is allowed). The 12-field payload (accountTenure, appAccountToken,
  consumptionStatus, lifetimeDollarsPurchased/Refunded, platform,
  playTime, userStatus, ...) is ConsumptionRequestV1 (deprecated
  deliveryStatusV1) - a legacy shape, not the current one.
  Consent must be valid (freely given, specific, informed,
  unambiguous, opt-in, withdrawable) and must NOT be collected with
  the App Tracking Transparency prompt. If the customer has not
  consented, the notification is simply not answered.
  Apple makes the final refund decision; the response is evidence,
  not a verdict.
- RevenueCat "Configure refund policies" (Refund Control): with
  RevenueCat, RevenueCat receives the notification and responds under
  the project's first matching policy (preferences: prefer full
  refund / prefer decline / consumption data only / do not respond).
  Prerequisites: Apple App Store Server Notifications configured per
  app, and customer consent obtained - enabling consumption data
  sharing in RevenueCat is itself a confirmation that consent was
  obtained. Outcomes are monitored on the Refund Control page /
  Refund Requests Outcomes Chart.
This gate is the RESPONSE-PAYLOAD layer. It is not the refund-rate
measurement gate (refund-check, 2026-11-13, whose F-4 only asked
whether a response path exists) and not the in-app refund request
sheet gate (refund-sheet-check, 2026-11-17, the customer-facing
beginRefundRequest surface).
Exit 0=PASS, 1=FAIL.
"""
import json, sys
def check(d):
    f=[]
    dec=d.get("decision") or {}
    if not dec.get("decision_recorded"): f.append("CI-0 how CONSUMPTION_REQUEST notifications will be answered (direct App Store Server API, or RevenueCat Refund Control) is not recorded as a decision - the 12-hour clock starts at notification time, so an undecided route is an unanswered request")
    if not dec.get("owner_recorded"): f.append("CI-0 no single consumption-response owner is recorded")
    if not dec.get("refund_preference_policy_recorded"): f.append("CI-0 no refund-preference policy is recorded (which preference is sent for which customer/purchase segment, and why) - without it the preference sent to Apple is whatever a dashboard default or a hardcoded value happens to be, including a blanket decline the team never chose")
    con=d.get("consent") or {}
    if not con.get("consent_obtained_before_sharing"): f.append("CI-1 customer consent to share consumption data with Apple is not obtained (wording in terms or a consent flow) before sharing - Apple requires valid consent before personal data is sent through Send Consumption Information, and enabling sharing in RevenueCat is itself a confirmation that consent exists")
    if not con.get("no_send_without_consent"): f.append("CI-1 there is no rule that a request is simply not answered when the customer has not consented - customerConsented only ever carries true, so a non-consented send is both an Apple validation failure and a consent violation")
    if not con.get("consent_scope_covers_existing_customers"): f.append("CI-1 the consent scope is not checked for existing customers (terms updated after purchase) - consent collected only from new customers does not cover the installed base whose refunds will actually arrive")
    dat=d.get("data_foundation") or {}
    if not dat.get("transaction_id_retrievable"): f.append("CI-2 the transaction identifier from the CONSUMPTION_REQUEST notification is not stored retrievably per customer - the Send Consumption Information call is keyed by exactly that identifier")
    if not dat.get("delivery_and_sample_facts_known"): f.append("CI-2 the two factual anchors of the v2 payload cannot be determined truthfully per transaction (deliveryStatus: was this purchase delivered and working, or undelivered and why; sampleContentProvided: was a free sample, trial, or feature information offered before purchase) - both are required fields, and guessing them is a false statement to Apple")
    if not dat.get("usage_data_computable"): f.append("CI-2 the customer's actual usage cannot be computed from retained records where a consumption share is reportable - a percentage invented at response time, or a fixed value sent for everyone, misstates each individual customer to Apple")
    res=d.get("response") or {}
    if not res.get("all_required_fields_sent"): f.append("CI-3 not all required v2 ConsumptionRequest fields are sent (customerConsented, deliveryStatus, sampleContentProvided) in the current v2 shape - answering in the deprecated 12-field V1 shape, or omitting a required field, is a malformed say in the refund decision")
    if not res.get("consumption_percentage_rules_followed"): f.append("CI-3 the consumptionPercentage rules are not followed (derived from actual usage where sent; never sent for auto-renewable subscriptions, which Apple calculates itself - sending it is an error; GRANT_PRORATED only with a strictly partial percentage where a percentage is allowed)")
    if not res.get("delivery_consumption_consistent"): f.append("CI-3 delivery and consumption are not kept consistent (content not delivered means the consumed share is 0) - an inconsistent payload is rejected by Apple and, worse, claims use that never happened")
    if not res.get("refund_preference_matches_policy"): f.append("CI-3 the refundPreference actually sent is not checked against the recorded policy (CI-0) - the preference is the one explicit ask the developer gets to make, and an unchecked one can silently be a blanket decline")
    tim=d.get("timing_and_outcome") or {}
    if not tim.get("response_within_12h_automated"): f.append("CI-4 responses are not automated to land within Apple's 12-hour window - a manual path answers late or never, and after 12 hours Apple decides with no input from the developer at all")
    if not tim.get("outcome_linked_and_measured"): f.append("CI-4 the outcome of each request (response accepted, then REFUND or REFUND_DECLINED) is not linked back per request and measured - the team cannot learn whether its preference policy helps, harms, or is ignored")
    if not tim.get("entitlement_reflects_refund"): f.append("CI-4 a granted refund (REFUND) does not flow back into the entitlement state the app reads - a refunded customer keeps access the store has already taken back")
    ver=d.get("verification") or {}
    if not ver.get("sandbox_consumption_tested"): f.append("CI-5 no Sandbox end-to-end test of a consumption response exists (notification received -> payload sent -> acceptance observed) - the first real run of this path is a real customer's refund, on a 12-hour clock")
    if not ver.get("field_mapping_unit_tested"): f.append("CI-5 the mapping from retained records to payload fields (delivery status, sample provision, consumption percentage and its auto-renewable exclusion, delivery consistency) is not unit-tested - field errors surface as Apple rejections or silent misstatements, not as test failures")
    return f
if __name__=="__main__":
    data=json.load(open(sys.argv[1])); fails=check(data)
    if fails:
        print(f"FAIL ({len(fails)}):")
        [print(" -",x) for x in fails]; sys.exit(1)
    print("PASS")
