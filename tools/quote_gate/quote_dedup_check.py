#!/usr/bin/env python3
"""名言重複除去ゲート (quote dedup gate) — 2026-11-10 恒常組み込み.

同一アカウントで同じ名言テキストを再投稿しないための機械チェック。
正本レジストリ: hidden_files/used-quotes-registry.json
（アカウントごとに使用済み quote を quote_id / 正規化テキストで保持する）

使い方:
  チェック（投稿前・必須）:
    python3 quote_dedup_check.py check --account aniccaffirmations \
        --platform youtube --quote "I am a magnet for success and good fortune."
    終了コード: 0=OK（未使用） / 2=完全一致の重複あり（投稿禁止・差し替え） /
                3=近接重複あり（Jaccard>=0.8。投稿禁止・差し替え）
  登録（公開URLが取れた直後・必須）:
    python3 quote_dedup_check.py register --account aniccaffirmations \
        --platform youtube --quote "..." --url https://... --date 2026-11-10
  進捗（一周管理）:
    python3 quote_dedup_check.py status --account aniccaffirmations

ルール:
  - プール（quote-canon の全件）が一周するまで、同一アカウントで同一 quote を再使用しない。
  - canon ファイルが存在する場合はその件数をプール総数とし、使用済み distinct 数が
    プール総数に達した時点で cycle が +1 され再使用可になる。
  - canon が無い間は「一周完了」を宣言できない（再使用は常時禁止）。
"""
import argparse, json, re, sys, unicodedata
from pathlib import Path

GOAL = Path.home() / "workspace/goals/anicca-revenue-growth-as-life-manager"
REGISTRY = GOAL / "hidden_files/used-quotes-registry.json"
CANON_CANDIDATES = [
    Path.home() / "workspace/anicca-ops/files/quote-canon/quotes.json",
    GOAL / "hidden_files/quote-canon/quotes.json",
]
NEAR_THRESHOLD = 0.8


def normalize(text: str) -> str:
    s = unicodedata.normalize("NFKC", text or "").lower()
    s = re.sub(r"[^\w\sぁ-んァ-ヶ一-龥]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def tokens(norm: str):
    return set(norm.split())


def load_registry():
    if REGISTRY.exists():
        return json.loads(REGISTRY.read_text(encoding="utf-8"))
    return {"version": 1, "accounts": {}}


def save_registry(reg):
    REGISTRY.write_text(json.dumps(reg, ensure_ascii=False, indent=1), encoding="utf-8")


def pool_size():
    for p in CANON_CANDIDATES:
        if p.exists():
            try:
                d = json.loads(p.read_text(encoding="utf-8"))
                if isinstance(d, list):
                    return len(d), str(p)
                if isinstance(d, dict):
                    for k in ("quotes", "items", "canon"):
                        if isinstance(d.get(k), list):
                            return len(d[k]), str(p)
            except Exception:
                pass
    return None, None


def account_entries(reg, account):
    return reg.get("accounts", {}).get(account, {"entries": []})["entries"]


def cmd_check(args):
    reg = load_registry()
    entries = account_entries(reg, args.account)
    nq = normalize(args.quote)
    if not nq:
        print("ERROR: quote が空です", file=sys.stderr)
        return 1
    for e in entries:
        if e["quote_norm"] == nq:
            print(f"DUPLICATE: account={args.account} は既にこの名言を使用済み "
                  f"(date={e.get('date')}, url={e.get('url')}, cycle={e.get('cycle', 1)})。"
                  f"投稿せず別の quote へ差し替えること。")
            return 2
    tq = tokens(nq)
    for e in entries:
        te = tokens(e["quote_norm"])
        if not tq or not te:
            continue
        j = len(tq & te) / len(tq | te)
        if j >= NEAR_THRESHOLD:
            print(f"NEAR-DUPLICATE: account={args.account} の使用済み名言と近接重複 "
                  f"(類似度 {j:.2f}, 既出: {e['quote_text']!r}, url={e.get('url')})。"
                  f"投稿せず別の quote へ差し替えること。")
            return 3
    ps, _ = pool_size()
    used = len({e["quote_norm"] for e in entries})
    cyc = entries[-1].get("cycle", 1) if entries else 1
    print(f"OK: account={args.account} 未使用 (使用済み distinct={used}"
          + (f"/プール{ps}" if ps else "/プール未確定(canon未構築)")
          + f", cycle={cyc})")
    return 0


def cmd_register(args):
    reg = load_registry()
    acct = reg.setdefault("accounts", {}).setdefault(args.account, {"entries": []})
    entries = acct["entries"]
    nq = normalize(args.quote)
    ps, _ = pool_size()
    used = {e["quote_norm"] for e in entries}
    cycle = entries[-1].get("cycle", 1) if entries else 1
    if nq in used:
        # 一周が完了している場合のみ新サイクルとして許可
        if ps and len(used) >= ps:
            cycle += 1
        elif not args.force:
            print(f"REFUSED: 既に使用済みです (account={args.account})。"
                  f"一周未完了のため再登録しません。--force は監査時のみ。")
            return 2
    entries.append({
        "quote_text": args.quote,
        "quote_norm": nq,
        "quote_id": args.quote_id,
        "platform": args.platform,
        "url": args.url,
        "date": args.date,
        "cycle": cycle,
    })
    save_registry(reg)
    print(f"REGISTERED: account={args.account} cycle={cycle} "
          f"distinct_used={len({e['quote_norm'] for e in entries})}")
    return 0


def cmd_status(args):
    reg = load_registry()
    entries = account_entries(reg, args.account)
    ps, src = pool_size()
    used = {e["quote_norm"] for e in entries}
    print(f"account={args.account} entries={len(entries)} distinct={len(used)} "
          f"pool={ps if ps else '未確定'} canon={src or 'なし'}")
    for e in entries:
        print(f"  [{e.get('date')}] cycle={e.get('cycle',1)} {e['quote_text'][:70]!r} {e.get('url') or ''}")
    return 0


def main():
    ap = argparse.ArgumentParser(description="quote dedup gate")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("check", "register"):
        p = sub.add_parser(name)
        p.add_argument("--account", required=True)
        p.add_argument("--platform", default="")
        p.add_argument("--quote", required=True)
        if name == "register":
            p.add_argument("--url", default="")
            p.add_argument("--date", default="")
            p.add_argument("--quote-id", default=None)
            p.add_argument("--force", action="store_true")
    p = sub.add_parser("status")
    p.add_argument("--account", required=True)
    args = ap.parse_args()
    return {"check": cmd_check, "register": cmd_register, "status": cmd_status}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
