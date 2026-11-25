#!/usr/bin/env python3
"""Fetch Apify revenue-side state (auth) into the measurement ledger.

Standing home: cron anicca-measurement-loop (15m), hourly-gated step —
this script self-gates: if the newest {type:"apify_revenue"} row in the
ledger is <55 minutes old it exits 0 without calling the API
(--force overrides). Same convention as the loop's LinkedIn/TikTok steps.

What is measured (実測のみ — estimates are never written):
- Account: GET /v2/users/me with the vault-held API token
  (credentials.json, service "apify", key api_token — the value is read
  in-process only and never printed or written anywhere).
- Own monthly usage: GET /v2/users/me/usage/monthly (cost side).
- Revenue drivers for both monetized Actors (public, no auth):
  GET /v2/acts/{username}~{actorName} — runs/users/pricing, the same
  source apify_stats.py uses for type:"apify" rows.
- Developer earnings (the payout figure): Apify API v2 exposes no
  public earnings endpoint (docs checked 2026-11-21; earnings live in
  Console > Monetization). If /v2/users/me ever returns monetization /
  earnings fields they are copied verbatim; otherwise earnings_usd
  stays null and earnings_status says 未計測 with the reason — the
  ledger never fills the gap with an estimate.

On failure an error row is still written — the ledger records the
outage, it never stays silent (same rule as apify_stats.py).
"""
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

LEDGER = Path(
    "/home/hatch/workspace/goals/anicca-revenue-growth-as-life-manager/"
    "hidden_files/measurement-ledger.jsonl"
)
VAULT = Path("/home/hatch/workspace/anicca-ops/credentials.json")
API = "https://api.apify.com/v2"
ACTORS = [
    "anicca~app-store-reviews-rankings",
    "salubrious_verity~google-maps-lead-scraper",
]
GATE_MINUTES = 55


def last_row_age_minutes() -> float | None:
    if not LEDGER.exists():
        return None
    last_ts = None
    with LEDGER.open() as f:
        for line in f:
            if '"apify_revenue"' not in line:
                continue
            try:
                ts = json.loads(line).get("ts")
            except Exception:  # noqa: BLE001
                continue
            if ts:
                last_ts = ts
    if not last_ts:
        return None
    then = datetime.fromisoformat(last_ts)
    return (datetime.now(timezone.utc) - then).total_seconds() / 60.0


def load_token() -> str:
    data = json.loads(VAULT.read_text())
    for entry in data.get("credentials", []):
        if entry.get("service") == "apify" and entry.get("api_token"):
            return entry["api_token"]
    raise RuntimeError("apify api_token not found in vault")


def fetch(url: str, headers: dict | None = None, retries: int = 4) -> dict:
    delay = 5.0
    last_exc = None
    for attempt in range(retries):
        try:
            r = requests.get(url, headers=headers or {}, timeout=60)
            r.raise_for_status()
            return r.json()
        except Exception as e:  # noqa: BLE001
            last_exc = e
            if attempt < retries - 1:
                time.sleep(delay)
                delay = min(delay * 2, 60.0)
    raise last_exc


def actor_stats(slug: str) -> dict:
    d = fetch(f"{API}/acts/{slug}")["data"]
    st = d.get("stats") or {}
    prs = st.get("publicActorRunStats30Days") or {}
    pricing = (d.get("pricingInfos") or [{}])[0]
    out = {
        "actor": slug.replace("~", "/"),
        "actor_id": d.get("id"),
        "total_runs": st.get("totalRuns"),
        "total_users": st.get("totalUsers"),
        "total_users_30d": st.get("totalUsers30Days"),
        "runs30d_total": prs.get("TOTAL", 0),
        "runs30d_succeeded": prs.get("SUCCEEDED", 0),
        "pricing_model": pricing.get("pricingModel"),
        "last_run_started_at": st.get("lastRunStartedAt"),
    }
    # PAY_PER_EVENT price detail, when the API returns it (verbatim only).
    for key in ("pricePerUnitUsd", "eventTieredPricingUsd", "unitPriceUsd"):
        if pricing.get(key) is not None:
            out[f"pricing_{key}"] = pricing[key]
    return out


def main() -> int:
    force = "--force" in sys.argv
    age = last_row_age_minutes()
    if not force and age is not None and age < GATE_MINUTES:
        print(f"apify revenue: skip (last row {age:.0f} min ago, hourly gate)")
        return 0

    ts = datetime.now(timezone.utc).isoformat()
    row: dict = {"type": "apify_revenue", "ts": ts}
    errors: list[str] = []
    try:
        token = load_token()
        auth = {"Authorization": f"Bearer {token}"}

        try:
            me = fetch(f"{API}/users/me", headers=auth)["data"]
            row["account_username"] = me.get("username")
            plan = me.get("plan") or {}
            row["plan_id"] = plan.get("id")
            row["plan_description"] = plan.get("description")
            # Copy earnings verbatim IF the API ever returns them.
            for key, val in me.items():
                lk = key.lower()
                if ("monetiz" in lk or "earning" in lk) and isinstance(
                    val, (int, float)
                ):
                    row[f"account_{key}"] = val
        except Exception as e:  # noqa: BLE001
            errors.append(f"users/me: {type(e).__name__}: {e}")

        try:
            usage = fetch(f"{API}/users/me/usage/monthly", headers=auth)["data"]
            if isinstance(usage, dict):
                row["usage_monthly_keys"] = sorted(usage.keys())
                for key in (
                    "totalUsageCreditsUsd",
                    "totalUsageUsd",
                    "monthlyUsageUsd",
                ):
                    if usage.get(key) is not None:
                        row[f"usage_{key}"] = usage[key]
            elif isinstance(usage, list) and usage:
                row["usage_monthly_entries"] = len(usage)
        except Exception as e:  # noqa: BLE001
            errors.append(f"usage/monthly: {type(e).__name__}: {e}")

        actors = []
        for slug in ACTORS:
            try:
                actors.append(actor_stats(slug))
            except Exception as e:  # noqa: BLE001
                errors.append(f"acts/{slug}: {type(e).__name__}: {e}")
        row["actors"] = actors

        if "account_username" in row or actors:
            row.setdefault("earnings_usd", None)
            row["earnings_status"] = (
                "未計測: Apify API v2 に開発者収益の公開エンドポイントなし"
                "（収益は Console の Monetization 画面のみ）。"
                "本行では収益ドライバー（各 Actor の runs/users/価格）と"
                "当社 usage を実測として記録する"
            )
    except Exception as e:  # noqa: BLE001
        errors.append(f"fatal: {type(e).__name__}: {e}")

    if errors:
        row["error"] = "; ".join(errors)
    with LEDGER.open("a") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    if errors and "account_username" not in row and not row.get("actors"):
        print(f"apify revenue: ERROR {row['error']}")
        return 1
    print(
        "apify revenue: actors={n} earnings_usd={e} errors={err}".format(
            n=len(row.get("actors", [])),
            e=row.get("earnings_usd"),
            err=row.get("error", "none"),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
