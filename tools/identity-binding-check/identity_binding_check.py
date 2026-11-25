#!/usr/bin/env python3
"""identity-binding-check: deterministic gate for CUSTOMER IDENTITY BINDING
(RevenueCat App User ID + StoreKit appAccountToken). Stdlib only, offline, free.
Sources (read 2026-11-17):
- RevenueCat "Identifying Customers" https://www.revenuecat.com/docs/customers/identifying-customers
  (full read via browser.open): default configure without an App User ID generates a random
  $RCAnonymousID: cached on device, cleared on reinstall, cannot share status across
  apps/platforms. Custom IDs allow dashboard/API/webhook reference, restore after reinstall,
  and cross-device honouring. IDs are case-sensitive, scoped to a Project. logIn() may alias
  anonymous->custom, BUT if the provided ID already exists AND already has an anonymous alias,
  NO merge/purchase transfer occurs; non-anonymous->custom also never merges. logOut()
  generates a NEW anonymous ID. RevenueCat strongly recommends revealing the App User ID
  in settings for support. Tips: unique per user, non-guessable (UUID v4 recommended),
  <=100 chars, never email/IDFA/hardcoded; blocklist includes 'no_user','null','anonymous',
  'guest','' and any ID containing '/'.
- Apple "Product.PurchaseOption.appAccountToken(_:)" (read via live browser 2026-11-17):
  https://developer.apple.com/documentation/storekit/product/purchaseoption/appaccounttoken(_:)
  static func appAccountToken(_ token: UUID); App Store returns the same value in the
  resulting transaction's appAccountToken, matching the purchase to the app's own account. iOS 15+.
Exit 0=PASS, 1=FAIL.
"""
import json, sys
def check(d):
    f=[]
    dec=d.get("decision") or {}
    if not dec.get("decision_recorded"): f.append("ID-0 the identity model (anonymous-first vs custom-ID-only, and which system owns the ID) is not recorded as a decision - the SDK default (random anonymous ID, cleared on reinstall, no cross-platform sharing) silently becomes the product's identity model")
    if not dec.get("owner_recorded"): f.append("ID-0 no single identity-binding owner is recorded")
    if not dec.get("restore_behavior_recorded"): f.append("ID-0 the project's restore/transfer behaviour for alias merges is not recorded - whether a purchase moves to an identified user on logIn/restore is a project setting, and an unrecorded one cannot be tested against")
    fou=d.get("foundation") or {}
    if not fou.get("id_unique_non_guessable"): f.append("ID-1 the App User ID is not verified unique per user and non-guessable (UUID/opaque; never email, IDFA, or a hardcoded/shared string - a shared ID unlocks entitlements for users who never purchased)")
    if not fou.get("id_format_guarded"): f.append("ID-1 ID format is not guarded before logIn/configure (<=100 chars, not on RevenueCat's blocklist such as 'anonymous'/'guest'/'null'/'', no '/') - a blocked or malformed ID fails identity binding at the moment it matters most")
    if not fou.get("configure_strategy_deliberate"): f.append("ID-1 configure() strategy is not deliberate (configure with the custom ID when it is already known at launch, e.g. a persisted signed-in user, instead of always starting anonymous and relying on a later logIn that may never fire)")
    log=d.get("login") or {}
    if not log.get("login_wired_to_auth"): f.append("ID-2 logIn() is not wired to every auth sign-in path (sign-in, credential restore at launch, account switch) - a signed-in user the SDK still treats as anonymous cannot restore or share a subscription")
    if not log.get("login_result_checked"): f.append("ID-2 the logIn() result/error is not checked (a discarded try? result means a failed identity bind is invisible, and the returned CustomerInfo is never applied) - identity failure must surface in logs/metrics, not silence")
    if not log.get("alias_no_merge_handled"): f.append("ID-2 the no-merge alias case is not handled (provided ID already exists AND already has an anonymous alias, or current ID is non-anonymous: RevenueCat performs NO merge/purchase transfer) - code that assumes logIn always transfers the purchase will strand a paying user")
    out=d.get("logout_switch") or {}
    if not out.get("logout_wired_to_auth"): f.append("ID-3 logOut() is not wired to every sign-out / account-deletion path - the previous user's entitlements and identity leak into the next session on a shared device")
    if not out.get("logout_new_anonymous_handled"): f.append("ID-3 the consequence of logOut() (a brand-new anonymous ID is generated) is not handled - personalisation, server sync and support lookups that keep using the old ID after logout write to a dead identity")
    if not out.get("switch_handled"): f.append("ID-3 account switching is not handled as a direct logIn(new ID) (or an explicitly tested logOut+logIn) - an untested switch path is where cross-account entitlement leakage happens")
    use=d.get("use") or {}
    if not use.get("server_key_consistent"): f.append("ID-4 the server does not use the same App User ID as its subscription key (webhooks carry app_user_id / original_app_user_id / aliases; a server keyed by a different ID cannot reconcile the SDK state with its own SSOT)")
    if not use.get("support_id_visible"): f.append("ID-4 the App User ID is not revealed copyably in the app (RevenueCat strongly recommends a settings location) - support cannot look up a customer who cannot tell you who the SDK thinks they are")
    if not use.get("attributes_decided"): f.append("ID-4 subscriber attributes / appAccountToken binding are not decided and recorded (either attributes are synced, or a recorded decision says none are needed; for direct StoreKit purchases the purchase must carry appAccountToken as a UUID matching the account) - an undecided attribute layer is an unmeasured one")
    ver=d.get("verification") or {}
    if not ver.get("reinstall_restore_tested"): f.append("ID-5 no end-to-end test proves reinstall restore by identity (delete, reinstall, sign in with the same ID, entitlement returns without a manual restore) - the headline promise of custom IDs is untested")
    if not ver.get("multi_device_tested"): f.append("ID-5 no test proves the same ID honours the subscription on a second device/platform - cross-device sharing is claimed by the model but never exercised")
    if not ver.get("alias_cases_unit_tested"): f.append("ID-5 the alias table is not unit-tested (anonymous->new ID merges; anonymous->existing ID with an existing alias does NOT merge; non-anonymous->any does NOT merge) - the three outcomes need three different product behaviours")
    return f
if __name__=="__main__":
    data=json.load(open(sys.argv[1])); fails=check(data)
    if fails:
        print(f"FAIL ({len(fails)}):")
        [print(" -",x) for x in fails]; sys.exit(1)
    print("PASS")
