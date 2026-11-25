#!/usr/bin/env python3
"""pending-check: deterministic gate for the PENDING / DEFERRED PURCHASE
surface (Ask to Buy, SCA, cash payment methods -- a purchase that started
but is waiting on external action before it can complete).
Stdlib only, offline, free.
Sources (read 2026-11-16):
- RevenueCat error handling (community + handbook synthesis of the SDK
  contract): a pending purchase surfaces as ErrorCode.paymentPendingError;
  it is NOT a failure and NOT a cancellation. Do not show an error; show
  "Payment pending -- we'll unlock access when it's confirmed." RevenueCat
  does not grant entitlements for pending purchases. When the payment
  completes, the entitlement arrives through the CustomerInfo listener /
  delegate (and server-side via the INITIAL_PURCHASE webhook).
- RevenueCat staff (community.revenuecat.com, deferred-purchase thread):
  on iOS there is no way to query pending state at any moment outside the
  purchase call, and a pending purchase cannot be cancelled in code; it
  can resolve days later. Denial may not be delivered as a callback, so
  the pending UI must be re-read on foreground / next session.
- Apple StoreKit: the same condition is SKPaymentTransactionState.deferred
  (StoreKit 1) / Product.PurchaseResult.pending (StoreKit 2); the eventual
  transaction is delivered through the transaction updates stream, which
  the app must already be observing.
Exit 0 = PASS, 1 = FAIL.
Input JSON: {app,
 inventory:{causes_enumerated, pending_is_distinct_outcome,
   cannot_cancel_and_late_resolution_recorded},
 classification:{pending_distinguished_before_generic_failure,
   pending_not_tracked_as_failed, pending_not_treated_as_cancelled},
 message:{pending_shows_info_not_raw_error, pending_message_localized,
   pending_message_says_unlocks_when_confirmed},
 grant:{no_entitlement_granted_on_pending,
   no_retry_or_repurchasing_encouragement},
 resolution:{customerinfo_listener_observes_completion,
   pending_state_persists_or_rederived, foreground_recheck_clears_or_resolves},
 measurement:{pending_tracked_as_distinct_result,
   pending_resolution_counted}}
"""
import json, sys

def check(d):
    fails = []
    inv = d.get("inventory") or {}
    if not inv.get("causes_enumerated"):
        fails.append("PP-0 the pending causes are not enumerated (Ask to Buy / parental approval, SCA in Europe, cash payment methods such as convenience-store payment in Japan -- each cause has a different expected wait and a different person who must act; an unenumerated 'pending' cannot be messaged honestly)")
    if not inv.get("pending_is_distinct_outcome"):
        fails.append("PP-0 pending is not recorded as a distinct purchase outcome alongside success / cancelled / failed (a purchase flow with three recorded outcomes will force the fourth, real one into whichever bucket its code path falls through to -- in practice, 'failed')")
    if not inv.get("cannot_cancel_and_late_resolution_recorded"):
        fails.append("PP-0 the platform facts are not recorded: a pending purchase cannot be cancelled in code and can resolve days later (RevenueCat staff record; a design that assumes pending resolves in-session, or offers a cancel that does nothing, is built on a false model)")
    cl = d.get("classification") or {}
    if not cl.get("pending_distinguished_before_generic_failure"):
        fails.append("PP-1 the purchase code does not distinguish paymentPendingError before the generic failure branch (referenced zero times, every pending purchase falls into 'failed' with a raw error message -- the one outcome RevenueCat explicitly says is not a failure is the one the funnel records as failure)")
    if not cl.get("pending_not_tracked_as_failed"):
        fails.append("PP-1 pending is tracked as purchase_result=failed (pending buyers are counted as lost buyers; the funnel overstates failure, understates eventual conversion, and any failure-rate alert fires on people who may still pay)")
    if not cl.get("pending_not_treated_as_cancelled"):
        fails.append("PP-1 pending is treated as a cancellation (a pending buyer did not cancel -- they are waiting on a parent, a bank, or a cash payment; firing the cancellation path, e.g. a retention offer for a cheaper product, invites a second purchase attempt while the first is still alive)")
    me = d.get("message") or {}
    if not me.get("pending_shows_info_not_raw_error"):
        fails.append("PP-2 pending does not show an informational pending message instead of the raw error (error.localizedDescription for a pending code tells the user the purchase broke; RevenueCat's form is an info message: payment pending, access unlocks when confirmed)")
    if not me.get("pending_message_localized"):
        fails.append("PP-2 the pending message is not a localized string (no pending string exists in any locale; a hard-coded or raw-error message breaks the no-language-mixing rule on every non-English surface)")
    if not me.get("pending_message_says_unlocks_when_confirmed"):
        fails.append("PP-2 the pending message does not say what happens next (who must act / that access unlocks automatically on confirmation; without the next step the user cannot tell waiting from broken, and the rational response is to retry or delete)")
    gr = d.get("grant") or {}
    if not gr.get("no_entitlement_granted_on_pending"):
        fails.append("PP-3 premium access is granted on a pending purchase (RevenueCat does not grant entitlements for pending purchases; granting speculatively gives away the product on payments that may never complete -- assume not charged until confirmed)")
    if not gr.get("no_retry_or_repurchasing_encouragement"):
        fails.append("PP-3 the pending path leaves the user able / encouraged to purchase again while the first purchase is still pending (RevenueCat community record: a pending purchase can complete 30+ days later; a second attempt risks a double charge and a furious customer -- the pending state must block or clearly supersede re-purchase of the same product)")
    re_ = d.get("resolution") or {}
    if not re_.get("customerinfo_listener_observes_completion"):
        fails.append("PP-4 no CustomerInfo listener observes the pending purchase's completion (the purchase call already threw; the only in-app delivery of the eventual grant is the delegate / CustomerInfo stream -- without it, a buyer who pays an hour later stays locked out until some unrelated refresh)")
    if not re_.get("pending_state_persists_or_rederived"):
        fails.append("PP-4 the pending state does not survive relaunch and is not re-derived (approval can take minutes to days and will usually resolve in a later session; a pending flag held only in view state vanishes on relaunch, so the returning user sees a plain paywall with a live purchase still in flight)")
    if not re_.get("foreground_recheck_clears_or_resolves"):
        fails.append("PP-4 there is no foreground / next-session recheck that resolves or clears the pending state (denial of an Ask to Buy request may never arrive as a callback -- delasign/StoreKit record: the app must re-read purchase state when it enters the foreground, or a denied purchase leaves a permanent 'pending' ghost)")
    ms = d.get("measurement") or {}
    if not ms.get("pending_tracked_as_distinct_result"):
        fails.append("PP-5 pending is not tracked as its own purchase_result value (pending volume is invisible: nobody can say how many purchases are in flight, which cause dominates, or whether the pending message changes anything)")
    if not ms.get("pending_resolution_counted"):
        fails.append("PP-5 the pending-to-resolved conversion is not counted (pending is a delayed funnel stage, not an exit; without pending -> success / pending -> never-resolved counts, the true paywall conversion is understated by exactly the pending share and no fix can be judged)")
    return fails

def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "-"
    raw = sys.stdin.read() if path == "-" else open(path).read()
    d = json.loads(raw)
    fails = check(d)
    if fails:
        print(f"FAIL {len(fails)}")
        for f in fails:
            print(" -", f)
        return 1
    print("PASS")
    return 0

if __name__ == "__main__":
    sys.exit(main())
