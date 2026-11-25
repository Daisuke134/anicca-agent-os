#!/usr/bin/env python3
"""Bing SERP position check (scriptable from VM, no API key).
Bing is NOT Google: positions are Bing's index. It is the always-available
scripted SERP route; Google positions are snapshotted separately via the
agent search tool, and own-site Google truth comes from Search Console.
Records positions of target domains per keyword into the shared ledger.
"""
import json, re, urllib.parse, urllib.request, datetime, os, html as h

KEYWORDS = ["best affirmation apps", "best affirmation apps for iPhone",
            "affirmation app", "best daily affirmation apps",
            "daily affirmations", "best meditation affirmation app",
            "what is the best affirmation app"]
DOMAINS = ["aniccaai.com", "thevisionboard.app", "happierhuman.com"]
LEDGER = os.path.expanduser("~/workspace/goals/anicca-revenue-growth-as-life-manager/hidden_files/measurement-ledger.jsonl")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"}

def fetch(kw):
    q = urllib.parse.urlencode({"q": kw, "count": 30})
    req = urllib.request.Request("https://www.bing.com/search?" + q, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "ignore")

def positions(page):
    blocks = re.findall(r'<li class="b_algo".*?</li>', page, re.S)
    skip = ("bing.com", "microsoft.com", "msn.com", "live.com", "windows.com")
    urls = []
    for b in blocks:
        for u in re.findall(r'href="(https?://[^"]+)"', b):
            u = h.unescape(u)
            host = re.sub(r"^https?://", "", u).split("/")[0]
            if "bing.com/ck/a" in u:
                # Bing redirect: real URL is base64url in the u= param (a1-prefixed)
                m2 = re.search(r"[?&]u=a1([^&]+)", u)
                if m2:
                    import base64
                    try:
                        pad = "=" * (-len(m2.group(1)) % 4)
                        urls.append(base64.urlsafe_b64decode(m2.group(1) + pad).decode("utf-8", "ignore"))
                        break
                    except Exception:
                        pass
                continue
            if not any(s in host for s in skip):
                urls.append(u)
                break
    pos = {}
    for d in DOMAINS:
        pos[d] = next((i for i, u in enumerate(urls, 1) if d in u), None)
    return urls, pos

def main():
    ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
    rows = []
    for kw in KEYWORDS:
        try:
            urls, pos = positions(fetch(kw))
            row = {"type": "seo_bing", "ts": ts, "keyword": kw,
                   "top3": urls[:3], "positions": pos}
            print(kw, "->", pos, "| top1:", urls[0] if urls else None)
        except Exception as e:
            row = {"type": "seo_bing", "ts": ts, "keyword": kw, "error": str(e)}
            print(kw, "ERROR", e)
        rows.append(row)
    with open(LEDGER, "a") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"appended {len(rows)} rows")

if __name__ == "__main__":
    main()
