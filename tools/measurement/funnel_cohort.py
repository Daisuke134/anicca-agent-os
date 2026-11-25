#!/usr/bin/env python3
"""Unified funnel cohort builder (standing receiver, added 2026-11-12).

Pulls the Mixpanel Raw Export for [start, end+1day] from the shared
project (3970220) and builds, for EVERY app_id present in the project
(plus the six known apps), the in-app part of the one-chain funnel:

  first open -> onboarding started -> goal screen -> plan step ->
  reminder step -> notifications screen -> notification result ->
  onboarding completed -> first affirmation -> review prompt shown ->
  paywall shown -> purchase started -> purchase completed

Counting rules (fixed by the Issue #46 aggregation default):
  - app_environment = "production" only (simulator/sandbox never enter)
  - virtual device models ($model starting "iPhone99,") excluded
  - cohort = distinct_id whose first production app_opened falls in
    [start, end]; steps counted on/after the first-open day (UTC)
    through end+1 day (the export's last day)
  - the plan step and reminder step each carry two screen_id names
    across builds (plan_reveal/first_affirmation, nudge_times/
    reminder_schedule); they are the same logical steps and are summed
Apps with no events in the project are emitted with status
"no_events_received" so the chain row exists and fills automatically
from the first window in which events arrive.
Auth: Mixpanel service account from anicca-ops credentials.json
(entry service="mixpanel"); the secret is never printed.
Usage: funnel_cohort.py YYYY-MM-DD YYYY-MM-DD <output.json>
"""
import json, sys, urllib.request, base64, collections, datetime, pathlib

APPS = {
    "ai.anicca.app.ios": "Anicca",
    "com.dailydhamma.app": "Dhamma Quotes",
    "app.rork.thankful-gratitude-app": "Thankful",
    None: None,  # filled below with no-event apps
}
NO_EVENT_APPS = {"Honne": "no app_id received in project 3970220 yet",
                 "Sleep Reset": "no app_id received in project 3970220 yet",
                 "STUDIO CHERIE": "no app_id received in project 3970220 yet"}

def main():
    start, end, out_path = sys.argv[1], sys.argv[2], sys.argv[3]
    end_export = (datetime.date.fromisoformat(end) + datetime.timedelta(days=1)).isoformat()
    cred = json.load(open(pathlib.Path.home() / "workspace/anicca-ops-push/credentials.json"))["credentials"]
    mp = next(e for e in cred if isinstance(e, dict) and e.get("service") == "mixpanel")
    auth = base64.b64encode(f"{mp['username']}:{mp['secret']}".encode()).decode()
    url = f"https://data.mixpanel.com/api/2.0/export?project_id=3970220&from_date={start}&to_date={end_export}"
    req = urllib.request.Request(url); req.add_header("Authorization", "Basic " + auth)
    with urllib.request.urlopen(req, timeout=300) as r:
        rows = [json.loads(l) for l in r.read().decode().splitlines() if l.strip()]
    def P(r, k): return r["properties"].get(k)
    def day(r): return datetime.datetime.utcfromtimestamp(P(r, "time")).strftime("%Y-%m-%d")
    result = {"window": {"start": start, "end": end, "steps_through": end_export},
              "filter_declaration": {"app_environment": "production", "virtual_device_models": "excluded"},
              "apps": {}}
    app_ids = sorted({P(r, "app_id") for r in rows if P(r, "app_id")})
    for app_id in app_ids:
        if app_id == "ai.anicca.app.ios":
            # Legacy Anicca builds predate app_id tagging: their rows carry
            # app_id=None and Anicca-only events (affirmation_viewed, the
            # onboarding.* screen ids). Dhamma/Thankful rows are always
            # tagged, so None rows are Anicca's.
            arows = [r for r in rows if P(r, "app_id") in ("ai.anicca.app.ios", None)]
        else:
            arows = [r for r in rows if P(r, "app_id") == app_id]
        first = {}
        for r in arows:
            if r["event"] != "app_opened" or P(r, "app_environment") != "production": continue
            u = P(r, "distinct_id"); t = P(r, "time")
            if u not in first or t < first[u][0]: first[u] = (t, P(r, "$model"), day(r))
        cohort = {u: v for u, v in first.items() if start <= v[2] <= end and not (v[1] or "").startswith("iPhone99")}
        def cnt(ev, extra=None):
            s = set()
            for r in arows:
                u = P(r, "distinct_id")
                if u not in cohort or r["event"] != ev or day(r) < cohort[u][2]: continue
                if extra and not extra(r): continue
                s.add(u)
            return len(s)
        res = collections.Counter()
        for u in cohort:
            cands = [r for r in arows if P(r, "distinct_id") == u and r["event"] == "notification_permission_result" and day(r) >= cohort[u][2]]
            if cands: res[P(min(cands, key=lambda r: P(r, "time")), "result")] += 1
        name = APPS.get(app_id, app_id)
        result["apps"][name] = {
            "app_id": app_id, "status": "measured",
            "first_open_users": len(cohort),
            "onboarding_started": cnt("onboarding_started"),
            "screen_goal": cnt("screen_viewed", lambda r: P(r, "screen_id") == "onboarding.goal"),
            "screen_plan_step": cnt("screen_viewed", lambda r: P(r, "screen_id") in ("onboarding.plan_reveal", "onboarding.first_affirmation")),
            "screen_reminder_step": cnt("screen_viewed", lambda r: P(r, "screen_id") in ("onboarding.nudge_times", "onboarding.reminder_schedule")),
            "screen_notifications": cnt("screen_viewed", lambda r: P(r, "screen_id") == "onboarding.notifications"),
            "notification_first_result": dict(res),
            "onboarding_completed": cnt("onboarding_completed"),
            "first_affirmation_viewed": cnt("first_affirmation_viewed"),
            "review_prompt_shown_users": cnt("rating_store_review_requested") + cnt("rating_prompt_shown"),
            "paywall_shown": cnt("paywall_shown"),
            "purchase_started": cnt("purchase_started"),
            "purchase_completed_client": cnt("purchase_completed"),
        }
    for name, why in NO_EVENT_APPS.items():
        if name not in result["apps"]:
            result["apps"][name] = {"status": "no_events_received", "note": why,
                                    "receiver": "this script already emits the chain row; it fills automatically from the first window with events"}
    pathlib.Path(out_path).write_text(json.dumps(result, ensure_ascii=False, indent=1))
    print(json.dumps(result, ensure_ascii=False))

if __name__ == "__main__":
    main()
