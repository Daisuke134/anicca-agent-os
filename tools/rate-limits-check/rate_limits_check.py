#!/usr/bin/env python3
"""rate-limits-check: deterministic gate for the Rate Limits surface
(how an organization's spend caps, per-model RPM / ITPM / OTPM limits,
cache-aware token counting, ramp limits, 429 variants, response headers
and per-surface separate limits are known, honored and monitored -
decided, not left to each caller retrying blind).
Stdlib only, offline.
Canonical source (read in full 2026-11-19):
- Anthropic Claude Platform Docs "Rate limits"
  https://platform.claude.com/docs/en/api/rate-limits
  (340 lines read in full): two limit kinds - spend limits (maximum
  monthly cost) and rate limits (maximum requests over a period).
  Service limits are enforced at organization level; workspace limits
  are user-configurable. Tiers are assigned automatically from usage
  history and standing; new / low-history orgs may start in an
  Evaluation tier below the standard limits shown. Limits are maximums,
  not guaranteed minimums. Enforcement uses the token bucket algorithm
  (capacity replenishes continuously, not at fixed resets), and a
  nominal 60 RPM can be enforced as 1 request per second, so short
  bursts can trigger errors while under the per-minute figure.
  Spend caps by tier: Start $500, Build $1,000, Scale $200,000 per
  calendar month; Custom has no cap. Reaching the tier cap pauses API
  usage until 00:00 UTC on the first of next month and returns HTTP
  429 rate_limit_error with NO retry-after header and, on Messages,
  error.details.error_code enforced_spend_limit_reached - retrying,
  including SDK automatic retries, fails until access resumes; moving
  to a higher tier restores access. A self-set spend limit below the
  cap instead returns HTTP 400 invalid_request_error ("You have
  reached your specified API usage limits...") and is lifted by
  raising or removing the limit; Claude Code workspace limits are
  checked separately and can return a 429 WITH retry-after.
  Messages rate limits are RPM, ITPM and OTPM per model class; rows
  can share one combined bucket (Fable 5.1 family, Opus 4.x family,
  Sonnet 4.x family each share; newer flagship rows are separate).
  Default ITPM counts only uncached input tokens: input_tokens and
  cache_creation_input_tokens count, cache_read_input_tokens do NOT -
  at a 2M ITPM limit and 80 percent cache hit rate, 10M total input
  tokens per minute are effectively processable. ITPM is estimated at
  request start and adjusted during the request. OTPM is evaluated in
  real time on actual output tokens only; max_tokens does not factor
  into OTPM, so a higher max_tokens carries no rate-limit downside.
  Ramp limits cap how fast usage on a model can grow: the limit is the
  org's recent per-minute peak plus a step, rising at most one step
  per minute of successful usage up to the rate limit and falling
  after quiet periods, never below a starting amount; input and
  output are counted separately, fast mode has its own ramp, cache
  reads do not count, and a burst within seconds can itself count as a
  sharp increase. A ramp 429 carries error_code ramp_limit_exceeded;
  recovery is to wait retry-after, hold at a succeeding level, then
  grow at most one step per minute, and to start bulk jobs low and
  spread evenly. The Message Batches API is not subject to ramp.
  Separate surfaces: Batches has its own limits shared across models
  (1,000 RPM to all endpoints, 200,000 batch requests in the
  processing queue, 100,000 per batch); Managed Agents endpoints have
  their own org limits (create 300 RPM, read 1,200 RPM), separate
  from Messages; the Files API has its own per-org limit shared across
  upload / list / retrieve / download / delete; fast mode
  (speed: "fast") has dedicated limits separate from standard, with
  anthropic-fast-* status headers.
  Responses carry anthropic-ratelimit-requests / -tokens /
  -input-tokens / -output-tokens limit / remaining / reset headers
  (plus anthropic-priority-* on Priority Tier); the tokens headers
  show the most restrictive limit in effect, remaining is rounded to
  the nearest thousand, resets are RFC 3339, and
  anthropic-workspace-id names the workspace a request counted
  against. Current limits are visible on the Console Rate limits page
  (Custom tier is shown for every org on AWS / Google Cloud managed)
  and readable / settable via the Rate Limits API; the Usage page
  charts hourly maximum uncached ITPM, the current ITPM limit and the
  cache rate, plus hourly maximum OTPM against its limit. Higher
  limits are requested via "Request tier increase" on the Rate limits
  page or Anthropic support. Workspace spend / rate limits protect
  workspaces from each other, are set per limiter type, default to the
  org limit when unset, and never override the org-wide limit even
  when they sum above it; on AWS / Google Cloud the default workspace
  cannot take a spend limit, and a default-workspace spend limit may
  not count or stop Console playground, Managed Agents, or Console-
  account Claude Code / Desktop usage (the org limit still applies).
Exit 0=PASS, 1=FAIL.
"""
import json, sys
def check(d):
    f=[]
    dec=d.get("decision") or {}
    if not dec.get("decision_recorded"): f.append("RL-0 the Rate Limits surface is not recorded as a decided surface - which limits bind which workloads, and what happens at each limit, is left to each caller and habit, not a decision")
    if not dec.get("owner_recorded"): f.append("RL-0 no owner is recorded for limit correctness (tier, headroom, 429 handling) - a workload that burns the shared org bucket or retries a paused surface has no accountable reader")
    if not dec.get("tiers_inventoried"): f.append("RL-0 the organization's tier and current limits are not inventoried (tier is assigned from usage history, new orgs may sit in an Evaluation tier below the published standard limits, and the Console limits page - showing Custom tier for every org on AWS / Google Cloud managed - is the record) - planning runs on published table numbers the org may not actually have")
    kn=d.get("knowledge") or {}
    if not kn.get("dimensions_known"): f.append("RL-1 the limit dimensions are not known (Messages limits are RPM, ITPM and OTPM per model class at organization level, enforced with a token bucket that replenishes continuously - a nominal 60 RPM can be enforced as 1 request per second, so bursts error while under the per-minute figure; published limits are maximums, not guaranteed minimums) - callers pace to the minute figure and are surprised by burst rejections")
    if not kn.get("cache_aware_counting_known"): f.append("RL-1 cache-aware counting is not known (default ITPM counts only uncached input: input_tokens and cache_creation_input_tokens count, cache_read_input_tokens do not - at 2M ITPM and an 80 percent cache hit rate, 10M total input tokens per minute are effectively processable; ITPM is estimated at request start and adjusted in flight; OTPM counts actual output in real time and max_tokens does not factor into it, so raising max_tokens has no rate-limit downside) - throughput is left on the table, or headroom is misjudged in both directions")
    if not kn.get("shared_buckets_known"): f.append("RL-1 shared buckets are not known (some table rows are one combined limit across a model family - the Fable 5.1 family, the Opus 4.x family and the Sonnet 4.x family each share a bucket, while newer flagship rows are separate) - parallel workloads on sibling models are budgeted as if each had its own full limit and collide")
    rt=d.get("retry") or {}
    if not rt.get("retry_after_honored"): f.append("RL-2 retry-after is not honored (on a 429 that carries retry-after, wait at least that many seconds before retrying; earlier retries can fail - and not every 429 carries the header) - retries land inside the enforced window and extend the block")
    if not rt.get("error_variants_distinguished"): f.append("RL-2 the 429 / limit variants are not distinguished (a tier spend-cap 429 has NO retry-after and carries error_code enforced_spend_limit_reached, and retrying - including SDK automatic retries - fails until access resumes; a ramp 429 carries ramp_limit_exceeded; a self-set spend limit instead returns HTTP 400 invalid_request_error; a Claude Code workspace limit can return a 429 WITH retry-after) - a month-long pause is retried as if it were a per-minute limit, or a brief limit is abandoned as if it were a pause")
    if not rt.get("ramp_handled"): f.append("RL-2 ramp limits are not handled (the ramp cap is the recent per-minute peak plus a step, rising at most one step per minute of successful usage and falling after quiet periods, never below a starting amount; input and output count separately, fast mode ramps separately, cache reads do not count, and a seconds-long burst can itself trip it; recovery is to wait retry-after, hold at a succeeding level, grow at most one step per minute, and start scheduled or bulk jobs low and spread evenly - the Batches API is exempt) - a cold-start bulk job 429s while nominally under its ITPM / OTPM limits and the cause is misread")
    sp=d.get("spend") or {}
    if not sp.get("tier_caps_known"): f.append("RL-3 tier spend caps are not known (Start $500, Build $1,000, Scale $200,000 per calendar month, Custom uncapped; reaching the cap pauses API usage until 00:00 UTC on the first of the next month, and moving to a higher tier restores access sooner) - a hard monthly stop is discovered by outage instead of planned around")
    if not sp.get("own_limits_set"): f.append("RL-3 self-set limits are not used deliberately (an org can set its own spend limit below the tier cap and per-workspace spend / rate limits per limiter type; unset workspace limits match the org limit, org-wide limits always apply even when workspace limits sum above them, the default workspace cannot take a spend limit on AWS / Google Cloud managed, and a default-workspace limit may not count Console playground, Managed Agents or Console-account Claude Code / Desktop usage) - one workspace can consume the whole org, or a limit believed protective silently excludes the surfaces that matter")
    if not sp.get("paused_surface_not_retried"): f.append("RL-3 a paused surface is retried (once a spend cap is reached, requests fail until access resumes and automatic SDK retries fail with them; the only restorations are the calendar reset, a tier increase, or raising / removing a self-set limit) - retry loops burn the window they are waiting out and bury the real signal")
    mo=d.get("monitoring") or {}
    if not mo.get("headers_read"): f.append("RL-4 response limit headers are not read (anthropic-ratelimit-requests / -tokens / -input-tokens / -output-tokens limit, remaining and reset, plus anthropic-priority-* on Priority Tier; the tokens headers show the most restrictive limit in effect, remaining is rounded to the nearest thousand, resets are RFC 3339, and anthropic-workspace-id names the workspace the request counted against) - headroom is guessed from errors instead of read from every response")
    if not mo.get("console_monitored"): f.append("RL-4 Console usage is not monitored (the Usage page charts hourly maximum uncached input tokens per minute against the current ITPM limit together with the cache rate, and hourly maximum output tokens per minute against the OTPM limit - the record for headroom, peak timing and caching tuning) - limit increases are requested, or caching left untuned, without the measured peak that justifies either")
    if not mo.get("limits_api_used"): f.append("RL-4 limits are not read programmatically (the Rate Limits API reads the org's and workspaces' configured limits and sets workspace limits; the Console Rate limits page is the human record) - automation paces against stale or published-table limits instead of the org's configured ones")
    va=d.get("variants") or {}
    if not va.get("separate_surfaces_known"): f.append("RL-5 separate-surface limits are not known (Batches: 1,000 RPM shared across models, 200,000 batch requests in the processing queue, 100,000 per batch; Managed Agents: create 300 RPM and read 1,200 RPM per org, separate from Messages; Files API: its own per-org limit shared across upload, list, retrieve, download and delete; fast mode: dedicated limits separate from standard with anthropic-fast-* status headers) - a surface is paced with Messages numbers it does not share, or throttled by a bucket it was never in")
    if not va.get("workspace_limits_applied"): f.append("RL-5 workspace limits are not applied where workloads share an org (custom spend and rate limits per workspace protect workspaces from each other's overuse and share the org bucket deliberately, set per limiter type) - the noisiest loop or job starves the rest of the organization without any record of the choice")
    if not va.get("higher_limits_path_known"): f.append("RL-5 the higher-limits path is not known (Request tier increase on the Console Rate limits page, or Anthropic support for urgent needs; a tier move also restores access after a spend-cap pause) - a genuine ceiling is worked around with retries and splits instead of raised through the one route that raises it")
    return f
if __name__=="__main__":
    data=json.load(open(sys.argv[1])); fails=check(data)
    if fails:
        print(f"FAIL ({len(fails)}):")
        [print(" -",x) for x in fails]; sys.exit(1)
    print("PASS"); sys.exit(0)
