#!/usr/bin/env python3
"""web-tools-check: deterministic gate for the Web Tools surface
(how Claude's server-side web search and web fetch are triggered,
versioned, budgeted, domain-filtered, content-limited, continued
across turns with encrypted payloads and citations, provenance-checked
for fetched URLs, and accounted - $10 per 1,000 searches vs fetch at
token cost only - is decided, not left to whatever each call happens
to request).
Stdlib only, offline.
Canonical sources (read in full 2026-11-19):
- Anthropic Claude Platform Docs "Web search tool"
  https://platform.claude.com/docs/en/agents-and-tools/tool-use/web-search-tool
  (250 lines read in full): Claude searches when the request depends on
  current / changing / out-of-training information or explicitly asks;
  it answers directly for stable knowledge, creative work, analysis of
  provided content and greetings. Triggering is steerable via the
  system prompt; max_uses caps searches per turn (single-fact 1-3,
  comparative research 10+), failed searches count, and a turn spanning
  pause_turn / tool_result-only continuations accumulates against the
  same cap (dynamic-filtering calls excepted). Versions:
  web_search_20250305 basic, web_search_20260209 adds dynamic filtering
  (code filters results before context; allowed_callers defaults to
  ["code_execution_20260120"], set ["direct"] to call directly - models
  without programmatic tool calling require it or return 400; the API
  provisions the needed code execution automatically at no extra charge
  beyond tokens), web_search_20260318 adds response_inclusion
  ("excluded" drops nested blocks consumed by code execution; token
  usage unaffected; direct / paused calls always return full).
  Domain filtering: allowed_domains XOR blocked_domains (both = 400),
  bare domains with optional path, no scheme. user_location localizes
  (type approximate; city / region / ISO 3166-1 alpha-2 country - bad
  code = 400 / IANA timezone). Search results carry url, title,
  page_age and encrypted_content that must be passed back exactly in
  multi-turn use (missing or modified = 400). Citations are always
  enabled; web_search_result_location carries url, title,
  encrypted_index and cited_text (up to 150 chars); cited_text / title /
  url do not count toward token usage. Errors arrive in-body on an
  HTTP 200: too_many_requests, invalid_tool_input, max_uses_exceeded,
  query_too_long, request_too_large, unavailable; a successful search
  with no matches returns an empty content list, not an error.
  stop_reason pause_turn: resend the paused assistant message
  unchanged; mixing server and client tools in one parallel group
  returns tool_use instead and the search runs after client results.
  Pricing: $10 per 1,000 searches plus token costs; results count as
  input tokens in the turn and in later turns; failed searches are not
  billed; Batches API prices search the same but throttles it per org.
  Support is checkable per model via the Models API
  (capabilities.server_tools.web_search.supported).
- Anthropic Claude Platform Docs "Web fetch tool"
  https://platform.claude.com/docs/en/agents-and-tools/tool-use/web-fetch-tool
  (276 lines read in full): fetch retrieves full content from specified
  webpages and PDFs (PDFs return as base64 document content); Claude
  fetches when a URL is present or a specific resource is named (with
  search enabled it locates it first - combined search and fetch);
  it does not fetch for general-knowledge questions. Versions:
  web_fetch_20250910 basic, 20260209 dynamic filtering, 20260309 adds
  cache bypass, 20260318 adds response inclusion. max_uses caps fetches
  per turn (failed fetches count; no default limit). max_content_tokens
  truncates text content (approximate; binary / PDF exempt - an
  oversize PDF is a content_too_large error against the PDF limits).
  use_cache defaults true; false bypasses the cache for fresh content
  only on explicit need (bypass costs latency). Citations are optional
  and off by default (citations.enabled=true to allow citing fetched
  passages) - unlike search, where they are always on. URL validation:
  fetch only URLs that appeared earlier in the conversation - user
  messages, client-side tool results, or prior web search / fetch
  results; URLs appearing only in Claude's own output or only in the
  system prompt are not fetchable; server-tool results other than
  search / fetch are not a source; url_sources can disable or filter
  each source (a filter naming a tool not in tools fails the request).
  A URL that appears to contain a credential is refused
  (url_not_allowed) unless the credential appears in the system prompt
  or a user message. Errors arrive in-body on HTTP 200:
  invalid_tool_input, url_too_long (over 250 chars), url_not_allowed,
  url_not_in_prior_context, url_not_accessible, too_many_requests,
  unsupported_content_type (only text / HTML / PDF), content_too_large,
  max_uses_exceeded, unavailable. Pricing: no additional charge beyond
  standard token costs (average webpage 10 kB ~ 2,500 tokens; large
  docs page 100 kB ~ 25,000; research PDF 500 kB ~ 125,000); Batches
  pricing is the same as Messages.
Exit 0=PASS, 1=FAIL.
"""
import json, sys
def check(d):
    f=[]
    dec=d.get("decision") or {}
    if not dec.get("decision_recorded"): f.append("WS-0 the Web Tools surface is not recorded as a decided surface - when the model may reach the live web, through which tool and under what limits, is left to each call site and habit, not a decision")
    if not dec.get("owner_recorded"): f.append("WS-0 no owner is recorded for web correctness (triggering, filtering, continuation, provenance, spend) - a stale answer presented as searched, or a search bill nobody expected, has no accountable reader")
    if not dec.get("web_surfaces_inventoried"): f.append("WS-0 there is no inventory of the web surfaces (which work searches, which fetches a known page, which combines search-then-fetch) - the cheaper fetch and the billed search cannot be required where the surfaces are indistinguishable")
    trg=d.get("triggering") or {}
    if not trg.get("search_trigger_decided"): f.append("WS-1 search triggering is not decided (search when the request depends on current, changing or out-of-training information or explicitly asks; answer directly for stable knowledge, creative work, analysis of provided content and greetings; steer the threshold in the system prompt and verify per-model support via the Models API) - the model searches for settled facts it already knows, or answers from training data where the fact has moved")
    if not trg.get("version_and_caller_decided"): f.append("WS-1 the search version and caller are not decided (basic web_search_20250305 vs dynamic filtering on 20260209 and later, where allowed_callers defaults to code execution and filtering keeps irrelevant results out of context; direct calling needs allowed_callers [direct] and models without programmatic tool calling return 400 without it; response_inclusion arrives on 20260318) - every result is loaded raw into context at full token cost, or a request fails on a caller default nobody chose")
    if not trg.get("fetch_trigger_decided"): f.append("WS-1 fetch triggering is not decided (fetch only when a URL is present or a specific page or document is named - locating it with search first when no URL is given; never fetch for general-knowledge or open-ended questions) - fetches fire where a direct answer or a search was the right tool, paying full-page tokens for a fact")
    bud=d.get("budget") or {}
    if not bud.get("max_uses_capped"): f.append("WS-2 max_uses is not capped per surface (search: single-fact 1-3, comparative research 10 or more; fetch has no default limit so an explicit cap is the only brake; failed calls count against the cap, and searches and fetches from earlier requests in the same turn - resumed after pause_turn or continued with tool_result-only messages - accumulate against it, dynamic-filtering calls excepted) - a looping turn searches or fetches without bound and the cap is discovered from the max_uses_exceeded error instead of the design")
    if not bud.get("domain_filtering_decided"): f.append("WS-2 domain filtering is not decided (allowed_domains or blocked_domains, never both - both is a 400; entries are bare domains with an optional path and no scheme; an over-long filter list is request_too_large; organization settings and Managed Agents toolset entries apply on top) - the model reads from sources the surface never meant to trust, or a request fails on a filter combination a pre-check would have caught")
    if not bud.get("content_limits_set"): f.append("WS-2 content limits are not set (fetch max_content_tokens truncates text content - approximately, with binary and PDF content exempt and an oversize PDF failing as content_too_large against the PDF limits, where PDFs and images already in the conversation count too; search-side, dynamic filtering is the equivalent brake) - one large page or paper consumes the context and the budget the rest of the work needed")
    cont=d.get("continuation") or {}
    if not cont.get("encrypted_content_preserved"): f.append("WS-3 encrypted payloads are not preserved across turns (search results carry encrypted_content and citations carry encrypted_index; both must be sent back exactly as received or the request fails with a 400 validation error) - a multi-turn research thread breaks on its second turn, or results are silently dropped to make the error go away")
    if not cont.get("citations_handled"): f.append("WS-3 citations are not handled as designed (search citations are always enabled - url, title, encrypted_index and cited_text up to 150 characters, none of which count toward token usage; fetch citations are optional and off by default, so a surface that must cite fetched passages sets citations.enabled=true) - searched claims ship without their sources, or a fetch surface is assumed to cite when it cannot")
    if not cont.get("url_provenance_enforced"): f.append("WS-3 URL provenance is not enforced for fetch (only URLs that appeared earlier in the conversation are fetchable - user messages, client-side tool results, prior web search or fetch results; URLs appearing only in the model's own output, only in the system prompt, or only in other server-tool results are not sources; url_sources can disable or filter each source, and a filter naming a tool absent from tools fails the request; a URL that appears to contain a credential is refused unless that credential appears in the system prompt or a user message) - the model fetches a URL it invented, or a credential-bearing URL from a tool result is followed as if it were evidence")
    err=d.get("errors") or {}
    if not err.get("in_body_errors_handled"): f.append("WS-4 in-body errors are not handled (both tools return HTTP 200 with the error inside the body - search: too_many_requests, invalid_tool_input, max_uses_exceeded, query_too_long, request_too_large, unavailable; fetch: invalid_tool_input, url_too_long over 250 characters, url_not_allowed, url_not_in_prior_context, url_not_accessible, too_many_requests, unsupported_content_type for anything but text, HTML or PDF, content_too_large, max_uses_exceeded, unavailable; a successful search with no matches returns an empty content list, which is not an error) - a rate-limited or disallowed call is read as an empty result, and 'no results' is reported where the search never ran")
    if not err.get("pause_turn_handled"): f.append("WS-4 pause_turn is not handled (a long search or fetch turn can return stop_reason pause_turn - resend the paused assistant message unchanged to continue; when a server tool and a client tool are called in the same parallel group the API returns tool_use instead and runs the server tool after the client results arrive) - a paused research turn is abandoned as finished, or its partial state is edited and the continuation is invalid")
    if not err.get("cache_and_inclusion_decided"): f.append("WS-4 cache and response inclusion are not decided (fetch use_cache defaults to true - bypass it with false only when fresh content is explicitly required, because bypassing costs latency; response_inclusion excluded drops nested search and fetch blocks already consumed by a completed code execution call in agentic workflows, with token usage unaffected, while direct and paused calls always return full) - every fetch pays fresh-fetch latency by habit, or raw page content floods an agentic response nobody reads")
    eco=d.get("economics") or {}
    if not eco.get("search_pricing_accounted"): f.append("WS-5 search pricing is not accounted (web search costs $10 per 1,000 searches in addition to token costs; each search counts once regardless of result count; failed searches are not billed; search results count as input tokens both within the turn and in later turns that carry them) - a search-heavy loop's bill is its token line plus a per-search line nobody budgeted, and carried results keep billing on every later turn")
    if not eco.get("fetch_pricing_accounted"): f.append("WS-5 fetch pricing is not accounted (web fetch has no additional charge - only standard token costs for the fetched content: an average 10 kB page is about 2,500 tokens, a 100 kB documentation page about 25,000, a 500 kB research PDF about 125,000) - fetch is avoided as if it were billed per call while search is used as if it were free, inverting the actual price shape")
    if not eco.get("batch_throttling_accounted"): f.append("WS-5 batch behaviour is not accounted (both tools work in the Message Batches API at the same prices as Messages requests, and the Batches API throttles web search per organization to protect shared capacity, so large batches with many searches take longer) - a bulk research job is planned as if its searches run at interactive speed and its completion time is promised from the wrong model")
    return f
if __name__=="__main__":
    data=json.load(open(sys.argv[1])); fails=check(data)
    if fails:
        print(f"FAIL ({len(fails)}):")
        [print(" -",x) for x in fails]; sys.exit(1)
    print("PASS"); sys.exit(0)
