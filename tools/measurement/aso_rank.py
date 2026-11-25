#!/usr/bin/env python3
"""ASO keyword position tracker via Apple iTunes Search API (free, no auth).
Records the App Store search-result position of a target app (and optional
comparison apps) for a keyword set, per storefront. Appends JSONL to a ledger.
Note: iTunes Search API ordering is Apple's relevance order used as the
standard free proxy for App Store search position; it is not the ASA
popularity score (that requires Apple Search Ads / Astro on Mac).
"""
import json, sys, urllib.parse, urllib.request, datetime, os

TARGET = 6755129214           # Anicca - Daily Affirmations
COMPARE = {874656917: "I am"} # winner app for side-by-side
KEYWORDS = {
    "US": ["affirmation", "affirmations", "daily affirmations",
           "positive affirmations", "i am affirmations", "self love",
           "meditation", "gratitude", "motivation", "mindfulness"],
    "JP": ["アファメーション", "自己肯定感", "瞑想", "ポジティブ",
           "感謝", "モチベーション", "マインドフルネス"],
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
    for country, kws in KEYWORDS.items():
        for kw in kws:
            try:
                res = fetch(kw, country)
            except Exception as e:
                rows.append({"type": "aso", "ts": ts, "country": country,
                             "keyword": kw, "error": str(e)})
                continue
            pos = {str(TARGET): None}
            for name_id in COMPARE:
                pos[str(name_id)] = None
            for i, r in enumerate(res, 1):
                tid = str(r["trackId"])
                if tid in pos and pos[tid] is None:
                    pos[tid] = i
            top1 = res[0]["trackName"] if res else None
            row = {"type": "aso", "ts": ts, "country": country, "keyword": kw,
                   "returned": len(res), "top1": top1,
                   "pos_anicca": pos[str(TARGET)],
                   "pos_iam": pos[str(874656917)]}
            rows.append(row)
            print(f"{country} {kw!r}: Anicca={row['pos_anicca']} Iam={row['pos_iam']} n={len(res)} top1={top1}")
    with open(LEDGER, "a") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"appended {len(rows)} rows to ledger")

if __name__ == "__main__":
    main()
