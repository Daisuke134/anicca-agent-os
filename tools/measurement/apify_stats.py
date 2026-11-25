#!/usr/bin/env python3
"""Fetch Apify public Actor stats (no auth) into the measurement ledger.

Source: public API GET https://api.apify.com/v2/acts/{username}~{actorName}
(audit: hidden_files/apify-promptbase-audit-2026-11-06.md — public metrics
need no token; earnings need the vault-held API token, separate route).

Writes one {type:"apify", ...} row per run into measurement-ledger.jsonl.
On failure an error row is written instead — the ledger records the outage,
it never stays silent.
"""
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

LEDGER = Path(
    "/home/hatch/workspace/goals/anicca-revenue-growth-as-life-manager/"
    "hidden_files/measurement-ledger.jsonl"
)
ACTOR = "salubrious_verity~google-maps-lead-scraper"
API = f"https://api.apify.com/v2/acts/{ACTOR}"


def fetch(retries: int = 4) -> dict:
    delay = 5.0
    last_exc = None
    for attempt in range(retries):
        try:
            r = requests.get(API, timeout=60)
            r.raise_for_status()
            return r.json()["data"]
        except Exception as e:  # noqa: BLE001
            last_exc = e
            if attempt < retries - 1:
                time.sleep(delay)
                delay = min(delay * 2, 60.0)
    raise last_exc


def main() -> int:
    ts = datetime.now(timezone.utc).isoformat()
    row = {"type": "apify", "ts": ts, "actor": ACTOR.replace("~", "/")}
    try:
        d = fetch()
        st = d.get("stats") or {}
        prs = st.get("publicActorRunStats30Days") or {}
        total30 = prs.get("TOTAL", 0)
        succ30 = prs.get("SUCCEEDED", 0)
        pricing = (d.get("pricingInfos") or [{}])[0]
        row.update(
            actor_id=d.get("id"),
            total_runs=st.get("totalRuns"),
            total_users=st.get("totalUsers"),
            total_users_7d=st.get("totalUsers7Days"),
            total_users_30d=st.get("totalUsers30Days"),
            total_users_90d=st.get("totalUsers90Days"),
            reviews=st.get("actorReviewCount"),
            review_rating=st.get("actorReviewRating"),
            bookmarks=st.get("bookmarkCount"),
            runs30d_total=total30,
            runs30d_succeeded=succ30,
            runs30d_timed_out=prs.get("TIMED-OUT", 0),
            runs30d_failed=prs.get("FAILED", 0),
            success_rate30d_computed=(succ30 / total30) if total30 else None,
            pricing_model=pricing.get("pricingModel"),
            modified_at=d.get("modifiedAt"),
            last_run_started_at=st.get("lastRunStartedAt"),
        )
    except Exception as e:  # noqa: BLE001
        row["error"] = f"{type(e).__name__}: {e}"
    with LEDGER.open("a") as f:
        f.write(json.dumps(row) + "\n")
    if "error" in row:
        print(f"apify stats: ERROR {row['error']}")
        return 1
    print(
        "apify stats: total_runs={total_runs} total_users={total_users} "
        "runs30d={runs30d_total} succeeded={runs30d_succeeded} "
        "timed_out={runs30d_timed_out} reviews={reviews}".format(**row)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
