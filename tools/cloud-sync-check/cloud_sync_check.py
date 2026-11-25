#!/usr/bin/env python3
"""cloud-sync-check: deterministic gate for the CLOUD SYNC / CONTINUITY surface.
Stdlib only, offline, free.
Source (read 2026-11-16 via live browser): Apple Developer, "CKAccountStatus"
https://developer.apple.com/documentation/cloudkit/ckaccountstatus
- CKAccountStatus has 5 cases: available / couldNotDetermine / noAccount /
  restricted (parental controls or MDM) / temporarilyUnavailable.
- temporarilyUnavailable: the account exists but is not ready for CloudKit
  operations. Do NOT delete cached data, do NOT enqueue operations; listen
  for CKAccountChanged until the status becomes available.
The gate generalises the contract: whichever sync engine is chosen (CloudKit
or the app's own server), continuity is a decided, two-way, account-aware,
conflict-ruled, deletion-propagating, rehearsed property -- not an accident
of whichever store happened to get an upload call.
Exit 0=PASS, 1=FAIL.
"""
import json, sys
def check(d):
    f=[]
    dec=d.get("decision") or {}
    if not dec.get("continuity_decision_recorded"): f.append("CS-0 no recorded continuity decision (which stores sync, to what engine, and which stay local is decided nowhere -- continuity is whatever the code happens to do)")
    if not dec.get("sync_owner_recorded"): f.append("CS-0 no single sync/continuity owner is recorded")
    if not dec.get("reinstall_expectation_recorded"): f.append("CS-0 the reinstall / new-device expectation is not recorded (what a returning user gets back is unspecified, so its absence cannot be a bug)")
    cov=d.get("coverage") or {}
    if not cov.get("every_store_classified"): f.append("CS-1 user-content stores are not classified sync-vs-local with reasons (an unclassified store is local by accident)")
    if not cov.get("upload_path_exists"): f.append("CS-1 synced stores have no upload path")
    if not cov.get("download_restore_path_exists"): f.append("CS-1 there is no download/restore path (upload-only sync can never give a new device its data back -- the write exists, the return does not)")
    if not cov.get("identity_survives_device_change"): f.append("CS-1 sync identity does not survive a device change (keyed to a device id, the synced copy is orphaned exactly when continuity matters)")
    acc=d.get("account_status") or {}
    if not acc.get("account_status_checked"): f.append("CS-2 the sync account's status is never checked (noAccount / restricted / signed-out are indistinguishable from success)")
    if not acc.get("unavailable_preserves_cache_no_enqueue"): f.append("CS-2 temporary unavailability is not handled as preserve-and-wait (Apple: on temporarilyUnavailable, do not delete cached data and do not enqueue operations)")
    if not acc.get("account_change_observed"): f.append("CS-2 account changes are not observed (no CKAccountChanged equivalent -- a status that recovers is never noticed, a status that is lost is never reacted to)")
    con=d.get("conflict") or {}
    if not con.get("conflict_rule_recorded"): f.append("CS-3 no conflict rule is recorded (two devices editing the same record resolve by timing accident, not by a rule)")
    if not con.get("pending_survives_restart"): f.append("CS-3 pending sync work does not survive an app restart (an in-memory buffer loses every unsynced change on kill / crash / reboot)")
    if not con.get("retry_trigger_wired"): f.append("CS-3 the retry entry point is not wired to any caller (a retry function nobody calls is not a retry)")
    dele=d.get("deletion") or {}
    if not dele.get("deletion_propagates_to_synced_copy"): f.append("CS-4 account/data deletion does not propagate to the synced copy (deleted-on-device data lives on the server and can return)")
    if not dele.get("signout_data_behavior_decided"): f.append("CS-4 sign-out behaviour for synced data is not decided or recorded")
    if not dele.get("account_switch_isolation"): f.append("CS-4 account switching is not isolated (one user's synced data can surface under another identity on the same device)")
    ver=d.get("verification") or {}
    if not ver.get("sync_outcomes_measured"): f.append("CS-5 sync success/failure is not measured per store (log lines are not a number; silent sync loss has no rate)")
    if not ver.get("restore_rehearsal_recorded"): f.append("CS-5 no restore rehearsal is recorded (second device or reinstall, with record counts preserved -- the only test that proves continuity)")
    if not ver.get("sync_state_logged"): f.append("CS-5 sync state is not logged in a structured, greppable way")
    return f
if __name__=="__main__":
    data=json.load(open(sys.argv[1])); fails=check(data)
    if fails:
        print(f"FAIL ({len(fails)}):")
        [print(" -",x) for x in fails]; sys.exit(1)
    print("PASS")
