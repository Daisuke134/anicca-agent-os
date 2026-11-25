#!/usr/bin/env python3
"""ASO keyword position tracker for the non-Anicca apps (same method and
ledger as aso_rank.py: iTunes Search API, free, no auth). Rows are written
with type="aso_app" so the Anicca-only consumers (rankings_snapshot.py,
which filters type="aso") are unaffected. Tracks each app's own position
only; no comparison app is fixed yet for these apps."""
import json, urllib.parse, urllib.request, datetime, os

APPS = {
    "honne": {"id": 6759667221, "name": "Honne",
              "keywords": {"JP": ["本音", "恋愛相談", "脈あり", "返信"],
                           "US": ["relationship advice", "texting advice"]}},
    "dhamma": {"id": 6757726663, "name": "Dhamma Quotes (Daily Dhamma)",
               "keywords": {"US": ["buddhist quotes", "buddha quotes", "dhamma"],
                            "JP": ["仏教", "法句経"]}},
    "sleep_reset": {"id": 6762143790, "name": "Sleep Reset",
                    "keywords": {"US": ["sleep tracker", "better sleep", "insomnia help"],
                                 "JP": ["睡眠", "不眠"]}},
    "thankful": {"id": 6759514159, "name": "Thankful - Gratitude Journal",
                 "keywords": {"US": ["gratitude journal", "gratitude"],
                              "JP": ["感謝日記", "感謝"]}},
    "studio_cherie": {"id": 6766485903, "name": "STUDIO CHERIE",
                      "keywords": {"JP": ["コーディネート", "着回し", "クローゼット"],
                                   "US": ["outfit planner", "wardrobe organizer"]}},
}
LEDGER = os.path.expanduser("~/workspace/goals/anicca-revenue-growth-as-life-manager/hidden_files/measurement-ledger.jsonl")

def fetch(term, country):
    q = urllib.parse.urlencode({"term": term, "country": country,
                                "entity": "software", "limit": 200})
    req = urllib.request.Request("https://itunes.apple.com/search?" + q,
                                 headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)["results"]

def main():
    ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
    rows = []
    for slug, cfg in APPS.items():
        target = str(cfg["id"])
        for country, kws in cfg["keywords"].items():
            for kw in kws:
                try:
                    res = fetch(kw, country)
                except Exception as e:
                    rows.append({"type": "aso_app", "ts": ts, "app": slug,
                                 "app_id": cfg["id"], "country": country,
                                 "keyword": kw, "error": str(e)})
                    continue
                pos = None
                for i, r in enumerate(res, 1):
                    if str(r["trackId"]) == target:
                        pos = i
                        break
                top1 = res[0]["trackName"] if res else None
                rows.append({"type": "aso_app", "ts": ts, "app": slug,
                             "app_id": cfg["id"], "country": country,
                             "keyword": kw, "returned": len(res),
                             "top1": top1, "pos": pos})
                print(f"{cfg['name']} {country} {kw!r}: pos={pos} n={len(res)} top1={top1}")
    with open(LEDGER, "a") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"appended {len(rows)} rows to ledger")

if __name__ == "__main__":
    main()
