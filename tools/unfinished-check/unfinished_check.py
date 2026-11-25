#!/usr/bin/env python3
"""unfinished-check: deterministic gate for the UNFINISHED TRANSACTION
FINISHING surface (StoreKit transactions that were paid for but never
finished, so StoreKit keeps them in the queue and redelivers them on
every launch until the app finishes them).
Stdlib only, offline, free.
Sources (read 2026-11-16):
- Apple StoreKit 2 form (Codez Up integration guide synthesising Apple
  docs, full read): you must call transaction.finish() yourself once
  you have delivered the content; StoreKit keeps an unfinished
  transaction in the queue and keeps redelivering it (including via
  Transaction.updates) until you finish it. An unfinished transaction
  keeps reappearing on every launch when the app crashes or throws
  between a successful purchase and finish(). Handle defensively: on
  launch, iterate Transaction.unfinished, re-verify, and finish
  anything you can confirm was already delivered. Transaction.updates
  must be listened to from launch and kept alive for the app lifetime.
  Only finish after delivery; do not grant on .unverified.
  https://codezup.com/in-app-purchases-ios-integration-guide/
- RevenueCat official "Using the SDK with your own IAP Code"
  (full read): completing a purchase tells the device billing library
  the purchase has been processed and can be discarded. RevenueCat
  does this BY DEFAULT. Setting purchasesAreCompletedBy to .myApp
  (formerly observer mode) transfers finishing to the app, and then
  storeKitVersion must also be set. A silent reliance on the default
  is a reliance on a config value nobody recorded.
  https://www.revenuecat.com/docs/migrating-to-revenuecat/sdk-or-not/finishing-transactions
Exit 0 = PASS, 1 = FAIL.
Input JSON: {app,
 inventory:{finishing_owner_recorded, crash_and_redelivery_facts_recorded,
   product_types_enumerated},
 configuration:{finishing_owner_explicit_or_verified_default,
   no_conflicting_direct_purchase_path, storekit_version_pinned_if_my_app},
 delivery:{finish_only_after_delivery_and_verification,
   unverified_not_granted_or_finished_as_delivered,
   delivery_idempotent_on_redelivery},
 recovery:{launch_drain_or_sdk_equivalent_verified,
   foreground_redrain},
 repurchase:{unfinished_does_not_block_forever,
   redelivery_not_double_counted},
 measurement:{unfinished_count_and_age_tracked,
   finishing_failures_tracked}}
"""
import json, sys

def check(d):
    fails = []
    inv = d.get("inventory") or {}
    if not inv.get("finishing_owner_recorded"):
        fails.append("UF-0 the finishing owner is not recorded (who finishes every transaction -- RevenueCat by default, or the app via purchasesAreCompletedBy=.myApp -- is nowhere written; a transaction nobody owns finishing for is a transaction that stays in the queue)")
    if not inv.get("crash_and_redelivery_facts_recorded"):
        fails.append("UF-0 the platform facts are not recorded: an unfinished transaction stays in the StoreKit queue and is redelivered on every launch (via Transaction.updates / Transaction.unfinished) until finished, and the crash window between payment and finish() is exactly how unfinished transactions are born")
    if not inv.get("product_types_enumerated"):
        fails.append("UF-0 the product types are not enumerated for finishing consequences (for a consumable an unfinished transaction blocks re-purchase of the same product; for a subscription / non-consumable it redelivers and can re-fire delivery -- the drain design differs by type and an unenumerated surface cannot be drained honestly)")
    cfg = d.get("configuration") or {}
    if not cfg.get("finishing_owner_explicit_or_verified_default"):
        fails.append("UF-1 the finishing owner is neither explicit in configuration nor a verified default (Purchases.configure sets no purchasesAreCompletedBy and no record verifies the SDK default applies on the pinned SDK version -- the whole finishing path rests on an unrecorded assumption about a default)")
    if not cfg.get("no_conflicting_direct_purchase_path"):
        fails.append("UF-1 a direct StoreKit purchase path exists that bypasses the recorded finishing owner (two finishing owners, or a path with none, guarantee either double-finishing or never-finishing for the bypassed transactions)")
    if not cfg.get("storekit_version_pinned_if_my_app"):
        fails.append("UF-1 the StoreKit version condition is not settled (RevenueCat requires storeKitVersion to be set when the app completes purchases itself; with no explicit owner there is also no record of which StoreKit version's finishing semantics apply)")
    dl = d.get("delivery") or {}
    if not dl.get("finish_only_after_delivery_and_verification"):
        fails.append("UF-2 finishing is not ordered after delivery and verification (finish() tells the App Store delivery is complete: finishing early is the one way a paid purchase can be lost, and finishing on an .informational verification mode means the verification result never gates the finish)")
    if not dl.get("unverified_not_granted_or_finished_as_delivered"):
        fails.append("UF-2 an unverified transaction can be granted or finished as delivered (a VerificationResult .unverified transaction is not genuinely from the App Store; granting on it, or finishing it as if delivered, defeats the verification step StoreKit 2 exists to provide)")
    if not dl.get("delivery_idempotent_on_redelivery"):
        fails.append("UF-2 delivery is not idempotent on redelivery (StoreKit's retry mechanism IS redelivery: the same transaction will arrive again via updates / unfinished until finished, so a non-idempotent delivery double-grants, double-counts, or double-charges the user-visible effect)")
    rc = d.get("recovery") or {}
    if not rc.get("launch_drain_or_sdk_equivalent_verified"):
        fails.append("UF-3 there is no verified launch drain of unfinished transactions (no Transaction.unfinished iteration in the app, and no verified record that the SDK equivalent drains the queue on configure -- a purchase interrupted by a crash has no proven recovery path and simply redelivers, or blocks, forever)")
    if not rc.get("foreground_redrain"):
        fails.append("UF-3 there is no foreground re-drain (transactions can complete while the app is backgrounded or on another device; without a foreground recheck the queue is only ever examined, if at all, in the session that created it)")
    rp = d.get("repurchase") or {}
    if not rp.get("unfinished_does_not_block_forever"):
        fails.append("UF-4 an unfinished transaction can block the user forever (with no drain there is no proof a stuck transaction ever clears: for consumables it blocks re-purchase outright, and for subscriptions it leaves a permanently redelivering transaction whose state nobody resolves)")
    if not rp.get("redelivery_not_double_counted"):
        fails.append("UF-4 a redelivered transaction is double-counted as a new purchase / revenue event (redelivery is the same purchase arriving again, not a second purchase; counting it twice inflates conversion and revenue exactly where the funnel is already weakest)")
    ms = d.get("measurement") or {}
    if not ms.get("unfinished_count_and_age_tracked"):
        fails.append("UF-5 the unfinished count and age are not tracked (nobody can say how many transactions are stuck in the queue or for how long; a growing unfinished backlog -- the signature of a finishing bug -- is invisible until users complain)")
    if not ms.get("finishing_failures_tracked"):
        fails.append("UF-5 finishing failures are not tracked (a finish() that throws, or an SDK finishing failure, leaves the transaction in the queue silently; without a failure count the drain cannot be judged or alarmed)")
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
