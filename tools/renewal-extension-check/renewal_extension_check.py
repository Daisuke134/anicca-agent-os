#!/usr/bin/env python3
"""renewal-extension-check: deterministic gate for the SUBSCRIPTION
RENEWAL DATE EXTENSION surface (App Store Server API goodwill /
outage compensation extensions). Stdlib only, offline, free.
Sources:
- Apple App Store Server API (via Apple's official app-store-server-
  library documentation, apple.github.io, read in full for the client
  methods): extendSubscriptionRenewalDate extends the renewal date of
  a customer's active subscription using the original transaction
  identifier; extendRenewalDateForAllActiveSubscribers uses a
  subscription's product identifier to extend the renewal date for all
  of its eligible active subscribers; getStatusOfSubscriptionRenewal-
  DateExtensions checks whether a (mass) request completed and gives
  the final count of successful or failed extensions, keyed by the
  requestIdentifier UUID and the productId.
- ExtendRenewalDateRequest fields (Apple API data types, confirmed in
  multiple independent client libraries generated from Apple's spec):
  extendByDays (required, 1-90 days), extendReasonCode (required:
  0 undeclared, 1 customer satisfaction, 2 other reasons, 3 service
  issue or outage), requestIdentifier (required, a caller-provided
  value that uniquely identifies the request, max 128 chars).
  MassExtendRenewalDateRequest adds productId (required) and an
  optional list of storefront country codes limiting eligibility.
  Errors include SubscriptionExtensionIneligible and
  SubscriptionMaxExtension (a subscription that already received the
  maximum allowed extensions).
- Apple overview article "Extending the renewal date for auto-
  renewable subscriptions" (read in full via live browser): the
  renewal date can be moved up to 90 days into the future, and at
  most twice within a year (365 days) per customer. Only active
  auto-renewable subscriptions with at least one previously paid
  period are eligible; free-offer-period, expired, inactive
  billing-retry, past-expiry grace-period, and already-twice-
  extended subscriptions are ineligible. An extension cannot be
  reversed once in effect, the extension period does not count
  toward the one year of paid service for commission, and after a
  successful extension Apple emails the customer the updated
  renewal date (Apple's mail states the date, not the team's
  reason - the team's own-voice explanation is a separate layer).
  Mass requests are asynchronous (hours to days), report per-
  subscription outcomes through App Store Server Notifications V2
  (RENEWAL_EXTENDED / RENEWAL_EXTENSION FAILURE / RENEWAL_EXTENSION
  SUMMARY on completion), and failed attempts can be retried
  individually with the failed subscription's originalTransactionId.
This gate is the SERVER/OPERATIONS layer for extensions. It is not
the billing grace period (dunning-grace gate), not a promotional
entitlement (a RevenueCat-side grant that does not move the store
renewal date), and not a win-back offer (winback-apple gate).
Exit 0=PASS, 1=FAIL.
"""
import json, sys
def check(d):
    f=[]
    dec=d.get("decision") or {}
    if not dec.get("decision_recorded"): f.append("RE-0 how renewal-date extensions will be used (triggers, surfaces, measurement) is not recorded as a decision - when an outage hits paying subscribers, the response will be improvised while the compensation window is already running")
    if not dec.get("owner_recorded"): f.append("RE-0 no single renewal-extension owner is recorded")
    if not dec.get("trigger_register_recorded"): f.append("RE-0 no trigger register distinguishes the legitimate cases (service issue or outage affecting subscribers, individual customer-satisfaction cases) from cases an extension must not be used for (masking ordinary churn, extending ineligible or expired subscriptions) - without it every incident invents its own policy")
    pre=d.get("prerequisites") or {}
    if not pre.get("original_transaction_id_stored"): f.append("RE-1 the original transaction identifier is not stored retrievably per subscriber on the server side - the individual extension endpoint is keyed by exactly that identifier, so at incident time the one value the call needs is the one value that was never kept")
    if not pre.get("server_api_credentials_verified"): f.append("RE-1 App Store Server API credentials (in-app-purchase key, issuer, bundle) are not verified as working - an extension capability that has never authenticated is a plan, not a capability")
    if not pre.get("eligibility_checked_before_call"): f.append("RE-1 eligibility (active subscription state) is not checked before an extension call - ineligible subscriptions return SubscriptionExtensionIneligible, and a run that discovers eligibility from Apple's errors has no clean target list")
    ind=d.get("individual") or {}
    if not ind.get("request_identifier_unique"): f.append("RE-2 requests do not carry a unique caller-provided requestIdentifier per extension request - the identifier is what makes a request identifiable and auditable; reusing or omitting it makes retries and records ambiguous")
    if not ind.get("extend_days_within_range"): f.append("RE-2 extendByDays is not constrained to Apple's 1-90 day range in the request builder - out-of-range values are rejected by Apple (InvalidExtendByDays) at the worst possible moment")
    if not ind.get("reason_code_matches_actual_reason"): f.append("RE-2 the extendReasonCode does not record the actual reason (1 customer satisfaction, 2 other, 3 service issue or outage; 0 undeclared is not a policy) - Apple's record of why subscribers were compensated, and the team's own incident accounting, both read this code")
    if not ind.get("response_and_new_expiry_recorded"): f.append("RE-2 the extension response (success and the new effective expiry/renewal date) is not recorded per subscriber - after the call nobody can answer who was actually extended, or until when")
    mass=d.get("mass") or {}
    if not mass.get("mass_limited_to_affected"): f.append("RE-3 a mass extension is not limited to the affected product (and storefronts, where the impact was regional) - extending every active subscriber for a partial outage spends the per-subscriber extension budget of people who were never harmed")
    if not mass.get("mass_status_polled_to_completion"): f.append("RE-3 mass extension requests are asynchronous but their status is never polled to completion with the requestIdentifier (success/failure counts) - 'request accepted' is reported as 'subscribers extended' while the final counts were never read")
    if not mass.get("mass_not_used_for_individual_case"): f.append("RE-3 there is no rule keeping individual cases on the individual endpoint - using the mass endpoint for one subscriber extends an entire product's subscriber base to fix one person's case")
    aft=d.get("aftermath") or {}
    if not aft.get("own_voice_notification_present"): f.append("RE-4 affected subscribers are not told in the team's own voice that their renewal date moved, by how much, and why - a silently shifted renewal date reads as a billing error when the next charge arrives late, and an unexplained extension cannot do the trust work it was bought for")
    if not aft.get("expiry_reflected_in_entitlement"): f.append("RE-4 the shifted expiry does not flow back into the entitlement state the app and support read - the subscriber was extended on Apple's side while the app still shows the old date")
    if not aft.get("extension_budget_and_errors_tracked"): f.append("RE-4 extensions per subscriber (against Apple's maximum-extension limit) and ineligible/max-extension errors are not tracked - the budget is spent invisibly until SubscriptionMaxExtension arrives during the incident that needed it most")
    ver=d.get("verification") or {}
    if not ver.get("sandbox_extension_tested"): f.append("RE-5 no end-to-end Sandbox test of an extension exists (individual call -> new expiry observed; mass call -> status polled to final counts) - the first real run of this path is during a real outage, on real subscribers")
    if not ver.get("error_handling_unit_tested"): f.append("RE-5 the handling of ineligible and max-extension errors is not unit-tested - those errors are the normal texture of a mass run, not edge cases")
    return f
if __name__=="__main__":
    data=json.load(open(sys.argv[1])); fails=check(data)
    if fails:
        print(f"FAIL ({len(fails)}):")
        [print(" -",x) for x in fails]; sys.exit(1)
    print("PASS")
