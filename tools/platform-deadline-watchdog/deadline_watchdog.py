#!/usr/bin/env python3
"""Platform Deadline Watchdog.

Scans Gmail platform notifications and extracts deadline-bearing items that
need an action from us (accept an order, send a contract request, respond to a
termination request, submit an evaluation, watch an escrow, ...), computes the
deadline from the platform rule table, cross-references closing events, and
prints a Markdown table + writes a JSON audit file.

Design notes
- Read-only: never sends, accepts, or clicks anything.
- Rules live in RULES below and mirror skills/platform-deadline-guard/SKILL.md.
  Deadlines tagged basis="rule" are computed from the notification date;
  basis="explicit" dates are read from the message text when present.
- An item whose resolution cannot be proven from mail is reported as
  "要確認" (needs the platform lane to check), never silently dropped.

Usage:
  deadline_watchdog.py [--days 30] [--now 2026-11-17T14:40:00+09:00]
                       [--out-md PATH] [--out-json PATH]
"""
import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone

GWS = "/opt/hatch/bin/hatch_gws_cli"
JST = timezone(timedelta(hours=9))

# ---------------------------------------------------------------- rules ----
# event: (regex over subject+snippet, kind, deadline_days, action, lane)
# kind: open = starts a deadline item; close = resolves an item;
#       info = no action deadline (monitor only)
RULES = {
    "Lancers": [
        (r"自動キャンセル", "close", None, "終了として台帳を閉じる", "-"),
        (r"仕事依頼がキャンセル|キャンセルされました", "close", None, "依頼ページで理由を確認し台帳を閉じる", "応募レーン"),
        (r"選定が終了", "close", None, "不採用は終了として記録のみ", "-"),
        (r"仮払い.*(完了|されました|行われました)", "close", None, "作業開始。契約の完了予定日を納期として台帳へ", "ランサーズ専用"),
        (r"承諾依頼", "open", 7, "承諾ページで発注内容を確認し、その場で承諾する（7日で発注キャンセル）", "ランサーズ専用/高速返信"),
        (r"承諾.*(督促|お願い)|選択されてから", "open", 7, "承諾を即実行する（督促＝期限接近）", "ランサーズ専用/高速返信"),
        (r"仮払いを待っています|仮払い待ち", "info", None, "クライアント仮払い待ち。発生を次回スキャンで確認", "ランサーズ専用"),
        (r"評価", "info", None, "相手の評価着地（情報）。自社の評価タスクは「やること」リスト側で台帳管理（メールでは検出できない）", "ランサーズ専用"),
        (r"連絡催促", "open", 7, "7日以内に必ず返信する（公式FAQ）", "高速返信"),
    ],
    "CrowdWorks": [
        (r"条件.*合意|提案条件", "open", 14, "契約リクエストを即送信する（合意から14日で自動キャンセル）", "CrowdWorks専用"),
        (r"契約リクエスト", "open", 14, "内容を確認し「契約する」で同意する", "CrowdWorks専用"),
        (r"契約途中終了リクエスト", "open", 7, "1週間以内に同意/拒否を処理する（無対応は評価に明記される）", "契約レーン"),
        (r"仮払い.*(完了|しました)", "info", 180, "作業開始。仮払いは180日で失効するため長期化したら再仮払いを確認", "CrowdWorks専用"),
        (r"条件変更リクエスト", "open", None, "条件を確認し同意/再提示を即返信する", "CrowdWorks専用"),
        (r"キャンセル", "close", None, "終了として台帳を閉じる", "-"),
    ],
    "Coconala": [
        (r"キャンセルとなりました", "close", None, "合意キャンセル等で終了。台帳を閉じる", "-"),
        (r"評価.*お願いします|評価入力をお願い", "open", None, "件名・本文の評価期限までに取引評価を入力する", "ココナラ専用"),
        (r"購入されました|購入がありました", "open", None, "トークルームで即応答し着手する", "ココナラ専用"),
        (r"キャンセルリクエスト|キャンセル申請", "open", None, "トークルームで即応答する（応答期限は未確認のため即時）", "ココナラ専用"),
        (r"見積もり|提案.*(受付|届き)", "info", None, "選定待ち。追加質問には即返信", "ココナラ専用"),
        (r"評価が届きました|評価を完了しました", "info", None, "相手の評価着地。自社の評価入力は別通知（評価入力のお願い）で追う", "ココナラ専用"),
        (r"募集が終了しました", "close", None, "募集終了。台帳を閉じる", "-"),
        (r"取引.*完了|完了しました", "close", None, "終了として台帳を閉じる", "-"),
    ],
    "Mercor": [
        (r"assessment|interview|availability", "open", None, "メール記載の期限までに完了する（期限はメール本文が正）", "Mercorレーン"),
    ],
    "Upwork": [
        (r"offer", "open", None, "オファー内容を確認し開始日前に承諾する", "海外受託"),
        (r"milestone.*(funded|activated)|funded.*milestone", "info", 14, "作業開始。納品後クライアント検収14日で自動リリース", "海外受託"),
        (r"contract.*(ended|terminated)|ended.*contract", "close", None, "終了として台帳を閉じる", "-"),
    ],
    "Freelancer": [
        (r"awarded|award", "open", None, "アワードを承諾しマイルストーン作成を確認する", "海外受託"),
        (r"milestone.*(created|released)", "info", None, "作成=作業開始、リリース=入金確定として記録", "海外受託"),
    ],
    "Fiverr": [
        (r"custom offer", "open", None, "オファー有効期限内に見込み客へフォローする", "海外受託"),
        (r"new order|order.*started", "info", None, "注文開始。納期（注文ページが正）までに納品", "海外受託"),
        (r"delivered|auto.*complete", "info", 3, "納品済み。買い手レビュー3日で自動完了（情報）", "海外受託"),
    ],
    "Workana": [
        (r"garant|escrow|pago|deposit", "info", None, "保証金入金を確認してから着手", "海外受託"),
        (r"proposal.*(accepted|aceptada)|hired", "open", None, "契約内容を確認し着手する", "海外受託"),
    ],
    "PeoplePerHour": [
        (r"invoice|payment request", "info", None, "入金状況を台帳で追う", "海外受託"),
        (r"proposal.*(accepted)|stream", "open", None, "WorkStreamで即応答する", "海外受託"),
    ],
    "Guru": [
        (r"safepay|funded", "info", None, "SafePay入金を確認してから着手", "海外受託"),
        (r"invoice", "info", None, "入金状況を台帳で追う", "海外受託"),
    ],
    "Contra": [
        (r"contract|proposal", "open", None, "契約内容を確認し即応答する", "海外受託"),
        (r"payment", "info", None, "入金確定として記録", "海外受託"),
    ],
    "Twine": [
        (r"pitch|brief|booked", "open", None, "内容を確認し即応答する", "海外受託"),
    ],
}

PLATFORM_DOMAINS = {
    "Lancers": "lancers.co.jp",
    "CrowdWorks": "crowdworks.jp",
    "Coconala": "coconala.com",
    "Mercor": "mercor.com",
    "Upwork": "upwork.com",
    "Freelancer": "freelancer.com",
    "Fiverr": "fiverr.com",
    "Workana": "workana.com",
    "PeoplePerHour": "peopleperhour.com",
    "Guru": "guru.com",
    "Contra": "contra.com",
    "Twine": "twine.net",
}

JP_QUERIES = [
    # high-severity pass first: acceptance requests are low-volume and must
    # never be cut off by the --max cap on the noisier queries below
    "from:(lancers.co.jp) subject:(承諾依頼 OR 発注承諾) newer_than:{days}d",
    "from:(lancers.co.jp) subject:(承諾 OR 仮払い OR キャンセル OR 選定 OR 評価 OR 完了 OR 督促) newer_than:{days}d",
    "from:(crowdworks.jp) subject:(契約 OR 仮払い OR 条件 OR 途中終了 OR 納品 OR キャンセル OR 同意) newer_than:{days}d",
    "from:(coconala.com) subject:(購入 OR キャンセル OR 評価 OR トークルーム OR 見積もり OR 完了 OR 終了) newer_than:{days}d",
]
EN_QUERY = (
    "from:(upwork.com OR freelancer.com OR fiverr.com OR mercor.com OR workana.com "
    "OR peopleperhour.com OR guru.com OR contra.com OR twine.net) newer_than:{days}d"
)

ID_PATTERNS = [
    r"work/detail/(\d+)",
    r"project_feature/(\d+)",
    r"project/approval/start/(\d+)",
    r"proposal_conditions/(\d+)",
    r"トークルームNo[:： ]*(\d+)",
    r"投稿No\.(\d+)",
    r"contract[/_](\d{6,})",
    r"\b(\d{8})\b",
    r"\b(\d{7})\b",
]
TITLE_PATTERN = re.compile(r"「([^」]{4,80})」")
EXPLICIT_DEADLINE = re.compile(r"(?:期限|締切)[：: ]*(\d{4})/(\d{1,2})/(\d{1,2})")


def gmail_search(query, max_results):
    cmd = [GWS, "gmail", "+triage", "--query", query, "--max", str(max_results),
           "--format", "json"]
    out = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    text = out.stdout.strip()
    if not text.startswith("{"):
        return [], f"no JSON output: {text[:200]} / stderr: {out.stderr[:200]}"
    data = json.loads(text)
    return data.get("messages", []), None


def platform_of(msg):
    frm = msg.get("from", "").lower()
    for name, domain in PLATFORM_DOMAINS.items():
        if domain in frm:
            return name
    return None


def extract_title(msg):
    m = TITLE_PATTERN.search(msg.get("snippet") or "")
    if m:
        return re.sub(r"\s+", "", m.group(1))[:40]
    return None


def extract_key(msg):
    text = (msg.get("subject") or "") + " " + (msg.get("snippet") or "")
    for pat in ID_PATTERNS:
        m = re.search(pat, text)
        if m:
            return "id:" + m.group(1)
    t = extract_title(msg)
    if t:
        return "title:" + t
    return "subject:" + (msg.get("subject") or "")[:40]


def extract_explicit_deadline(msg):
    text = (msg.get("subject") or "") + " " + (msg.get("snippet") or "")
    m = EXPLICIT_DEADLINE.search(text)
    if not m:
        return None
    y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
    return datetime(y, mo, d, 23, 59, tzinfo=JST)


def parse_dt(msg):
    raw = (msg.get("message_sent_at") or {}).get("user_local")
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        return None


def classify(platform, msg):
    text = (msg.get("subject") or "") + " " + (msg.get("snippet") or "")
    hits = []
    for pattern, kind, days, action, lane in RULES.get(platform, []):
        if re.search(pattern, text, flags=re.IGNORECASE):
            hits.append({"pattern": pattern, "kind": kind, "days": days,
                         "action": action, "lane": lane})
    return hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--now", default=None)
    ap.add_argument("--max", type=int, default=100)
    ap.add_argument("--out-md", default=None)
    ap.add_argument("--out-json", default=None)
    args = ap.parse_args()

    now = datetime.fromisoformat(args.now) if args.now else datetime.now(JST)

    messages, errors = [], []
    for tmpl in JP_QUERIES + [EN_QUERY]:
        msgs, err = gmail_search(tmpl.format(days=args.days), args.max)
        if err:
            errors.append(err)
        messages.extend(msgs)
    # dedupe messages returned by overlapping queries
    uniq = {}
    for m in messages:
        uniq[m.get("id")] = m
    messages = list(uniq.values())

    events = []
    for msg in messages:
        platform = platform_of(msg)
        if not platform:
            continue
        dt = parse_dt(msg)
        hits = classify(platform, msg)
        if not hits:
            continue
        hit = hits[0]  # rules are ordered: first match wins per message
        key = extract_key(msg)
        if "評価" in hit["pattern"] or "評価" in (msg.get("subject") or "") and hit["kind"] == "open":
            key += ":eval"
        events.append({
            "platform": platform,
            "key": key,
            "title": extract_title(msg),
            "kind": hit["kind"],
            "days": hit["days"],
            "action": hit["action"],
            "lane": hit["lane"],
            "pattern": hit["pattern"],
            "subject": msg.get("subject"),
            "at": dt.isoformat() if dt else None,
            "explicit_deadline": (extract_explicit_deadline(msg).isoformat()
                                  if extract_explicit_deadline(msg) else None),
            "id": msg.get("id"),
        })
    events.sort(key=lambda e: e["at"] or "")

    # group into items: an open event is resolved by a later close event on
    # the same platform whose key matches OR whose title matches.
    def matches(close, open_):
        if close["platform"] != open_["platform"]:
            return False
        if close["key"] == open_["key"]:
            return True
        return bool(close["title"] and open_["title"]
                    and close["title"] == open_["title"])

    closes = [e for e in events if e["kind"] == "close"]
    items = []
    for e in events:
        if e["kind"] == "close":
            continue
        later_close = [c for c in closes
                       if matches(c, e) and (c["at"] or "") >= (e["at"] or "")]
        resolved = bool(later_close)
        deadline, remaining_h, status = None, None, None
        dl = None
        if e["explicit_deadline"]:
            dl = datetime.fromisoformat(e["explicit_deadline"])
        elif e["days"] and e["at"]:
            dl = datetime.fromisoformat(e["at"]) + timedelta(days=e["days"])
        if dl is not None:
            deadline = dl.isoformat()
            remaining_h = round((dl - now).total_seconds() / 3600, 1)
        if resolved:
            status = "処理済み（解消イベントあり）"
        elif e["kind"] == "info":
            status = "監視（期限アクションなし）"
        elif deadline is None:
            status = "要確認（期限はプラットフォームで確認）"
        elif remaining_h < 0:
            status = "期限切れ・未処理の疑い"
        elif remaining_h <= 48:
            status = "期限間近・未処理"
        else:
            status = "未処理（期限内）"
        items.append({**e, "deadline": deadline, "remaining_hours": remaining_h,
                      "status": status,
                      "resolved_by": later_close[0]["subject"] if later_close else None})

    # closing events with no open in window are listed as closed items
    for c in closes:
        items.append({**c, "deadline": None, "remaining_hours": None,
                      "status": "終了（クローズ通知）", "resolved_by": None})

    # dedupe identical opens (same platform/key/pattern keep EARLIEST:
    # the deadline runs from the first notice)
    seen = {}
    for it in items:
        k = (it["platform"], it["key"], it["pattern"], it["kind"])
        if k not in seen or (it["at"] or "") < (seen[k]["at"] or ""):
            seen[k] = it
    items = list(seen.values())

    order = {"期限切れ・未処理の疑い": 0, "期限間近・未処理": 1,
             "要確認（期限はプラットフォームで確認）": 2, "未処理（期限内）": 3,
             "監視（期限アクションなし）": 4, "処理済み（解消イベントあり）": 5,
             "終了（クローズ通知）": 6}
    items.sort(key=lambda x: (order.get(x["status"], 9), x["at"] or ""))

    lines = [f"# Platform Deadline Watchdog — scan {now.isoformat()} (window {args.days}d)",
             "",
             f"matched events: {len(events)} / items: {len(items)}",
             ""]
    if errors:
        lines.append(f"SEARCH ERRORS: {errors}")
        lines.append("")
    lines.append("| 状態 | プラットフォーム | アイテム | イベント | 通知日時 | 期限（推定含む） | 残り | 担当 | 次アクション |")
    lines.append("|---|---|---|---|---|---|---|---|---|")
    for it in items:
        rem = "" if it["remaining_hours"] is None else f"{it['remaining_hours']}h"
        lines.append("| {status} | {platform} | {key} | {subject} | {at} | {deadline} | {rem} | {lane} | {action} |".format(
            status=it["status"], platform=it["platform"], key=it["key"],
            subject=(it["subject"] or "")[:60], at=(it["at"] or "")[:16],
            deadline=(it["deadline"] or "—")[:16], rem=rem,
            lane=it["lane"], action=it["action"]))
    report = "\n".join(lines) + "\n"

    if args.out_md:
        with open(args.out_md, "w") as f:
            f.write(report)
    if args.out_json:
        with open(args.out_json, "w") as f:
            json.dump({"scanned_at": now.isoformat(), "errors": errors,
                       "events": events, "items": items}, f, ensure_ascii=False, indent=1)
    print(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
