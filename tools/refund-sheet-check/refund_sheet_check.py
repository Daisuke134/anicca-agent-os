#!/usr/bin/env python3
"""refund-sheet-check: deterministic gate for the IN-APP REFUND REQUEST
SHEET surface (StoreKit beginRefundRequest). Stdlib only, offline, free.
Sources:
- Apple Tech Talk 10887 "Support customers with StoreKit 2 and App Store
  Server API" (developer.apple.com/videos/play/tech-talks/10887, read in
  full): in iOS 15 the App Store introduced beginRefundRequest in StoreKit 2
  so customers can request a refund for an in-app purchase from within the
  app, instead of being redirected to Report a Problem / Apple Support.
  The app surfaces transactions for the customer to choose from (a stored
  history of transactions and original transaction IDs is the prerequisite),
  may show contextual information about past purchases and custom in-app
  messaging / troubleshooting help, then calls the API, which displays
  Apple's refund request sheet where the customer picks a reason code
  (consistent with Report a Problem). Apple renders the decision. Approved:
  the app is notified and the server receives REFUND. Denied: the server
  receives REFUND_DECLINED. Most refund requests occur within 30 days of
  purchase. For auto-renewable subscriptions a successful refund cancels
  the subscription, so retention help belongs alongside -- never in front
  of -- the request. Sandbox can simulate a refund from pending to
  approved or declined.
- RevenueCat "Handling Refunds" (production-docs.revenuecat.com, read):
  Apple does not allow developers to issue refunds on behalf of customers;
  RevenueCat automatically detects an issued Apple refund when Platform
  Server Notifications are configured. Copy must therefore never promise
  that the developer will refund -- Apple decides.
Exit 0=PASS, 1=FAIL.
"""
import json, sys
def check(d):
    f=[]
    dec=d.get("decision") or {}
    if not dec.get("decision_recorded"): f.append("RS-0 whether the in-app refund request sheet is offered, and on which surface (settings / support / subscription management), is not recorded as a decision - the absence of the surface is currently an accident, not a decision")
    if not dec.get("owner_recorded"): f.append("RS-0 no single refund-sheet owner is recorded")
    if not dec.get("fallback_recorded"): f.append("RS-0 the fallback for users who cannot use the sheet (below iOS 15, no eligible transaction, sheet error) is not recorded - those users need a working path to Report a Problem / support, not a dead end")
    txn=d.get("transactions") or {}
    if not txn.get("transactions_surfaced_for_choice"): f.append("RS-1 the customer is not shown their transactions to choose which one to request a refund for - beginRefundRequest acts on one chosen transaction, so without a chooser the sheet cannot be reached for the right purchase")
    if not txn.get("original_ids_stored"): f.append("RS-1 original transaction IDs are not stored per purchase (Apple's stated prerequisite for surfacing transactions and for refund lookup) - without them the app cannot reliably identify the transaction a customer means")
    if not txn.get("contextual_info_shown"): f.append("RS-1 no contextual information about the past purchase (product, date, price, renewal state) is shown before the sheet - Apple gives the app flexibility to display it, and a bare button makes mistaken-transaction requests likely")
    sht=d.get("sheet") or {}
    if not sht.get("sheet_called_with_txn_and_scene"): f.append("RS-2 beginRefundRequest is not called with the chosen transaction and an active window scene - the system sheet is the refund channel; a web redirect or a support email is the pre-iOS 15 path Apple replaced")
    if not sht.get("statuses_handled_distinctly"): f.append("RS-2 the sheet's outcomes are not handled distinctly (submitted vs user-cancelled vs error) - treating a cancellation or an error as a submitted request tells the customer a refund is coming that was never requested")
    if not sht.get("result_copy_states_apple_decides"): f.append("RS-2 the result copy does not state that Apple reviews and decides the refund (and its timing) - a developer cannot issue or promise an App Store refund (RevenueCat/Apple), so any other wording is a promise the app cannot keep")
    sep=d.get("separation") or {}
    if not sep.get("troubleshoot_help_offered"): f.append("RS-3 no troubleshooting / help offer accompanies the refund entry - Apple positions the API as a way to help a frustrated customer resolve the underlying issue inside the app, not only to process the exit")
    if not sep.get("refund_access_not_blocked"): f.append("RS-3 access to the refund request is blocked or gated behind retention steps the customer must dismiss first - retention may be offered alongside, never as a toll booth in front of a refund (dark-pattern risk, cf. the Prayer Lock ban)")
    if not sep.get("cancel_distinguished_from_refund"): f.append("RS-3 cancelling a subscription and requesting a refund are not distinguished in copy and flow - a successful subscription refund cancels the subscription, while cancelling alone refunds nothing; conflating them misleads in both directions")
    aft=d.get("aftermath") or {}
    if not aft.get("refund_notification_revokes"): f.append("RS-4 an approved refund does not flow back into entitlement state (REFUND server notification / RevenueCat detection revoking access) - a refunded customer who keeps premium has converted a refund into a free subscription")
    if not aft.get("declined_recorded"): f.append("RS-4 a declined refund (REFUND_DECLINED) is not recorded - a customer Apple declined who is then told nothing, or told the opposite, is a support incident created by silence")
    if not aft.get("outcome_recorded_per_transaction"): f.append("RS-4 refund outcomes are not recorded per transaction / product - spikes by product or paywall version stay invisible until they show up as a rate problem (see the refund-rate gate)")
    ver=d.get("verification") or {}
    if not ver.get("funnel_measured"): f.append("RS-5 the refund-entry -> sheet -> outcome funnel is not measured - the surface can be broken (wrong transaction, sheet never appears) with no signal")
    if not ver.get("sandbox_simulation_tested"): f.append("RS-5 the Sandbox refund simulation (pending -> approved and pending -> declined) is not end-to-end tested - Sandbox exists precisely to exercise this sheet, and an untested refund path fails first on a real frustrated customer")
    if not ver.get("status_unit_tests"): f.append("RS-5 sheet status handling (submitted / cancelled / error fallback) is not unit-tested")
    return f
if __name__=="__main__":
    data=json.load(open(sys.argv[1])); fails=check(data)
    if fails:
        print(f"FAIL ({len(fails)}):")
        [print(" -",x) for x in fails]; sys.exit(1)
    print("PASS")
