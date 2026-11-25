#!/usr/bin/env python3
"""ad-attribution-check: deterministic gate for the AD ATTRIBUTION surface
(SKAdNetwork 4 / AdAttributionKit conversion-value schema).
Stdlib only, offline, free.
Sources (Apple's framework design, as documented by Apple and the MMP
documentation that mirrors Apple's SKAdNetwork 4 specification):
- SKAdNetwork 4 (iOS 16.1+): up to three postbacks in windows anchored to
  install -- window 1 days 0-2 (fine value 0-63 AND coarse low/medium/high),
  window 2 days 3-7 (coarse only), window 3 days 8-35 (coarse only). Fine
  values arrive only when the crowd-anonymity tier is high enough; coarse
  values are the reliable floor. A window can be locked early
  (lockWindow) to finalise the value and receive the postback sooner;
  once locked, the value cannot rise again in that window.
- The conversion value is a designed schema: events/revenue are mapped
  onto the 6-bit fine range and onto coarse buckets per window, in
  advance, as a recorded decision -- not improvised at call sites.
- AdAttributionKit (iOS 17.4+) is Apple's successor framework: the
  advertised app calls Postback.updateConversionValue, SKAdNetwork
  updates are mirrored into it, and an AttributionCopyEndpoint in the
  Info.plist AdAttributionKit dictionary sends the developer a copy of
  the winning postback. Adopting or deferring it is a decision to record.
- Apple Search Ads attribution (AdServices AAAttribution token, posted
  to api-adservices.apple.com within 24h) is the separate first-party
  channel and does not substitute for a SKAN conversion-value schema.
Exit 0=PASS, 1=FAIL.
"""
import json, sys
def check(d):
    f=[]
    dec=d.get("decision") or {}
    if not dec.get("schema_recorded"): f.append("AA-0 no conversion-value schema is recorded as a decision (which event maps to which fine/coarse value, per window) - the values in code are call-site improvisation, not a schema")
    if not dec.get("owner_recorded"): f.append("AA-0 no single ad-attribution owner is recorded")
    if not dec.get("aak_adoption_decision_recorded"): f.append("AA-0 no recorded decision on AdAttributionKit (adopt, or defer with a reason) - the successor framework is absent by drift, not by decision")
    inv=d.get("inventory") or {}
    if not inv.get("skadnetwork_items_present"): f.append("AA-1 SKAdNetworkItems is missing from Info.plist - no ad network can be credited for an install at all")
    if not inv.get("each_id_mapped_to_network"): f.append("AA-1 the SKAdNetwork identifiers in Info.plist are not inventoried against the networks they belong to (an unmapped list cannot be pruned, extended, or checked when a network changes its ID)")
    if not inv.get("copy_endpoint_decision_recorded"): f.append("AA-1 no recorded decision on receiving a copy of the winning postback (SKAN developer copy / AdAttributionKit AttributionCopyEndpoint) - whether postbacks are ever seen server-side is undecided")
    val=d.get("values") or {}
    if not val.get("fine_range_uses_schema"): f.append("AA-2 the fine value range is not used as a schema (only a few adjacent integers for the whole funnel) - window 1 can carry 64 distinct signals and the design uses almost none of them")
    if not val.get("coarse_independent_per_event"): f.append("AA-2 the coarse value is derived mechanically from the fine value, so distinct funnel steps collide in the same coarse bucket (coarse is the only signal low-volume campaigns ever return, so the collision is the measurement)")
    if not val.get("monotonic_guard"): f.append("AA-2 there is no monotonic guard on conversion-value updates (any later call site can lower the value within a window, and nothing stores the highest value reached)")
    if not val.get("trial_distinguished_from_paid"): f.append("AA-2 a trial start and a paid purchase carry the same conversion value - the single most important revenue distinction is invisible to attribution")
    win=d.get("windows") or {}
    if not win.get("first_update_timing_recorded"): f.append("AA-3 the timing of the first conversion-value update is not recorded (the measurement windows are anchored to install/first launch, so a late first update silently truncates window 1)")
    if not win.get("window2_3_signals_planned"): f.append("AA-3 no signals are planned for windows 2 (days 3-7) and 3 (days 8-35) - trial conversion and first renewal, the events those windows exist for, are unmeasured by design")
    if not win.get("lock_decision_recorded"): f.append("AA-3 no recorded lockWindow decision (locking finalises a value early for a faster postback; never locking is legitimate only as a recorded choice, not as an unconsidered default)")
    rec=d.get("receipt") or {}
    if not rec.get("asa_token_flow_present"): f.append("AA-4 the Apple Search Ads attribution token flow (AdServices AAAttribution, posted within 24h) is not present - first-party keyword attribution is missing")
    if not rec.get("postback_receipt_verified"): f.append("AA-4 postback receipt is not verified anywhere (no server copy, no MMP readback) - the team cannot show that a single postback ever arrived")
    if not rec.get("update_failures_measured"): f.append("AA-4 conversion-value update failures are not measured (a log line is not a metric - a broken update path would be invisible in every dashboard)")
    ver=d.get("verification") or {}
    if not ver.get("mapping_tests_exist"): f.append("AA-5 the event-to-value mapping and its monotonicity are not tested (the schema can regress at any call site without a single failing test)")
    if not ver.get("postback_rates_measured"): f.append("AA-5 postback outcomes are not measured (received count, null/coarse-only rate by window) - no way to know whether attribution works or silently returns nothing")
    return f
if __name__=="__main__":
    data=json.load(open(sys.argv[1])); fails=check(data)
    if fails:
        print(f"FAIL ({len(fails)}):")
        [print(" -",x) for x in fails]; sys.exit(1)
    print("PASS")
