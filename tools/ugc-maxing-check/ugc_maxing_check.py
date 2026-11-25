#!/usr/bin/env python3
"""ugc-maxing-check: deterministic gate for the UGC MAXING program surface (the system
that turns proven content into daily volume across accounts). Stdlib only, offline, free.
Owns the PROGRAM layer: content machine + amplification + agent distribution + volume math.
Not the per-video brief (ugc-brief-check UB-0..), not per-account winner copying
(distribution loops), not paid creator hiring (banned: paid growth is prohibited).
Sources (read 2026-11-22):
- Postiz, "UGC Strategy for Apps: How One Studio Scaled to 6,000 Videos a Month With
  Creators, Theme Pages and an AI Agent" https://postiz.com/blog/ugc-strategy-6000-videos-theme-pages-ai-agent
  (read in full) Christian-app studio, own numbers: 6,000 videos/month peak, $150k/month
  revenue, studio $1.7M/year, 150M+ views in 3 months, core team 15 produced 100M+ views.
  Two halves: content machine (daily new content) + content amplification (every winner
  pushed across theme pages); amplification only multiplies what is proven -- amplify a
  flop and you get many flops. Brief = daily scripts + all assets + examples from other
  creators + content calendar; a creator who fails with that brief has a skill issue.
  Theme pages (brand-owned, one topic, no personal identity), 3 types: AI replicas of own
  best UGC (~1/10 cost), cinematic 3D hook reposts of already-viral videos (10M+ views;
  start here -- no new footage needed), AI story videos about the problem the app solves.
  Distribution: one approved folder daily -> AI agent schedules via Postiz to TikTok +
  Instagram + YouTube in one step; team reviews the calendar instead of filling it.
  PAID PARTS NOT COPIED (user rule: paid growth prohibited): Sideshift $299/mo, ~$100k
  creator payouts, per-creator salaries. Free form used here: own existing accounts as
  theme pages + AI replicas/stories + agent-run Postiz distribution already in place.
- viral.app, "Canvas UGC for Apps: Organic Acquisition Playbook (2026)"
  https://viral.app/blog/insights/canvas-ugc-organic-acquisition-apps
  (search-result read, secondary): ~300k TikToks / 100k Reels measured. Accounts posting
  20-39/month had a 100K-view post in 28% of months vs 7% at 1-4 posts; per-post breakout
  chance stays 2.6-4.1% up to ~40 posts/month; judge a new account only after 30-60 posts;
  accounts posting 80+/month were 87% photo slideshows, which break out less often.
Exit 0=PASS, 1=FAIL.
"""
import json, sys
def check(d):
    f=[]
    dec=d.get("program_decision") or {}
    if not dec.get("two_layer_system_recorded"): f.append("UM-0 the program is not recorded as two layers (content machine that makes new content daily + amplification that pushes every winner across accounts -- most teams build only the first half and growth stalls)")
    if not dec.get("amplify_only_proven_winners"): f.append("UM-0 amplification is not restricted to proven winners (amplification multiplies what is already proven; amplify a flop and you get many flops)")
    if not dec.get("free_organic_form_recorded"): f.append("UM-0 the free/organic form is not recorded (the source playbook's paid parts -- hiring platform fees, creator payouts -- are prohibited here; the copied form is own accounts + AI replicas/stories + agent distribution, at no new spend)")
    if not dec.get("existing_accounts_only"): f.append("UM-0 theme pages are not restricted to existing accounts (no new SNS accounts are created; amplification runs on accounts the company already operates)")
    mac=d.get("content_machine") or {}
    if not mac.get("proven_format_fixed_before_volume"): f.append("UM-1 volume is produced before one format is proven and written down (hook, first frame, beats, CTA -- the format that keeps beating the average becomes the brief; volume on an unproven format is noise)")
    if not mac.get("brief_gives_everything"): f.append("UM-1 producers are left to invent (the brief hands over daily scripts, all assets, examples from other producers, and a content calendar -- with that brief, failure is an execution issue, not a brief issue)")
    if not mac.get("stock_built_ahead"): f.append("UM-1 content is not batch-produced ahead into stock (daily volume that depends on same-day production stops on the first bad day; winners pre-build)")
    if not mac.get("comedy_taste_in_scripts"): f.append("UM-1 scripts carry no comedy taste (company rule 2026-11-22: comedy taste goes into everything -- posts included; a hard-day/stress audience opens the app because it is funny)")
    amp=d.get("amplification") or {}
    if not amp.get("every_winner_gets_amplified"): f.append("UM-2 proven winners are posted once on one account and left (every viral video is raw material, not a finished post -- each winner is rebuilt for more accounts)")
    if not amp.get("theme_page_types_assigned"): f.append("UM-2 the three theme-page types are not assigned (AI replicas of own best content / cinematic-hook reposts of proven winners / AI story videos about the problem the app solves)")
    if not amp.get("start_with_hook_reposts"): f.append("UM-2 amplification does not start with hook reposts (they need no new footage -- a new scroll-stopping opening on content that already proved it converts -- and come before replicas/stories, which need a proven library to model)")
    if not amp.get("hook_clips_rights_safe"): f.append("UM-2 hook clips are not rights-safe (use clips we own or generate in the same style; borrowed viral hooks invite takedowns on every page that carries them)")
    dis=d.get("agent_distribution") or {}
    if not dis.get("single_approved_folder_pipeline"): f.append("UM-3 new content does not land in one approved folder daily (machine output, replicas and stories converge in one place the agent picks up -- scattered files are unscheduled files)")
    if not dis.get("agent_schedules_all_platforms_one_step"): f.append("UM-3 distribution is hand-posted per platform (the agent schedules each video to TikTok + Instagram + YouTube in one step via Postiz; dozens of accounts cannot be run by logging in and out)")
    if not dis.get("calendar_reviewed_not_handfilled"): f.append("UM-3 the calendar is filled by hand (the agent fills it; the team's job is reviewing the calendar, not assembling it)")
    if not dis.get("winners_requeued_with_new_hook"): f.append("UM-3 proven winners are not re-queued (a winner gets a new hook and goes out again on theme pages -- the queue is a loop, not a one-way chute)")
    vol=d.get("volume_math") or {}
    if not vol.get("per_account_cadence_in_winner_band"): f.append("UM-4 per-account cadence is below the winner band (measured: 20-39 posts/month -> a 100K post in 28% of months vs 7% at 1-4 posts; about one a day per account is the floor the math supports)")
    if not vol.get("accounts_judged_after_30_to_60_posts"): f.append("UM-4 accounts are judged before 30-60 posts (breakout is a per-post lottery at 2.6-4.1%; killing an account at post 8 judges the lottery, not the account)")
    if not vol.get("slideshows_not_counted_as_video_volume"): f.append("UM-4 photo slideshows are counted toward video volume at high cadence (at 80+/month accounts were 87% slideshows, which break out less often -- inflated counts hide a video shortfall)")
    mea=d.get("measurement_honesty") or {}
    if not mea.get("judged_on_installs_not_views"): f.append("UM-5 the program is judged on views (views are the lottery ticket; installs and paywall starts are the payout -- a format that earns views without installs is top-of-funnel only)")
    if not mea.get("winner_variant_pairs_recorded"): f.append("UM-5 winner-to-variant pairs are not recorded (each amplified variant names its source winner URL and its own URL -- an amplification claim without the pair is unverifiable)")
    if not mea.get("shown_experience_exists_in_app"): f.append("UM-5 amplified content shows an experience that is not in the app (outside must equal inside: words/experiences shown in distribution must exist in the product, or the install is bought with a lie)")
    return f
if __name__=="__main__":
    data=json.load(open(sys.argv[1])); fails=check(data)
    if fails:
        print(f"FAIL ({len(fails)}):")
        [print(" -",x) for x in fails]; sys.exit(1)
    print("PASS"); sys.exit(0)
