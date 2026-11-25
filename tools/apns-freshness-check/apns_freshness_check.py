#!/usr/bin/env python3
"""apns-freshness-check: deterministic gate for APNs header freshness
(expiration / collapse / push-type / priority -> client stale guard ->
lateness measurement), for an app whose product is a timely nudge.
Stdlib only, offline, free.
Sources (read 2026-11-15):
- Apple APNs header definitions (via docs.rs apple_apns header docs,
  which reproduce Apple's field semantics): apns-expiration is the epoch
  after which the notification is no longer valid -- nonzero means APNs
  stores and retries until that date, 0 means try once and do not store;
  apns-collapse-id coalesces multiple notifications into one (<=64 bytes);
  apns-push-type must accurately reflect the payload or APNs may error,
  delay, or drop; apns-priority defaults to 10 when omitted, and a
  background push type must use priority 5 (10 is an error).
- Practitioner explainer (secondary, bimalkhatri.com.np APNs Explained):
  APNs is best-effort; for an offline device it keeps only one stored
  notification per app, for up to 30 days when no expiration is chosen --
  so an unset expiration lets a moment-bound nudge arrive long after its
  moment and still be shown.
Exit 0 = PASS, 1 = FAIL. Warnings do not fail.
Input JSON: {app,
 inventory:{recorded, kinds_listed_with_validity_window, decision_recorded},
 expiration:{expiration_set_per_kind, moment_kinds_bounded_short,
   no_unbounded_default_for_moment_kinds},
 headers:{collapse_id_coalesces_superseded_per_kind,
   push_type_matches_payload, priority_matches_kind},
 client_guard:{client_reads_scheduled_time,
   client_discards_or_replaces_stale_on_arrival,
   stale_arrival_not_recorded_as_timely},
 sender_evidence:{sender_headers_evidenced_not_assumed,
   delivery_id_joinable_to_send},
 measurement:{lateness_computed_from_scheduled_vs_delivered,
   lateness_distribution_counted, outcome_joinable_by_lateness}}
"""
import json, sys

def check(d):
    fails, warns = [], []
    inv = d.get("inventory") or {}
    if not inv.get("recorded"):
        fails.append("AH-0 the APNs freshness surface is not inventoried (which headers the sender sets -- expiration, collapse-id, push-type, priority -- is nowhere recorded; an unrecorded surface cannot be audited)")
    if not inv.get("kinds_listed_with_validity_window"):
        fails.append("AH-0 the notification kinds are not listed with a validity window (a nudge for a moment of rumination and a daily reminder do not stay true for the same length of time; without a per-kind window there is nothing to set expiration against)")
    if not inv.get("decision_recorded"):
        fails.append("AH-0 no recorded freshness decision exists (the honest states are 'moment kinds expire at their window, superseded nudges collapse, stale arrivals are discarded client-side and counted late' or an explicit recorded choice not to -- silence is not a state)")
    ex = d.get("expiration") or {}
    if not ex.get("expiration_set_per_kind"):
        fails.append("AH-1 apns-expiration is not set per kind (an omitted expiration leaves storage and retry to the platform default, so a notification for one specific moment can be delivered long after that moment has passed)")
    if not ex.get("moment_kinds_bounded_short"):
        fails.append("AH-1 moment-bound kinds do not carry a short bounded expiration (expiration must track the kind's validity window; a window of days turns a timely intervention into a late, wrong one)")
    if not ex.get("no_unbounded_default_for_moment_kinds"):
        fails.append("AH-1 an unbounded/default storage lifetime is in effect for moment kinds (APNs stores at most one notification per app for an offline device and may hold it far beyond the moment; relying on that default is a decision to deliver stale nudges)")
    hd = d.get("headers") or {}
    if not hd.get("collapse_id_coalesces_superseded_per_kind"):
        fails.append("AH-2 no apns-collapse-id coalesces superseded nudges per kind (without it, stored and fresh nudges for the same habit pile up as separate notifications instead of the newest replacing the older)")
    if not hd.get("push_type_matches_payload"):
        fails.append("AH-2 apns-push-type matching the payload is not evidenced (Apple: the value must accurately reflect the payload contents; a mismatch can make APNs error, delay, or drop the notification)")
    if not hd.get("priority_matches_kind"):
        fails.append("AH-2 apns-priority is not matched to kind (alerts that must arrive at their moment use immediate priority; any background-type send must use priority 5 -- 10 with background is an error, and an omitted header silently defaults to 10)")
    cg = d.get("client_guard") or {}
    if not cg.get("client_reads_scheduled_time"):
        fails.append("AH-3 the client never reads the scheduled/intended time carried with the notification (without it the client cannot know the notification is late, however late APNs delivers it)")
    if not cg.get("client_discards_or_replaces_stale_on_arrival"):
        fails.append("AH-3 the client does not discard or replace a stale arrival (reading scheduledTime to personalize a message is not a freshness guard; a nudge that arrives after its window must be dropped or replaced with the current moment's words, not presented as timely)")
    if not cg.get("stale_arrival_not_recorded_as_timely"):
        fails.append("AH-3 a stale arrival can be recorded as a timely delivery (if the outcome record says only 'delivered' with the delivery date and never compares it to the scheduled time, late delivery is indistinguishable from on-time delivery in the data the product learns from)")
    se = d.get("sender_evidence") or {}
    if not se.get("sender_headers_evidenced_not_assumed"):
        fails.append("AH-4 the sender's header values are not evidenced (the sending code or its config must be read, in the repo or the sender's own records; header behaviour assumed from the client's existence is not evidence, and a sender outside the client repo stays unverified until read)")
    if not se.get("delivery_id_joinable_to_send"):
        fails.append("AH-4 no delivery identifier joins the send to the client outcome (without a shared id carried in the payload and read on arrival, a late delivery cannot be traced to the send that was supposed to arrive on time)")
    ms = d.get("measurement") or {}
    if not ms.get("lateness_computed_from_scheduled_vs_delivered"):
        fails.append("AH-5 lateness is never computed (scheduled/intended time versus actual delivery time is the surface's core quantity; a funnel that counts deliveries without lateness cannot see freshness failing)")
    if not ms.get("lateness_distribution_counted"):
        fails.append("AH-5 no lateness distribution is counted (share delivered inside the window, share late, share expired/never delivered; without the distribution the size of the stale-delivery problem is opinion)")
    if not ms.get("outcome_joinable_by_lateness"):
        fails.append("AH-5 outcome cannot be joined by lateness (opened/responded for on-time versus late deliveries), so whether a stale nudge still helps -- or actively harms by arriving in the wrong moment -- is unknowable")
    return fails, warns

def main():
    d = json.load(open(sys.argv[1]))
    fails, warns = check(d)
    for w in warns: print("WARN:", w)
    for f in fails: print("FAIL:", f)
    print(f"{'PASS' if not fails else 'FAIL'}: {len(fails)} fail(s), {len(warns)} warning(s) -- {d.get('app')}")
    sys.exit(0 if not fails else 1)

if __name__ == "__main__":
    main()
