#!/usr/bin/env python3
"""SNS per-post views collector (standing mechanism, added 2026-11-12).

For a date window, lists PUBLISHED posts via the Postiz CLI, reads each
post's official analytics (analytics:post), and appends one row per
(platform, account) to the measurement ledger:
  type=sns_post_views {window_start, window_end, read_at, platform,
                      account, posts_published, posts_measured,
                      views_total, likes_total, views_note}
Views are the platform's cumulative totals at read time for posts
published inside the window (Postiz returns lifetime-to-date totals).
Daily snapshots make window-exact deltas computable from the next
window onward. Platforms whose analytics come back empty (LinkedIn)
are recorded with posts_measured=0 and a note, never zero-filled views.
Usage: sns_post_views.py YYYY-MM-DD YYYY-MM-DD [--no-ledger]
"""
import json, subprocess, sys, collections, datetime, concurrent.futures, pathlib

LEDGER = pathlib.Path.home() / "workspace/goals/anicca-revenue-growth-as-life-manager/hidden_files/measurement-ledger.jsonl"
POSTIZ = str(pathlib.Path.home() / ".local/bin/postiz")

def run_cli(args, timeout=120):
    out = subprocess.run([POSTIZ]+args, capture_output=True, text=True, timeout=timeout)
    return out.stdout

def parse_json_array(text):
    i = text.find('[')
    if i < 0: return []
    d, _ = json.JSONDecoder().raw_decode(text[i:])
    return d

def post_views(post_id):
    try:
        out = run_cli(['analytics:post', post_id], timeout=60)
        arr = parse_json_array(out)
    except Exception:
        return None
    views = likes = None
    for block in arr:
        label = (block.get('label') or '').lower()
        data = block.get('data') or []
        if not data: continue
        total = data[-1].get('total')
        if label in ('views', 'impressions'): views = int(total)
        elif label == 'likes': likes = int(total)
    if views is None and likes is None: return None
    return (views or 0, likes or 0, views is not None)

def main():
    start, end = sys.argv[1], sys.argv[2]
    write_ledger = '--no-ledger' not in sys.argv
    ints = parse_json_array(run_cli(['integrations:list']))
    imap = {i['id']: (i.get('identifier'), i.get('profile') or i.get('name')) for i in ints}
    posts = parse_json_array(run_cli(['posts:list', '--startDate', f'{start}T00:00:00Z', '--endDate', f'{end}T23:59:59Z'], timeout=300))
    by_acct = collections.defaultdict(list)
    for p in posts:
        if p.get('state') != 'PUBLISHED': continue
        key = imap.get((p.get('integration') or {}).get('id'))
        if key: by_acct[key].append(p['id'])
    read_at = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat()
    rows = []
    for (platform, account), ids in sorted(by_acct.items()):
        got = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
            for res in ex.map(post_views, ids):
                if res: got.append(res)
        views = sum(g[0] for g in got if g[2])
        likes = sum(g[1] for g in got)
        measured = sum(1 for g in got if g[2])
        note = 'cumulative totals at read time (Postiz analytics:post)'
        if measured == 0:
            note = 'analytics returned empty for all posts on this platform (Postiz limitation); views not measurable via this route'
            views = None; likes = None
        row = {"type": "sns_post_views", "window_start": start, "window_end": end,
               "read_at": read_at, "platform": platform, "account": account,
               "posts_published": len(ids), "posts_measured": measured,
               "views_total": views, "likes_total": likes, "views_note": note}
        rows.append(row)
        print(json.dumps(row, ensure_ascii=False))
    if write_ledger:
        with open(LEDGER, 'a') as f:
            for r in rows: f.write(json.dumps(r, ensure_ascii=False) + '\n')
    pathlib.Path('/tmp/sns_post_views_result.json').write_text(json.dumps(rows, ensure_ascii=False, indent=1))

if __name__ == '__main__':
    main()
