#!/usr/bin/env python3
"""LinkedIn per-post metrics (daily, fail-honest).

Routes:
1. PUBLIC JSON-LD (ACTIVE for likes/comments/followers; verified 2026-11-16):
   A logged-out HTTPS GET of the post's public page
   (https://www.linkedin.com/feed/update/urn:li:share:<id>, browser UA, no
   cookies, no login) returns HTTP 200 with a schema.org JSON-LD
   SocialMediaPosting block carrying interactionStatistic LikeAction /
   CommentAction userInteractionCount, commentCount, and the author's
   FollowAction count (followers). Control-verified the same day against a
   known high-engagement post (Justin Welsh, activity 7228956267333967872):
   LikeAction 2192 / CommentAction 581 returned to a logged-out request, so
   the numbers are real, not guest-zeroed placeholders.
   The linkedin.com/posts/<slug> URL (found in the JSON-LD @id) serves the
   identical block. The /embed/feed/update/ URL returns 200 but contains no
   counts (verified 2026-11-16).
   IMPRESSIONS are NOT exposed on the public page (no view counter exists in
   the structured data): impressions are an author-only metric, officially
   available only via the Member Post Analytics API with the member's own
   OAuth token. impressions therefore stays null with an explicit status.

2. Postiz analytics (tried every run, currently structurally empty):
   Postiz Cloud's `linkedin` provider (PERSONAL profile) has no analytics
   code path at all (upstream: gitroomhq/postiz-app issue #1680), so
   `analytics:platform` / `analytics:post` return [] for every id form and
   date window. The `linkedin-page` provider DOES return analytics (verified
   live 2026-11-16), proving the gap is provider-specific. Kept in the loop
   so the day upstream ships memberCreatorPostAnalytics support, those
   numbers (including impressions) start flowing too.

3. Member Post Analytics API (not yet active): self-hosted Postiz + our own
   LinkedIn developer app approved for the Community Management API, then
   GET https://api.linkedin.com/rest/memberCreatorPostAnalytics
   (scope r_member_postAnalytics). Stub: fetch_linkedin_api().

Evidence: anicca-ops files/linkedin-genuine-bip-spec-2026-11-16.md and goal
hidden_files/linkedin-metrics-route-evidence-2026-11-16.md.

This script NEVER fabricates or estimates engagement numbers. A measured 0
is recorded as 0; an unobtainable metric stays null with an explicit status.

Usage:
  python3 linkedin_post_metrics.py [--date YYYY-MM-DD] [--dry-run]
Appends one row per LinkedIn post published/scheduled on the target JST date
to hidden_files/measurement-ledger.jsonl (type=social_linkedin,
granularity=post), plus one platform row (granularity=platform).
"""
import argparse
import datetime as dt
import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request

POSTIZ = "/home/hatch/.local/bin/postiz"
INTEGRATION_ID = "cmvv0yppi03iio91cax0bwmjx"  # linkedin, Daisuke Narita (personal)
PAGE_INTEGRATION_ID = "cmvv0yves03kkpa1cov0r8w6g"  # linkedin-page, EverFocus Labs
LEDGER = ("/home/hatch/workspace/goals/anicca-revenue-growth-as-life-manager/"
          "hidden_files/measurement-ledger.jsonl")
JST = dt.timezone(dt.timedelta(hours=9))
BROWSER_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
              "AppleWebKit/537.36 (KHTML, like Gecko) "
              "Chrome/131.0.0.0 Safari/537.36")
ROOT_CAUSE = ("provider_not_supported: Postiz Cloud 'linkedin' (personal profile) "
              "provider has no analytics code path (gitroomhq/postiz-app#1680); "
              "analytics returns [] for all id forms and date windows. "
              "Not zero engagement.")
IMPRESSIONS_STATUS = ("author_only: impressions are not exposed on LinkedIn's "
                      "public post page (no view counter in its structured "
                      "data, full JSON-LD parse verified 2026-11-16); "
                      "officially available only to the post author via the "
                      "Member Post Analytics API (member OAuth, "
                      "r_member_postAnalytics), not yet approved.")


def run_postiz(args, timeout=120):
    out = subprocess.run([POSTIZ] + args, capture_output=True, text=True,
                         timeout=timeout)
    return out.stdout or ""


def parse_json_payload(stdout):
    """Postiz CLI prints a header line, then JSON. Return parsed JSON or None."""
    lines = stdout.splitlines()
    for i, line in enumerate(lines):
        s = line.strip()
        if s.startswith("[") or s.startswith("{"):
            try:
                return json.loads("\n".join(lines[i:]))
            except json.JSONDecodeError:
                return None
    return None


def list_linkedin_posts():
    raw = run_postiz(["posts:list"], timeout=180)
    obj = parse_json_payload(raw)
    posts = obj.get("posts", []) if isinstance(obj, dict) else []
    return [p for p in posts
            if isinstance(p.get("integration"), dict)
            and p["integration"].get("id") == INTEGRATION_ID]


def analytics_post(post_id, days):
    raw = run_postiz(["analytics:post", post_id, "-d", str(days)], timeout=90)
    return parse_json_payload(raw)


def analytics_platform(integration_id, days):
    raw = run_postiz(["analytics:platform", integration_id, "-d", str(days)],
                     timeout=90)
    return parse_json_payload(raw)


def fetch_public_jsonld(url):
    """Logged-out GET of the public post page; parse schema.org JSON-LD.

    No cookies are sent or stored (fresh urllib opener per call), no login.
    Returns (data, status): data has likes/comments/followers/slug when the
    SocialMediaPosting block is present, else data is None and status says why.
    """
    if not url:
        return None, "no_url"
    req = urllib.request.Request(url, headers={
        "User-Agent": BROWSER_UA,
        "Accept-Language": "en-US,en;q=0.9",
    })
    try:
        with urllib.request.urlopen(req, timeout=40) as resp:
            status = resp.getcode()
            body = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return None, "http_%d" % e.code
    except Exception as e:  # network, timeout, redirect loop, ...
        return None, "error:%s" % type(e).__name__
    if status != 200:
        return None, "http_%d" % status
    for m in re.finditer(
            r'<script type="application/ld\+json">(.*?)</script>', body, re.S):
        try:
            d = json.loads(m.group(1))
        except json.JSONDecodeError:
            continue
        if not isinstance(d, dict) or d.get("@type") != "SocialMediaPosting":
            continue
        stats = {}
        for s in d.get("interactionStatistic") or []:
            itype = (s.get("interactionType") or "").rsplit("/", 1)[-1]
            if itype and isinstance(s.get("userInteractionCount"), int):
                stats[itype] = s["userInteractionCount"]
        followers = None
        author = d.get("author") or {}
        astat = author.get("interactionStatistic") or {}
        if isinstance(astat.get("userInteractionCount"), int):
            followers = astat["userInteractionCount"]
        likes = stats.get("LikeAction")
        comments = d.get("commentCount")
        if comments is None:
            comments = stats.get("CommentAction")
        if likes is None and comments is None:
            return None, "jsonld_found_but_no_counts"
        return {
            "likes": likes, "comments": comments, "followers": followers,
            "slug_url": d.get("@id"),
            "date_published": d.get("datePublished"),
        }, "ok"
    return None, "no_jsonld_block (authwall or layout change)"


def fetch_linkedin_api(post):
    """Self-host / memberCreatorPostAnalytics route. Not configured yet."""
    return None, "not_configured: own LinkedIn app + r_member_postAnalytics not yet approved"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=None, help="JST date YYYY-MM-DD (default: today JST)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    target = (dt.date.fromisoformat(args.date) if args.date
              else dt.datetime.now(JST).date())
    ts = dt.datetime.now(dt.timezone.utc).isoformat()

    platform_res = analytics_platform(INTEGRATION_ID, 30)
    page_res = analytics_platform(PAGE_INTEGRATION_ID, 30)
    page_ok = isinstance(page_res, list) and len(page_res) > 0

    posts = list_linkedin_posts()

    # Followers probe: public page of the most recent PUBLISHED post overall
    # (the author FollowAction count rides on every post page).
    followers = None
    followers_status = "unmeasured: no published post available as probe"
    published = [p for p in posts if p.get("state") == "PUBLISHED"
                 and p.get("releaseURL") and p.get("publishDate")]
    if published:
        latest = max(published, key=lambda p: p["publishDate"])
        probe, probe_status = fetch_public_jsonld(latest["releaseURL"])
        if probe and probe.get("followers") is not None:
            followers = probe["followers"]
            followers_status = ("measured_public_jsonld: author FollowAction "
                                "count on public post page %s"
                                % latest["releaseURL"])
        else:
            followers_status = "unmeasured: public probe %s -> %s" % (
                latest["releaseURL"], probe_status)

    rows = []
    rows.append({
        "type": "social_linkedin", "granularity": "platform", "ts": ts,
        "date_jst": target.isoformat(), "account": "LinkedIn Daisuke Narita",
        "followers": followers,
        "followers_status": followers_status,
        "route_tested": ("postiz analytics:platform %s -d 30 -> %s; "
                         "contrast check analytics:platform %s (linkedin-page) -d 30 -> %s; "
                         "public followers probe -> %s"
                         % (INTEGRATION_ID,
                            "[]" if platform_res == [] else platform_res,
                            PAGE_INTEGRATION_ID,
                            "non-empty series (provider code path exists)" if page_ok else page_res,
                            followers_status)),
        "note": ("Postiz personal-profile analytics route does not exist "
                 "(#1680); likes/comments/followers are measured via the "
                 "public JSON-LD route instead. Impressions remain "
                 "author-only (see per-post impressions_status)."),
    })

    todays = []
    for p in posts:
        pub = p.get("publishDate")
        if not pub:
            continue
        pub_jst = dt.datetime.fromisoformat(pub.replace("Z", "+00:00")).astimezone(JST)
        if pub_jst.date() == target:
            todays.append((pub_jst, p))
    todays.sort(key=lambda item: item[0])

    measured_posts = 0
    for pub_jst, p in todays:
        res7 = analytics_post(p["id"], 7)
        res30 = analytics_post(p["id"], 30)
        api_res, api_status = fetch_linkedin_api(p)
        postiz_measured = None
        if isinstance(res30, list) and res30:
            postiz_measured = res30

        likes = comments = None
        metrics_status = ROOT_CAUSE
        public_note = "not_attempted"
        if p.get("state") == "PUBLISHED":
            time.sleep(1)
            pub_data, pub_status = fetch_public_jsonld(p.get("releaseURL"))
            if pub_data:
                likes = pub_data.get("likes")
                comments = pub_data.get("comments")
                metrics_status = (
                    "measured_public_jsonld: logged-out GET of the public "
                    "post page; schema.org SocialMediaPosting "
                    "interactionStatistic (LikeAction/CommentAction). "
                    "Control-verified 2026-11-16 against Justin Welsh post "
                    "activity 7228956267333967872 (likes 2192 / comments 581 "
                    "returned logged-out), so values are real, not "
                    "guest-zeroed.")
                public_note = "ok slug=%s" % pub_data.get("slug_url")
                measured_posts += 1
            else:
                public_note = pub_status
                metrics_status = ("unmeasured: public route failed (%s); "
                                  "postiz: %s" % (pub_status, ROOT_CAUSE))
        if postiz_measured:
            metrics_status = "measured_postiz: %s" % (postiz_measured,)

        rows.append({
            "type": "social_linkedin", "granularity": "post", "ts": ts,
            "date_jst": target.isoformat(), "account": "LinkedIn Daisuke Narita",
            "postiz_id": p["id"], "state": p.get("state"),
            "slot_jst": pub_jst.strftime("%H:%M"),
            "url": p.get("releaseURL"), "release_id": p.get("releaseId"),
            "impressions": None, "impressions_status": IMPRESSIONS_STATUS,
            "likes": likes, "comments": comments,
            "metrics_status": metrics_status if p.get("state") == "PUBLISHED" else "not_published",
            "route_tested": ("public_jsonld: %s; postiz analytics:post %s -d 7 -> %s; "
                             "-d 30 -> %s; linkedin_api: %s"
                             % (public_note, p["id"], res7, res30, api_status)),
            "source": "linkedin_post_metrics.py: public post page JSON-LD (logged-out) + Postiz posts:list/analytics",
        })

    for r in rows:
        line = json.dumps(r, ensure_ascii=False)
        if args.dry_run:
            print(line)
        else:
            with open(LEDGER, "a") as f:
                f.write(line + "\n")
    print("rows_written=%d posts_today=%d posts_measured_public=%d followers=%s "
          "platform_empty=%s page_route_ok=%s"
          % (len(rows), len(todays), measured_posts, followers,
             platform_res == [], page_ok))
    return 0


if __name__ == "__main__":
    sys.exit(main())
