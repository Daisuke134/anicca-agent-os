#!/usr/bin/env python3
"""offline-resilience-check: deterministic gate for the OFFLINE / NETWORK RESILIENCE surface.
Stdlib only, offline, free.
Sources (read 2026-11-16):
- Apple WWDC17 Advances in Networking, Part 2 (Adaptable Connectivity): do not preflight-check
  connectivity (Reachability/NWPathMonitor is a bad predictor of where a flow ends up); instead
  opt in with URLSessionConfiguration.waitsForConnectivity so a task that would fail for lack of
  connectivity waits and fires when a connection arrives; implement
  urlSession(_:taskIsWaitingForConnectivity:) to present an offline/waiting mode WITHOUT
  blocking the user. https://www.vadimbulavin.com/network-connectivity-on-ios-with-swift/?ref=MobileDevelopersCafe
  (quotes Apple Networking Overview + WWDC sessions verbatim)
- NWPathMonitor (Network framework) is the modern path-status source; its correct use is to
  inform UI and trigger deferred work on recovery, not to gate requests.
Exit 0=PASS, 1=FAIL.
"""
import json, sys
def check(d):
    f=[]
    dec=d.get("decision") or {}
    if not dec.get("network_surfaces_inventoried"): f.append("OF-0 network-dependent surfaces are not inventoried in one record (a fetch nobody listed is a fetch nobody made resilient)")
    if not dec.get("offline_owner_recorded"): f.append("OF-0 no single offline/resilience owner is recorded")
    if not dec.get("core_value_offline_decision_recorded"): f.append("OF-0 what must keep working with no network (the core value) is not decided and recorded, so offline behaviour is whatever the code happens to do")
    con=d.get("connectivity") or {}
    if not con.get("no_preflight_gating"): f.append("OF-1 requests are gated on a preflight connectivity check (Apple: preflight is a bad predictor; always attempt the request)")
    if not con.get("waits_for_connectivity_or_recorded_alternative"): f.append("OF-1 deferred/core fetches neither opt into waitsForConnectivity nor record an alternative (a fetch in airplane mode fails instantly and is never re-attempted by the system)")
    if not con.get("path_status_informs_ui_or_retry"): f.append("OF-1 no path-status signal (NWPathMonitor or waiting delegate) informs the UI or triggers deferred work on recovery")
    if not con.get("waiting_state_indicated_without_blocking"): f.append("OF-1 the waiting/offline state is not indicated to the user without blocking (silence reads as a broken app, not as offline)")
    ret=d.get("retry") or {}
    if not ret.get("core_fetch_retries_with_backoff"): f.append("OF-2 the core content fetch is a single attempt with no retry/backoff (one transient failure spends the whole day)")
    if not ret.get("retry_on_reconnect_or_foreground"): f.append("OF-2 a failed core fetch is not re-attempted on reconnect or foreground return (recovery depends on a cold restart or an unrelated event)")
    if not ret.get("failure_types_distinguished_in_measurement"): f.append("OF-2 failure types (offline / HTTP / decode) are not distinguished in measurement (the catch-all log line cannot size the offline problem)")
    cac=d.get("cache") or {}
    if not cac.get("personalized_cache_persisted_across_launches"): f.append("OF-3 the personalized content cache is memory-only (it dies with the process, so offline-after-restart has nothing personalised to show)")
    if not cac.get("todays_core_content_persisted"): f.append("OF-3 today's already-selected core content is not persisted for same-day offline reopen")
    if not cac.get("bundled_fallback_for_core_value"): f.append("OF-3 no bundled/static fallback exists for the core value (first launch offline is an empty app)")
    if not cac.get("stale_never_presented_as_fresh"): f.append("OF-3 stale content can be presented as fresh (no fetched-at/staleness marking, so yesterday's personalised words can silently pose as today's)")
    if not cac.get("cache_scoped_with_rollover"): f.append("OF-3 the cache is not scoped to its day/period with a rollover rule (matching by time-of-day alone leaks one day's content into the next)")
    syn=d.get("sync") or {}
    if not syn.get("writes_queued_and_restored_on_failure"): f.append("OF-4 user writes are not queued and restored on sync failure (a failed PUT drops the user's answers)")
    if not syn.get("pending_survives_restart"): f.append("OF-4 the pending-sync queue does not survive a restart (the queue is memory-only, so a killed app loses the queued write)")
    if not syn.get("pending_state_indicated_or_reconciled"): f.append("OF-4 pending/un-synced state is neither indicated nor reconciled on next launch (the user cannot tell their data has not reached the server)")
    ver=d.get("verification") or {}
    if not ver.get("offline_failure_rate_measured"): f.append("OF-5 the offline/fetch failure rate is not measured as a rate (no denominator, so 'offline is rare' is an opinion, not a number)")
    if not ver.get("airplane_or_link_conditioner_test_recorded"): f.append("OF-5 no airplane-mode / Network Link Conditioner test is recorded for the offline path (the one state every travelling user hits is the one state never tested)")
    return f
if __name__=="__main__":
    data=json.load(open(sys.argv[1])); fails=check(data)
    if fails:
        print(f"FAIL ({len(fails)}):")
        [print(" -",x) for x in fails]; sys.exit(1)
    print("PASS")
