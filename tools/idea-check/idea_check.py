#!/usr/bin/env python3
"""App-idea selection gate checker (Mau Baron prompt, adapted).
Primary source (full image read 2026-11-13):
 - Mau Baron (@maubaron) "the only prompt you need to find a $100k/mo app
   idea" https://x.com/maubaron/status/2121065223839006722
   (image 1336x4096 read in full: don't invent, find apps already printing;
    Step 1 find 20 printing apps w/ revenue evidence, reviews + reviews/week,
    creators + views, paywall, creator one-liner, rank by revenue / quality;
    Step 2 pick 5 that pass: one sentence + one screenshot, visible twist,
    daily creators, belong-or-hire, buildable in 2 weeks, day-1 win, mascot,
    3 screenshots; Step 3 check content BEFORE building: 10 best competitor
    videos, 10 hooks, one of 3 formats, kill if no 100k+ view video exists;
    Step 4 money math: yearly+weekly price, 100k views -> paid at 3-5%
    download-to-paid, months to $10k/$25k/$100k; Step 5 launch test:
    onboarding+paywall copied from best in niche, launch-day 10 hooks,
    1-5 paid on day 1 = alive, 100k views + 0 paid = kill, don't tinker.)
Corroboration (full-text read 2026-11-13):
 - Starter Story / David Adias (Stoppr, sugar-quit): cloned a $200k/mo app,
   validated via Google Trends + TikTok/IG content research, exact copy of
   onboarding, built in ~2.5 weeks, 60k downloads / ~900 paying / $12k/mo
   in 5 months, first month $5k.
   https://www.starterstory.com/stories/i-found-a-successful-app-made-it-1-different-and-now-make-12k-month-stoppr
Adaptations (owner rules override the source where they conflict):
 - Paywall: source prefers hard paywall for first apps. Portfolio rule:
   Anicca is soft paywall by owner decision 2026-11-13. Gate I-2 therefore
   requires the model to be RECORDED with a reason, not hard by default.
 - Money: source assumes 3 paid creators ($500-$1,000/mo each) + $100/day
   Spark ads. Paid growth is prohibited (free organic only). Gate I-4
   therefore FAILS any plan that requires paid creators or ads, and
   requires a recorded free-organic capacity path to $10k/mo instead.
 - Prayer Lock dark patterns (fake timer, win-back pressure, review
   steering) are never copied; they fail I-2 if present in the twist.
Gates:
 I-0 category & buildability: category is one of the boring printing
     categories; idea needs no marketplace / social feed / chat / team /
     expensive backend.
 I-1 printing evidence (Step 1): source app monthly revenue AND how it is
     known, total reviews, rating, reviews/week, creators posting + their
     views, source paywall, creator one-liner; revenue/quality rank noted.
 I-2 winnable (Step 2): one sentence, one screenshot, visible twist,
     daily creators in niche, belong-or-hire, build <= 14 days, day-1 win,
     mascot/visual, 3 store screenshots planned, paywall model recorded
     with reason, no dark patterns in twist.
 I-3 content before build (Step 3): >=10 best competitor videos found,
     >=10 hooks written, format chosen (reaction_demo / talking_head /
     skit), best competitor video >= 100,000 views (else kill).
 I-4 money math, free-organic (Step 4): yearly + weekly price recorded,
     views->paid math recorded with download-to-paid rate in 3-5% band
     (or a recorded reason outside it), months-to-$10k recorded, plan
     reaches $10k/mo on free organic capacity, no paid creators / ads.
 I-5 launch test (Step 5): onboarding + paywall copied from a named best
     in niche, launch hooks >= 10, kill rules recorded (day-1 paid range
     = alive; 100k views + 0 paid = kill), no-tinker rule recorded.
"""
import json, sys

BORING = {"screen_time_blocker", "quit_addiction", "habit_routine", "faith",
          "walking_steps", "sleep", "fasting_water", "counter_streak_lock",
          "affirmation"}
FORMATS = {"reaction_demo", "talking_head", "skit"}
DARK = {"fake_timer", "winback_pressure", "review_steering"}

def main(path):
    d = json.load(open(path))
    fails, warns = [], []
    # I-0
    if not d.get("candidate_recorded"):
        fails.append("I-0 candidate is not recorded")
    if d.get("category") not in BORING:
        fails.append(f"I-0 category {d.get('category')!r} is not one of the boring printing categories")
    for k in ("needs_marketplace", "needs_social_feed", "needs_chat", "needs_team", "needs_expensive_backend"):
        if d.get(k):
            fails.append(f"I-0 idea requires {k} (source rule: skip)")
    # I-1
    s1 = d.get("step1_printing") or {}
    if not s1.get("source_monthly_revenue_usd"):
        fails.append("I-1 source app monthly revenue is not recorded")
    if not s1.get("revenue_evidence_how"):
        fails.append("I-1 revenue evidence method is not recorded (ranking / reviews-per-week / creator activity)")
    if not s1.get("total_reviews"):
        fails.append("I-1 source total reviews not recorded")
    if not s1.get("rating"):
        fails.append("I-1 source rating not recorded")
    if not s1.get("reviews_per_week"):
        fails.append("I-1 source reviews/week not recorded (printing-now evidence)")
    if not s1.get("creators_posting"):
        fails.append("I-1 creators posting about the source app not recorded")
    if not s1.get("creator_video_views"):
        fails.append("I-1 creator video views not recorded")
    if not s1.get("source_paywall_recorded"):
        fails.append("I-1 source paywall (price / trial / hard-or-freemium) not recorded")
    if not s1.get("creator_one_liner"):
        fails.append("I-1 creator one-sentence pitch not recorded")
    if not s1.get("ranked_by_revenue_over_quality"):
        warns.append("I-1 rank by revenue / quality not recorded (best targets are ugly apps making a lot of money)")
    # I-2
    s2 = d.get("step2_winnable") or {}
    for k, msg in (
        ("one_sentence", "one-sentence pitch"), ("one_screenshot", "one-screenshot explainability"),
        ("visible_twist", "visible twist in store screenshots"), ("daily_creators_in_niche", "daily creators in niche"),
        ("belong_or_hire_creators", "belong-to-niche or hireable creators"), ("day1_win", "day-1 win"),
        ("mascot_or_visual", "mascot / brand visual"), ("three_screenshots_planned", "3 store screenshots plan")):
        if not s2.get(k):
            fails.append(f"I-2 {msg} is not recorded")
    bd = s2.get("build_days")
    if bd is None or bd > 14:
        fails.append(f"I-2 build time {bd} exceeds 14 days (or unrecorded)")
    if not s2.get("paywall_model") or not s2.get("paywall_model_reason"):
        fails.append("I-2 paywall model / reason not recorded (portfolio rule: recorded + reasoned, Anicca = soft by owner decision)")
    dark = set(s2.get("twist_elements") or []) & DARK
    if dark:
        fails.append(f"I-2 twist contains prohibited dark patterns: {sorted(dark)}")
    # I-3
    s3 = d.get("step3_content_first") or {}
    if (s3.get("best_competitor_videos_found") or 0) < 10:
        fails.append("I-3 fewer than 10 best competitor videos found (content check comes before building)")
    if (s3.get("hooks_written") or 0) < 10:
        fails.append("I-3 fewer than 10 hooks written in the competitor style")
    if s3.get("format") not in FORMATS:
        fails.append(f"I-3 format {s3.get('format')!r} is not one of reaction_demo / talking_head / skit")
    if (s3.get("best_competitor_video_views") or 0) < 100000:
        fails.append("I-3 no competitor video at 100k+ views: kill rule applies (no content = no distribution = no app)")
    # I-4
    s4 = d.get("step4_money_math") or {}
    if not s4.get("yearly_price_usd") or not s4.get("weekly_price_usd"):
        fails.append("I-4 yearly + weekly price not both recorded")
    if not s4.get("views_to_paid_math_recorded"):
        fails.append("I-4 100k-views -> downloads / paid / revenue math not recorded")
    rate = s4.get("download_to_paid_pct")
    if rate is None:
        fails.append("I-4 download-to-paid rate not recorded")
    elif not (3 <= rate <= 5) and not s4.get("rate_outside_band_reason"):
        warns.append(f"I-4 download-to-paid rate {rate}% is outside the source 3-5% band without a recorded reason")
    if s4.get("months_to_10k") is None:
        fails.append("I-4 months to $10k/mo not recorded")
    if s4.get("paid_creators_required") or s4.get("paid_ads_required"):
        fails.append("I-4 plan requires paid creators or paid ads (prohibited: free organic only)")
    if not s4.get("reaches_10k_on_free_organic"):
        fails.append("I-4 plan does not reach $10k/mo on recorded free-organic capacity (source kill rule, adapted)")
    # I-5
    s5 = d.get("step5_launch_test") or {}
    if not s5.get("onboarding_paywall_copied_from"):
        fails.append("I-5 onboarding + paywall copied-from (named best in niche) not recorded")
    if (s5.get("launch_hooks") or 0) < 10:
        fails.append("I-5 launch hooks fewer than 10")
    if not s5.get("day1_alive_rule_recorded"):
        fails.append("I-5 day-1 alive rule (1-5 paid = alive, go all-in on distribution) not recorded")
    if not s5.get("kill_rule_recorded"):
        fails.append("I-5 kill rule (100k views + 0 paid = kill, do not fix product) not recorded")
    if not s5.get("no_tinker_until_3k_recorded"):
        warns.append("I-5 no-product-tinkering until $3k/mo rule not recorded")
    return fails, warns

if __name__ == "__main__":
    f, w = main(sys.argv[1])
    for x in f: print("FAIL:", x)
    for x in w: print("WARN:", x)
    print(f"RESULT: {'PASS' if not f else 'FAIL'} ({len(f)} fails, {len(w)} warns)")
    sys.exit(0 if not f else 1)
