#!/usr/bin/env python3
"""Standing D1/D7 retention aggregation (Issue #50, added 2026-11-12).

Companion to funnel_cohort.py: same Mixpanel Raw Export source (shared
project 3970220) and the same fixed counting rules (Issue #46 aggregation
default):

  - app_environment = "production" only (simulator/sandbox never enter
    the cohort; cohort membership is decided by a production app_opened)
  - virtual device models ($model starting "iPhone99,") excluded
  - days are UTC calendar days, as in funnel_cohort.py

Definitions:
  - Cohort: distinct_id whose FIRST production app_opened in the export
    range falls inside [start, end]. The export starts 7 days before
    `start` (lead-in) so that users already active before the window
    are not misread as new; a user whose in-range first open is in the
    lead-in is not a cohort member.
  - Return on day X: the same distinct_id has an app_opened in the same
    app bucket on UTC day X (any environment tag on the return event;
    distinct_id is per device install, and the cohort itself is
    production-only).
  - D1 retained: return on cohort_day + 1. D7 retained: cohort_day + 7.
  - A cohort day is D1/D7-eligible only when its target day is a fully
    observed day (<= last_complete_day). Rates always carry their
    denominator (eligible cohort users); nothing is estimated.
  - Apps with no eligible cohort are emitted with status "unmeasured"
    plus a reason; apps with no events in the project at all are
    emitted with status "no_events_received" (same style as
    funnel_cohort.py), so the row exists and fills automatically.

Anicca note (same as funnel_cohort.py): legacy Anicca builds predate
app_id tagging; their rows carry app_id=None and Anicca-only events.
Dhamma/Thankful rows are always tagged, so None rows are Anicca's.

Auth: Mixpanel service account from anicca-ops credentials.json
(entry service="mixpanel"); the secret is never printed.
Usage: retention_d1d7.py YYYY-MM-DD YYYY-MM-DD <output.json>
"""
import json, sys, urllib.request, base64, collections, datetime, pathlib

APPS = {
    "ai.anicca.app.ios": "Anicca",
    "com.dailydhamma.app": "Dhamma Quotes",
    "app.rork.thankful-gratitude-app": "Thankful",
}
NO_EVENT_APPS = {"Honne": "no app_id received in project 3970220 yet",
                 "Sleep Reset": "no app_id received in project 3970220 yet",
                 "STUDIO CHERIE": "no app_id received in project 3970220 yet"}
LEAD_IN_DAYS = 7
OBSERVE_AFTER_DAYS = 7  # so the last cohort day's D7 target can be exported


def daterange(a, b):
    d = a
    while d <= b:
        yield d
        d += datetime.timedelta(days=1)


def main():
    start_s, end_s, out_path = sys.argv[1], sys.argv[2], sys.argv[3]
    start = datetime.date.fromisoformat(start_s)
    end = datetime.date.fromisoformat(end_s)
    today = datetime.date.today()
    export_from = start - datetime.timedelta(days=LEAD_IN_DAYS)
    export_to = min(end + datetime.timedelta(days=OBSERVE_AFTER_DAYS), today)
    # A day counts as fully observed when the export covers it entirely:
    # every exported day before today is complete; today is partial.
    last_complete_day = export_to if export_to < today else today - datetime.timedelta(days=1)

    cred = json.load(open(pathlib.Path.home() / "workspace/anicca-ops-push/credentials.json"))["credentials"]
    mp = next(e for e in cred if isinstance(e, dict) and e.get("service") == "mixpanel")
    auth = base64.b64encode(f"{mp['username']}:{mp['secret']}".encode()).decode()
    url = (f"https://data.mixpanel.com/api/2.0/export?project_id=3970220"
           f"&from_date={export_from.isoformat()}&to_date={export_to.isoformat()}")
    req = urllib.request.Request(url)
    req.add_header("Authorization", "Basic " + auth)
    with urllib.request.urlopen(req, timeout=300) as r:
        rows = [json.loads(l) for l in r.read().decode().splitlines() if l.strip()]

    def P(r, k):
        return r["properties"].get(k)

    def day(r):
        return datetime.datetime.utcfromtimestamp(P(r, "time")).date()

    result = {
        "window": {"start": start_s, "end": end_s},
        "export": {"from": export_from.isoformat(), "to": export_to.isoformat(),
                   "lead_in_days": LEAD_IN_DAYS,
                   "last_complete_day": last_complete_day.isoformat()},
        "filter_declaration": {"app_environment": "production", "virtual_device_models": "excluded"},
        "definitions": {
            "cohort": "distinct_id whose first production app_opened in the export range falls in [start, end]",
            "return": "app_opened by the same distinct_id in the same app bucket on the target UTC day",
            "d1": "return on cohort_day + 1", "d7": "return on cohort_day + 7",
            "eligibility": "cohort day counts only when its target day <= last_complete_day",
        },
        "apps": {},
    }

    app_ids = sorted({P(r, "app_id") for r in rows if P(r, "app_id")})
    buckets = {}
    for app_id in app_ids:
        if app_id == "ai.anicca.app.ios":
            buckets[app_id] = [r for r in rows if P(r, "app_id") in ("ai.anicca.app.ios", None)]
        else:
            buckets[app_id] = [r for r in rows if P(r, "app_id") == app_id]

    for app_id, arows in buckets.items():
        first = {}          # user -> (time, model, first_day)
        open_days = collections.defaultdict(set)  # user -> {days with app_opened}
        for r in arows:
            if r["event"] != "app_opened":
                continue
            u = P(r, "distinct_id")
            open_days[u].add(day(r))
            if P(r, "app_environment") != "production":
                continue
            t = P(r, "time")
            if u not in first or t < first[u][0]:
                first[u] = (t, P(r, "$model"), day(r))
        cohort = {u: v[2] for u, v in first.items()
                  if start <= v[2] <= end and not (v[1] or "").startswith("iPhone99")}
        by_day = collections.Counter(cohort.values())

        def metric(offset):
            per_day = []
            elig = retained = 0
            for d in daterange(start, end):
                members = [u for u, cd in cohort.items() if cd == d]
                if not members:
                    continue
                target = d + datetime.timedelta(days=offset)
                if target > last_complete_day:
                    per_day.append({"cohort_day": d.isoformat(), "cohort_users": len(members),
                                    "status": "not_yet_observable",
                                    "reason": f"target day {target.isoformat()} is after last complete day {last_complete_day.isoformat()}"})
                    continue
                kept = sum(1 for u in members if target in open_days.get(u, set()))
                elig += len(members)
                retained += kept
                per_day.append({"cohort_day": d.isoformat(), "cohort_users": len(members),
                                "status": "measured", "retained_users": kept})
            if elig == 0:
                if not cohort:
                    return {"status": "unmeasured", "reason": "no production first-open cohort in window (0 users)",
                            "eligible_cohort_users": 0, "retained_users": None, "rate": None, "per_day": per_day}
                return {"status": "unmeasured",
                        "reason": f"no cohort day has its target day on or before last complete day {last_complete_day.isoformat()} (window not matured)",
                        "eligible_cohort_users": 0, "retained_users": None, "rate": None, "per_day": per_day}
            return {"status": "measured", "eligible_cohort_users": elig, "retained_users": retained,
                    "rate": round(retained / elig, 4), "per_day": per_day}

        name = APPS.get(app_id, app_id)
        result["apps"][name] = {
            "app_id": app_id, "status": "measured" if cohort else "unmeasured",
            "cohort_users": len(cohort),
            "cohort_by_day": {d.isoformat(): by_day[d] for d in sorted(by_day)},
            "d1_retention": metric(1),
            "d7_retention": metric(7),
        }
        if not cohort:
            result["apps"][name]["note"] = "no production first-open cohort in window; D1/D7 stay unmeasured (not 0)"

    for name, why in NO_EVENT_APPS.items():
        if name not in result["apps"]:
            result["apps"][name] = {"status": "no_events_received", "note": why,
                                    "receiver": "this script already emits the row; it fills automatically from the first window with events"}

    pathlib.Path(out_path).write_text(json.dumps(result, ensure_ascii=False, indent=1))
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
