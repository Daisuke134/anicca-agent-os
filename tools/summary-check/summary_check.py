#!/usr/bin/env python3
"""summary-check: deterministic gate for the Scheduled Summary stack
(per-kind delivery intent -> breakthrough honesty -> relevance scoring ->
thread grouping -> scheduledDeliverySetting re-read -> measurement),
for an app whose product is a timely nudge. Stdlib only, offline, free.
Sources (read 2026-11-15):
- Apple WWDC21 session 10091 "Send communication and Time Sensitive
  notifications" (transcript read via apple-docs mirror): notifications
  can be delivered at scheduled times of day as a summary, presented
  collectively at preset times; include media attachments for a better
  chance to be featured at the top of the summary; adopt the relevance
  score API so the right notifications from the app get featured.
- Apple UNNotificationContent.relevanceScore documentation (as quoted in
  OneSignal's iOS relevance score doc, read 2026-11-15): the system uses
  relevanceScore, a value between 0 and 1, to sort the notifications
  from your app; the highest score gets featured in the notification
  summary. The score is compared only against the same app's
  notifications, applies only to people who enabled Scheduled Summary
  for the app (iOS 15+), and does not change delivery timing -- timing
  is governed by the interruption level (time-sensitive breaks through
  the summary; see ts-check).
Exit 0 = PASS, 1 = FAIL. Warnings do not fail.
Input JSON: {app,
 inventory:{recorded, per_kind_delivery_intent_defined, decision_recorded},
 breakthrough:{moment_bound_kind_has_breakthrough_path,
   no_kind_claims_immediacy_without_mechanism,
   marketing_never_uses_breakthrough},
 relevance:{payload_or_nse_sets_relevance_score,
   scores_differentiated_by_kind, featured_kind_is_highest_scored},
 grouping:{thread_id_set_per_kind, thread_scheme_coherent},
 setting:{scheduled_delivery_setting_reread,
   onboarding_explains_summary_choice,
   in_app_fallback_when_scheduled},
 measurement:{event_defined, event_fired,
   scheduled_delivery_share_counted, delay_joinable_to_outcome}}
"""
import json, sys

def check(d):
    fails, warns = [], []
    inv = d.get("inventory") or {}
    if not inv.get("recorded"):
        fails.append("SUM-0 the Scheduled Summary surface is not inventoried (which notification kinds exist, and for each kind whether summary-delayed delivery is acceptable, are nowhere recorded; an unrecorded surface cannot be audited)")
    if not inv.get("per_kind_delivery_intent_defined"):
        fails.append("SUM-0 no per-kind delivery intent exists (Scheduled Summary is an all-or-nothing setting per app, so the only design lever is deciding kind by kind which notifications must arrive at their moment and which may wait for the next summary window; without that table every kind is summary-eligible by drift)")
    if not inv.get("decision_recorded"):
        fails.append("SUM-0 no recorded decision exists for summary behaviour (the honest states are 'these kinds break through, these kinds are scored for the summary, and we measure the scheduled share' -- silence is not a state)")
    bt = d.get("breakthrough") or {}
    if not bt.get("moment_bound_kind_has_breakthrough_path"):
        fails.append("SUM-1 the moment-bound kind has no breakthrough path (a nudge whose value is its moment, delivered in a summary hours later, is a different and weaker intervention; the only documented breakthrough is the time-sensitive interruption level actually carried in the payload or content -- an entitlement or a settings toggle alone breaks through nothing)")
    if not bt.get("no_kind_claims_immediacy_without_mechanism"):
        fails.append("SUM-1 a kind claims immediacy in product copy or onboarding without a mechanism that delivers it (promising 'the right words at the right moment' while every notification is summary-eligible is a claim the delivery layer cannot keep)")
    if not bt.get("marketing_never_uses_breakthrough"):
        fails.append("SUM-1 marketing content uses the breakthrough path (time-sensitive is reserved for content that is relevant right now or within the hour; spending it on promotion trains the system and the person to revoke it, and the revocation takes the moment-bound kinds down with it)")
    rv = d.get("relevance") or {}
    if not rv.get("payload_or_nse_sets_relevance_score"):
        fails.append("SUM-2 no delivery path ever sets a relevance score (for remote delivery the APNs payload must carry relevance-score, or the Notification Service Extension must set relevanceScore on the content; Apple WWDC21: adopt the relevance score API so the right notifications get featured. A score no path sets means the system features an arbitrary one of your notifications)")
    if not rv.get("scores_differentiated_by_kind"):
        fails.append("SUM-2 relevance scores are not differentiated by kind (a single constant -- worst of all 1.0 on everything -- sorts nothing; the score only has meaning as an ordering across the app's own kinds, with the kind the product most wants seen at the top)")
    if not rv.get("featured_kind_is_highest_scored"):
        fails.append("SUM-2 the kind the product would feature is not the highest scored (the featured slot in the summary is the one piece of summary real estate the app controls; if it belongs to a housekeeping kind, the summary leads with the least important thing the app said that day)")
    gr = d.get("grouping") or {}
    if not gr.get("thread_id_set_per_kind"):
        fails.append("SUM-3 no delivery path sets a thread identifier (for remote delivery the payload thread-id, or the extension setting threadIdentifier; without it the summary and Notification Center cannot group the app's notifications coherently, and related nudges scatter as unrelated interruptions)")
    if not gr.get("thread_scheme_coherent"):
        fails.append("SUM-3 the thread scheme is not coherent (one thread per ongoing topic or habit -- not one global thread that buries distinct moments together, and not a fresh random thread per message that defeats grouping entirely)")
    st = d.get("setting") or {}
    if not st.get("scheduled_delivery_setting_reread"):
        fails.append("SUM-4 notificationSettings().scheduledDeliverySetting is never re-read (this is the only client-side signal of whether the person put the app into scheduled delivery; an app that never reads it cannot tell a delivered nudge from a warehoused one)")
    if not st.get("onboarding_explains_summary_choice"):
        fails.append("SUM-4 onboarding never addresses the summary choice (when Scheduled Summary is on, the system offers people 'deliver immediately or in summary' for the app; an app whose value is timing that never explains why its moment-bound kind belongs in immediate delivery leaves the choice to a default dialog it does not control)")
    if not st.get("in_app_fallback_when_scheduled"):
        fails.append("SUM-4 there is no in-app fallback when scheduled delivery is on (if the moment's words are warehoused until the evening summary, opening the app must still surface them at their moment; otherwise scheduled delivery silently deletes the intervention for exactly the people who opted into summaries)")
    ms = d.get("measurement") or {}
    if not ms.get("event_defined"):
        fails.append("SUM-5 no summary measurement event exists at all (scheduled-delivery state at send/open time is unknowable in principle; whether summaries are eating the intervention is a matter of opinion)")
    elif not ms.get("event_fired"):
        fails.append("SUM-5 the summary event is defined but fired from 0 call sites (a defined-but-unfired event reads as 'delivery is fine' forever, indistinguishable from the truth)")
    if not ms.get("scheduled_delivery_share_counted"):
        fails.append("SUM-5 the scheduled-delivery share is not counted (scheduledDeliverySetting == enabled among authorized users is the surface's exposure denominator; without it a delay problem cannot be sized)")
    if not ms.get("delay_joinable_to_outcome"):
        fails.append("SUM-5 delivery delay cannot be joined to outcome (sent-at versus opened-at by kind, split by scheduled-delivery state), so whether summary delay costs the response the nudge exists to produce is unknowable")
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
