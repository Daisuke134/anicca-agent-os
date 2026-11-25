#!/usr/bin/env python3
"""retention-check: deterministic gate for short-video retention + shareability.
Stdlib only, offline, free. Sources (full-read via fxtwittergo 2026-11-15):
- Ernesto Lopez, X Article "The Anatomy of a Viral Video"
  https://x.com/ErnestoSOFTWARE/status/2119100195078090956
  (article https://x.com/i/article/2118816004969058304)
  Retention graph is the biggest virality indicator. Viral: >75% still
  watching after 3s, >=50% after half the video. Bad example: 35% at 0:04,
  1k views. Modern story arc: story starts at 70/100 tension in the first
  second, first 5s are the hook, spike to 90 within 5-10s (first dopamine
  hit: shocking stat / something goes wrong), then drop and spike again
  until the end; every spike is a new hook; beats are joined with "but" /
  "therefore", never "and then" (that is where people swipe). Shareability:
  explicitly ask people to share ("send this to that one friend that does
  X"); in his telling of X's open-sourced ranking, shares weigh 20 points
  vs 5 for comments/likes/saves, and IG's head names sends a top-3 signal,
  stronger for non-followers. Tracked 7,600+ of his own UGC videos; every
  viral one shares these three: modern story arc, extremely shareable,
  dopamine hit after dopamine hit.
- Mau Baron, X Article "How we ran a UGC army to $150k/month with 0
  employees" https://x.com/maubaron/status/2118738294452150361
  (article https://x.com/i/article/2118734538671038464)
  Daily diagnosis by bucket: <1k views on a previously-viral creator =
  hook problem; 1k-10k = retention problem (script + delivery);
  100k+ views with no downloads = conversion problem (where the app
  appears, what comments look like). Views and downloads are read side
  by side every day; a 2M-view day with flat downloads is a conversion
  problem, not a win. Converting format: app in first 15s, demo/screenshot
  in the video, app name in caption, comments full of "what's the app"
  (seed those yourself if you have to).
Exit 0 = PASS, 1 = FAIL. Warnings do not fail.
Input JSON: {app,
 inventory:{recorded, videos_tracked, retention_graph_read_per_video},
 retention:{measured, median_retention_3s_pct, median_retention_half_pct},
 story:{starts_at_high_tension, hook_first_3s, first_peak_within_10s,
   beats_but_therefore, and_then_chain, spikes_throughout},
 share:{explicit_share_ask, share_ask_names_specific_person,
   what_app_comment_seeded},
 diagnosis:{bucket_diagnosis_used, views_and_downloads_side_by_side_daily},
 measurement:{retention_joined_to_downloads, per_format}}
"""
import json, sys

def check(d):
    fails, warns = [], []
    inv = d.get("inventory") or {}
    if not inv.get("recorded"):
        fails.append("RT-0 distribution videos are not inventoried for retention (no record of which videos exist with their retention graphs; Ernesto: make a habit of checking every video's retention graph -- an unrecorded graph cannot be improved)")
    if not inv.get("retention_graph_read_per_video"):
        fails.append("RT-0 the retention graph is not read per video (judging by total views alone; Ernesto: the retention graph is the biggest indicator of a video going viral or not)")
    rt = d.get("retention") or {}
    if not rt.get("measured"):
        fails.append("RT-1 retention is not measured at the winner's two checkpoints (3s and half-video; without both numbers there is no way to tell a hook failure from a story failure)")
    else:
        r3 = rt.get("median_retention_3s_pct")
        rh = rt.get("median_retention_half_pct")
        if r3 is None or rh is None:
            fails.append("RT-1 retention is claimed measured but one of the two checkpoint values (3s / half) is missing; the missing value is the ground truth")
        else:
            if r3 <= 75:
                fails.append(f"RT-1 median retention at 3s is {r3}% -- at or below the winner's viral threshold of >75% (Ernesto's bad example was 35% at 0:04 and got 1k views; the first 3 seconds / hook are the failing layer)")
            if rh < 50:
                fails.append(f"RT-1 median retention at half the video is {rh}% -- below the winner's >=50% floor (the story arc, not the hook, is the failing layer)")
    st = d.get("story") or {}
    if not st.get("starts_at_high_tension"):
        fails.append("RT-2 stories do not start at high tension (Ernesto's modern arc starts at 70/100 in the first second; the school rising-action model that starts low is where Gen-Z viewers swipe)")
    if not st.get("hook_first_3s"):
        fails.append("RT-2 there is no hook in the first 3 seconds (the first 5 seconds are the hook in the winner's arc; people must know what is going on right away)")
    if not st.get("first_peak_within_10s"):
        fails.append("RT-2 there is no first peak / dopamine hit within 5-10 seconds (shocking stat or something going wrong; without the first spike the graph never reaches the viral shape)")
    if not st.get("beats_but_therefore"):
        fails.append("RT-2 beats are not joined with 'but' / 'therefore' (Ernesto: every spike is a new hook made by putting but/therefore between beats)")
    if st.get("and_then_chain"):
        fails.append("RT-2 scripts use an 'and then' chain (Ernesto: most people write 'and then' -- and that is exactly where people swipe)")
    if not st.get("spikes_throughout"):
        fails.append("RT-2 there are no repeated spikes until the end (one hook and then a flat line is the bad retention graph: flat after 0:04, 1k views)")
    sh = d.get("share") or {}
    if not sh.get("explicit_share_ask"):
        fails.append("RT-3 videos never explicitly ask for a share (Ernesto: the same way YouTubers ask for follows, ask people to share -- shares are, in his telling of X's open ranking, 20 points vs 5 for likes/comments/saves, and IG sends are a top-3 signal, stronger for non-followers)")
    if sh.get("explicit_share_ask") and not sh.get("share_ask_names_specific_person"):
        fails.append("RT-3 the share ask does not name a specific person ('send this to that one friend that does X'; a generic 'share this' does not give the viewer a recipient in mind)")
    if not sh.get("what_app_comment_seeded"):
        warns.append("RT-3 'what's the app' comments are not seeded (Mau: a converting format's comment section is full of them -- seed those yourself if you have to; warning only)")
    dg = d.get("diagnosis") or {}
    if not dg.get("bucket_diagnosis_used"):
        fails.append("RT-4 failures are not diagnosed by Mau's buckets (<1k = hook, 1k-10k = retention/script, 100k+ with no downloads = conversion; every bad week falls in one of the three, and the fix differs by bucket)")
    if not dg.get("views_and_downloads_side_by_side_daily"):
        fails.append("RT-4 views and downloads are not read side by side daily (Mau: a 2M-view day with a flat download line is not a win, it is a conversion problem -- caught a week late if read separately)")
    ms = d.get("measurement") or {}
    if not ms.get("retention_joined_to_downloads"):
        fails.append("RT-5 retention cannot be joined to downloads per video (a high-retention video that installs nobody and a low-retention video that installs are indistinguishable without the join)")
    if not ms.get("per_format"):
        fails.append("RT-5 retention is not read per format (Ernesto tracked 7,600+ of his own UGC videos to find what every viral one shares; an aggregate hides which format carries the arc)")
    return fails, warns

def main():
    d = json.load(open(sys.argv[1]))
    fails, warns = check(d)
    for w in warns: print("WARN:", w)
    for f in fails: print("FAIL:", f)
    print(f"{'PASS' if not fails else 'FAIL'}: {len(fails)} fail(s), {len(warns)} warning(s) -- {d.get('app')}")
    sys.exit(0 if not fails else 1)

if __name__ == "__main__":
    main()
