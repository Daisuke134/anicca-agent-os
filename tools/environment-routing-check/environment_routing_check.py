#!/usr/bin/env python3
"""environment-routing-check: deterministic gate for ENVIRONMENT ROUTING
(production / sandbox / Xcode separation of purchase data). Stdlib only, offline, free.
Sources (read 2026-11-17):
- Apple "Overview of testing in sandbox" (App Store Connect Help,
  https://developer.apple.com/help/app-store-connect/test-in-app-purchases/overview-of-testing-in-sandbox):
  development-signed and TestFlight apps ALWAYS transact in sandbox; StoreKit
  Testing in Xcode is a separate LOCAL environment driven by a .storekit
  configuration file and never reaches App Store servers. Three distinct
  environments exist, not two.
- Apple StoreKit: Transaction.environment / AppStore.environment carry the
  environment a transaction was created in (production / sandbox / Xcode).
  The legacy receipt-filename heuristic (sandboxReceipt) cannot see the Xcode
  environment and defaults everything unknown to production.
- RevenueCat "Sandbox Testing" (https://www.revenuecat.com/docs/test-and-launch/sandbox,
  full read via browser.open 2026-11-17): RevenueCat auto-detects production vs
  sandbox per purchase; non-production data is viewed via the Sandbox data
  toggle; there is NO sandbox/production *user* - the same App User ID can hold
  both, and the toggle does NOT affect New/Active Customers cards. Test Store
  uses a SEPARATE API key that must never ship in a release build (the SDK
  crashes release builds on purpose); Sandbox Testing Access can restrict
  which App User IDs receive entitlements from non-production purchases.
Exit 0=PASS, 1=FAIL.
"""
import json, sys
def check(d):
    f=[]
    dec=d.get("decision") or {}
    if not dec.get("decision_recorded"): f.append("ER-0 environment routing (how production / sandbox / Xcode purchase data is separated in analytics, server sync, revenue KPI and eval cases) is not recorded as a decided surface - separation exists by accident of defaults, not by choice")
    if not dec.get("owner_recorded"): f.append("ER-0 no single environment-routing owner is recorded (detection source, key selection and dashboard toggles are ongoing work, not a one-time flag)")
    if not dec.get("canonical_source_recorded"): f.append("ER-0 the canonical environment source is not recorded (StoreKit Transaction.environment / AppStore.environment) - every reader invents their own heuristic and the heuristics disagree")
    det=d.get("detection") or {}
    if not det.get("transaction_environment_read"): f.append("ER-1 the app never reads Transaction.environment / AppStore.environment - the one field Apple stamps on every transaction is unused, so no downstream system can route on truth")
    if not det.get("xcode_environment_distinguished"): f.append("ER-1 the Xcode (StoreKit Testing) environment is not distinguished from sandbox/production - local .storekit transactions are silently folded into a real environment and pollute its counts")
    if not det.get("simulator_distinguished"): f.append("ER-1 the simulator is not distinguished as its own environment label - simulator sessions are counted as sandbox or production")
    if not det.get("receipt_not_sole_source"): f.append("ER-1 the receipt-filename heuristic (sandboxReceipt, defaulting to production when absent) is the sole environment source - it cannot see Xcode, misclassifies a missing receipt as production, and Apple superseded it with Transaction.environment")
    sep=d.get("separation") or {}
    if not sep.get("analytics_env_tagged"): f.append("ER-2 analytics events carry no environment tag - sandbox/TestFlight usage is indistinguishable from real users in the product funnel")
    if not sep.get("revenue_kpi_excludes_nonproduction"): f.append("ER-2 revenue / install KPI does not verifiably exclude non-production data (RevenueCat's Sandbox toggle does not affect New/Active Customers cards, and the same App User ID can hold both kinds of receipts - an unexamined dashboard number mixes test purchases into the company's revenue truth)")
    if not sep.get("server_sync_separates"): f.append("ER-2 the server entitlement/usage sync does not carry or separate environment - a sandbox entitlement can be merged into the same usage record as a production one with no way to unwind it")
    if not sep.get("eval_cases_separate"): f.append("ER-2 eval / intervention records do not carry environment - sandbox and Xcode decision points can enter ManagerBench as if they were real-user cases")
    key=d.get("keys") or {}
    if not key.get("key_selected_by_build_config"): f.append("ER-3 the RevenueCat API key is not selected by build configuration (a single Info.plist value serves debug, TestFlight and release alike) - there is no structural place where a Test Store key is kept out of release or a platform key out of debug")
    if not key.get("test_store_key_absent_verified"): f.append("ER-3 it is not verified that no Test Store API key can reach a release build (RevenueCat crashes release builds on a Test Store key on purpose - discovering this from a TestFlight crash report is the failure mode, not a check)")
    if not key.get("sandbox_access_controlled"): f.append("ER-3 Sandbox Testing Access (which App User IDs may receive entitlements from non-production purchases) is not decided - any sandbox receipt presented for any account grants the entitlement lane")
    mea=d.get("measurement") or {}
    if not mea.get("env_counts_measured"): f.append("ER-4 transaction/session counts are not measured BY environment - pollution is discovered anecdotally, if ever, instead of as a number that moves")
    if not mea.get("dashboard_toggle_state_checked"): f.append("ER-4 the RevenueCat dashboard Sandbox-data toggle state behind every reported revenue number is not recorded with the number - two reports of 'the same' MRR can silently be different populations")
    ver=d.get("verification") or {}
    if not ver.get("xcode_config_wired"): f.append("ER-5 no StoreKit configuration file is wired to the scheme - the Xcode local environment (the E2E recording route that structurally avoids Apple sign-in dialogs) does not exist as a testable lane")
    if not ver.get("sandbox_e2e_tested"): f.append("ER-5 no sandbox end-to-end walk exists (development-signed or TestFlight build, sandbox account, purchase, environment recorded as sandbox in analytics AND server AND dashboard) - each layer's routing is only ever assumed from the others")
    if not ver.get("testflight_env_tested"): f.append("ER-5 the TestFlight environment is not explicitly tested (TestFlight is always sandbox, including for App Review) - the exact build reviewers run is the one whose data routing was never walked")
    return f
if __name__=="__main__":
    data=json.load(open(sys.argv[1])); fails=check(data)
    if fails:
        print(f"FAIL ({len(fails)}):")
        [print(" -",x) for x in fails]; sys.exit(1)
    print("PASS")
