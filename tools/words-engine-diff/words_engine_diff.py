#!/usr/bin/env python3
"""外の投稿文面とアプリ内カタログの重なりを実測する (same-engine 検証用)。
使い方: words_engine_diff.py <stock.md> <catalog_text_file...>
stock の「- 文面:」行からスライド文を取り出し、カタログ側テキストに含まれるか照合する。
"""
import re, sys, unicodedata

def norm(s):
    return unicodedata.normalize("NFKC", s).replace(" ", "").replace("　", "").strip("／/・")

stock = open(sys.argv[1], encoding="utf-8").read()
catalog = ""
for p in sys.argv[2:]:
    catalog += open(p, encoding="utf-8").read()
cat_n = norm(catalog)

phrases = []
for line in stock.splitlines():
    m = re.search(r"^- 文面: (.+)$", line)
    if not m:
        continue
    body = re.sub(r"表紙「[^」]*」", "", m.group(1))
    for seg in body.split("／"):
        seg = re.sub(r"^\d+\.\s*", "", seg.strip())
        if len(seg) >= 4:
            phrases.append(seg)

uniq = sorted(set(phrases))
hit = [p for p in uniq if norm(p) in cat_n]
print(f"投稿スライド文ユニーク数: {len(uniq)}")
print(f"アプリ内カタログに存在: {len(hit)} ({(len(hit)/len(uniq)*100 if uniq else 0):.1f}%)")
for p in hit[:10]:
    print("HIT:", p)
