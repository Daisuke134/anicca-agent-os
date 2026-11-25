#!/usr/bin/env python3
"""volume-experiment-check: deterministic gate for winner-style multi-account
content volume experiments (TikTok-first). Stdlib only, offline, free.
Primary source (read in full this run, 2026-11-23, via fxtwittergo):
- Ernesto Lopez (@ErnestoSOFTWARE), X post 2026-11-22:
  30 TikTok accounts on 4 phones, 60 videos/day, 1,800/month, every account
  created the same day, no warmup, 150k views within 3 days; his thesis is
  "shadow bans are not real" and volume finds a viral format fast, after which
  the first viral video is a domino into 100s of millions of views.
  https://x.com/ErnestoSOFTWARE/status/2124327598519988274
  His thesis is recorded AS HIS CLAIM, not as a proven fact: this gate requires
  the experiment to state its hypothesis and read its own numbers, never to
  assert the thesis before the read.
- Corroborating GOAT record (goats-watch): Ernesto's standing pattern is
  format-first (find a format already working in the niche, then put volume
  behind it; 1/day -> 6/day -> creator army replicating the ONE winning format).
Exit 0 = PASS, 1 = FAIL."""
import json, sys
def check(d):
    f=[]
    e=d.get("experiment") or {}
    if not e.get("exists"): f.append("MV-0 no volume experiment exists (posting a fixed 3 slots/day on one account is a schedule, not an experiment; the winner's unit of learning is a volume experiment with a stated hypothesis)")
    if not e.get("hypothesis_recorded"): f.append("MV-0 hypothesis is not recorded before launch (e.g. reach suppression vs volume; an experiment without a pre-registered hypothesis can prove anything afterwards)")
    if e.get("thesis_asserted_as_fact"): f.append("MV-0 a platform-behaviour thesis (e.g. 'shadow bans are not real') is asserted as fact before the experiment's own read (the winner states it as his thesis and posts 30 days of updates; copy the experiment, not the conclusion)")
    v=d.get("volume") or {}
    if not v.get("accounts_count"): f.append("MV-1 account count is not recorded (winner benchmark: 30 accounts; unrecorded fleet size makes the per-account rate unknowable)")
    if not v.get("posts_per_day_total"): f.append("MV-1 total posts/day is not recorded (winner benchmark: 60/day = 1,800/month; volume is the variable, so it must be a number, not an intention)")
    if v.get("posts_per_day_total") and v.get("accounts_count") and not v.get("posts_per_account_per_day"): f.append("MV-1 posts per account per day is not derived/recorded (total / accounts; a fleet total can hide one spammed account and 29 idle ones)")
    a=d.get("accounts") or {}
    if not a.get("all_owned_or_authorized"): f.append("MV-2 accounts are not recorded as all owned/authorized by the team (no purchased, borrowed or third-party accounts; fleet experiments run on accounts the operator controls end to end)")
    if a.get("purchased_accounts"): f.append("MV-2 purchased accounts are in the fleet (prohibited: provenance and standing-rule violation; new accounts are created by the team itself under the standing account rules)")
    if not a.get("creation_recorded"): f.append("MV-2 creation date/device per account is not recorded (the winner's variable was same-day creation with no warmup; whether warmup matters can only be read if creation conditions are in the ledger)")
    c=d.get("content") or {}
    if not c.get("format_is_winner_copy"): f.append("MV-3 content format is not a copy of a proven winner format (volume behind an original format tests two unknowns at once; the winner puts volume behind a format already working in the niche)")
    if not c.get("single_variable"): f.append("MV-3 more than one variable changes across the fleet (format, hook, account age and volume all moving means the read cannot attribute the result)")
    if c.get("fake_engagement"): f.append("MV-3 fake engagement is in use (prohibited: bought views/likes, engagement pods, or review manipulation of any kind; volume is a distribution test, not a metrics forgery)")
    m=d.get("measurement") or {}
    if not m.get("early_read_day"): f.append("MV-4 no early read is scheduled (winner read at day 3: 150k views; a 30-day experiment with no early read cannot kill a dead format early)")
    if not m.get("update_cadence_recorded"): f.append("MV-4 no fixed update cadence is recorded for the experiment's duration (winner: updates for 30 days; unrecorded cadence means the experiment silently stops being read)")
    if m.get("judged_on_views_only"): f.append("MV-4 results are judged on views only (views are the headline; saves, profile visits and installs decide whether the format converts)")
    if not m.get("winning_format_amplification_plan"): f.append("MV-4 no amplification plan exists for the first winning format (the winner's domino: one viral format gets replicated across the fleet/creators; a test with no scale-up step wastes its own finding)")
    g=d.get("guardrails") or {}
    if not g.get("stop_rule_on_enforcement"): f.append("MV-5 no stop rule is recorded for platform enforcement action (a warning/restriction on any fleet account pauses the fleet for review; pushing through enforcement converts an experiment into an account loss)")
    if not g.get("claims_recorded_as_claims"): f.append("MV-5 results are not recorded with claims separated from measured facts (follower counts and view totals from the operator's own posts are claims until the ledger's own read confirms them)")
    return f
def main():
    d=json.load(open(sys.argv[1])); fails=check(d)
    for x in fails: print("FAIL:",x)
    print(f"{'PASS' if not fails else 'FAIL'}: {len(fails)} fail(s) -- {d.get('app')}")
    sys.exit(0 if not fails else 1)
if __name__=="__main__": main()
