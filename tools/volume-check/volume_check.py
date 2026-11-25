#!/usr/bin/env python3
"""volume-check: judge a distribution-volume state description against
winner operating numbers and honest counting units. Stdlib only, offline.

Primary sources (read in full 2026-11-14):
 - Ernesto Lopez (@ErnestoSOFTWARE) 2026-11-12 post, full text read via
   fxtwittergo: Prayer Lock at $150k/mo ran ~6,000 videos/month =
   200 videos/day, consistently, high quality, dozens of new formats/month;
   app was #6 on the App Store. Four principles: Consistency, Volume,
   Quality, Iteration. https://x.com/ErnestoSOFTWARE/status/2120993812671586389
 - Ernesto Lopez 2026-11-12 post: a repurposing prompt got their app an
   extra 20M views/mo repurposing content. The prompt itself is inside an
   image; its text was NOT read, so no prompt content is claimed here.
   https://x.com/ErnestoSOFTWARE/status/2120769857683693903
 - Ghostfeed, "How to Scale AI UGC Without Making 500 Videos of Garbage":
   one concept -> executions -> hook variants -> platform cuts ->
   deployments must be counted separately; a platform cut is not a new
   creative; sane ramp Stage 1 = 10 approved assets/week, Stage 2 =
   10/day, Stage 3 = 30/day. https://ghostfeed.ai/blog/scale-ai-ugc-production
 - Company floor (standing rule): >=3 posts/day/account, winner slot
   times; a stopped day is a system failure, not an event.
Counting rule: winner comparison is always as-is vs winner, per day,
never cumulative totals.
"""
import json, sys
fails=[]; warns=[]
def fail(g,m): fails.append(f"[{g}] {m}")
def warn(g,m): warns.append(f"[{g}] {m}")
def main(path):
    s=json.load(open(path))
    # CV-0 record: the four units must be recorded separately
    if not s.get("recorded"): fail("CV-0","state not recorded (unmeasured)")
    u=s.get("units") or {}
    for k in ("concepts","variants","deployments"):
        if u.get(k) is None: fail("CV-0",f"units.{k} unrecorded (unmeasured; deployments alone inflate volume)")
    if u.get("concepts") is not None and u.get("deployments") is not None:
        if u.get("concepts")==0 and u.get("deployments")>0:
            fail("CV-0","deployments > 0 with 0 concepts: cross-posting counted as creation")
    # CV-1 daily volume vs winner and vs floor
    d=s.get("daily") or {}
    dep=d.get("deployments_per_day")
    if dep is None: fail("CV-1","deployments_per_day unmeasured")
    else:
        if dep < 3: fail("CV-1",f"{dep}/day below company floor 3/day/account")
        w=d.get("winner_deployments_per_day")
        if w is None: fail("CV-1","winner daily volume unrecorded (as-is must be shown vs winner)")
        elif dep < w: warn("CV-1",f"as-is {dep}/day vs winner {w}/day (gap {w-dep}/day) - report the gap, not the total")
    # CV-2 distinct concepts per week (iteration fuel)
    cw=d.get("new_concepts_per_week")
    if cw is None: fail("CV-2","new_concepts_per_week unmeasured (winner: dozens of new formats/month)")
    elif cw < 3: fail("CV-2",f"only {cw} new concepts/week: iteration starves (winner makes dozens of new formats/month)")
    # CV-3 repurposing: winners are repurposed, not only net-new
    r=s.get("repurposing") or {}
    if r.get("winner_content_repurposed") is not True:
        fail("CV-3","winning posts are not repurposed (winner: repurposing prompt = +20M views/mo, Ernesto 2026-11-12)")
    if r.get("repurpose_keeps_winner_template_measured") is not True:
        fail("CV-3","repurposing without a measured template (cuts/beats/text) is a rewrite, not a copy; use a template extractor (vtpl) or manual frame measurement")
    # CV-4 quality gate before volume (Ghostfeed: approval before expensive step)
    q=s.get("quality") or {}
    if q.get("copy_diff_counted_before_publish") is not True:
        fail("CV-4","volume shipped without counting copy differences vs the winner original before publish (100% copy gate)")
    if q.get("approved_assets_counted_separately") is not True:
        fail("CV-4","approved assets not counted separately from produced files (Ghostfeed bottleneck rule)")
    # CV-5 consistency: no zero days
    if d.get("zero_days_last_7") is None: fail("CV-5","zero days in last 7 unmeasured")
    elif d.get("zero_days_last_7")>0: fail("CV-5",f"{d['zero_days_last_7']} zero day(s) in last 7: a stopped surface is a system failure")
    # CV-6 paid volume is forbidden
    if s.get("paid_creators_or_ads_required") is True:
        fail("CV-6","plan requires paid creators/ads: paid growth is not considered; close the math on free organic capacity")
    for w_ in warns: print("WARN",w_)
    for f in fails: print("FAIL",f)
    print(f"RESULT {'PASS' if not fails else 'FAIL'} fails={len(fails)} warns={len(warns)}")
    return 0 if not fails else 1
if __name__=="__main__": sys.exit(main(sys.argv[1]))
