#!/usr/bin/env python3
"""tool-search-check: deterministic gate for the Tool Search surface
(how a large tool catalog is discovered and loaded on demand instead of
every definition being loaded into context up front - defer_loading
partition, variant and model compatibility, discoverability of names and
descriptions, continuation shape, fit and measured context savings, and
the cache / error / MCP constraints - is decided, not left to habit).
Stdlib only, offline.
Canonical source (read in full 2026-11-19):
- Anthropic Claude Platform Docs "Tool search tool"
  https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-search-tool
  (287 lines read in full): Claude works with hundreds or thousands of
  tools by searching the catalog (names, descriptions, argument names and
  argument descriptions) and loading only what it needs. Loading every
  definition up front causes context bloat (a typical multi-server setup
  - GitHub, Slack, Sentry, Grafana, Splunk - can consume about 55k tokens
  in definitions before any work; tool search typically reduces this by
  over 85 percent, loading only the 3-5 tools needed) and degrades tool
  selection accuracy once available tools exceed roughly 30-50. Two
  server-side variants: tool_search_tool_regex_20251119 (Claude builds
  regex patterns, Python re.search syntax) and
  tool_search_tool_bm25_20251119 (natural-language queries). The current
  compatibility table lists both variants across the current model line
  including Haiku 4.5; Opus 4.1 and earlier do not support tool search.
  Mechanics: include one search tool in the tools list, send EVERY tool
  definition in the tools array on every request, and set
  defer_loading: true on tools that should not load up front; at least
  one tool - normally the search tool itself - must stay non-deferred,
  and the search tool itself is never deferred. defer_loading controls
  what enters context, not what is sent: deferred definitions are
  excluded from the system-prompt prefix server-side, discovered tools
  arrive as tool_reference blocks that the API expands into full
  definitions inline; the strict-mode grammar builds from the full tool
  list, so deferral does not recompile it. Keep the 3-5 most frequently
  used tools non-deferred. Computer / browser toolsets take defer_loading
  per member inside configs (entry-level is rejected) and the value must
  resolve identically on every enabled member, because the toolset
  expands as a unit. Response shape: server_tool_use carries the search
  (pattern for regex, query for BM25, optional limit 1-10000, default 5
  results); NEVER return a tool_result for its srvtoolu_... ID - the API
  rejects the request. tool_search_tool_result blocks are kept in history
  unchanged; on the next request pass the assistant content back
  unchanged, add the tool_result for the discovered tool, and resend the
  same tools array. A search matching nothing returns an empty
  tool_references array, NOT an error, and discovered tools stay expanded
  through history so later turns reuse them without re-searching.
  Discoverability: both variants search names, descriptions, argument
  names and argument descriptions - write clear descriptive names, use
  consistent namespacing prefixes (github_, slack_) so one search matches
  a whole group, put keywords in descriptions that match how users
  describe tasks, add a system-prompt section naming the available tool
  categories, and monitor which tools Claude discovers to refine
  descriptions. MCP: with the MCP connector, defer_loading is set once on
  the mcp_toolset entry's default_config or per tool in configs, not on
  individual definitions. Custom search: an own search tool (for example
  embeddings) returns a normal tool_result whose content holds
  tool_reference blocks; every referenced tool must have a definition in
  the top-level tools parameter, normally deferred. Errors: HTTP 400 for
  all tools deferred and for a missing tool definition; execution
  failures return HTTP 200 with error_code invalid_tool_input (malformed
  regex or pattern over the 200-character limit), unavailable (timeout or
  service unavailable - a search timeout is reported as unavailable,
  never execution_time_exceeded), or too_many_requests. Prompt caching: a
  deferred tool cannot also carry cache_control (400) - put the cache
  breakpoint on a non-deferred tool. Limits: at most 10,000 deferred
  tools per request; each search returns up to 5 by default, limit is any
  integer 1-10000; regex patterns at most 200 characters, BM25 queries at
  most 500. Fit: use tool search at 10+ tools, definitions over 10k
  tokens, selection accuracy dropping as tools are added, aggregating
  multiple MCP servers (200+ tools), or a growing library; standard
  calling fits fewer than 10 tools, every tool used in every request, or
  definitions under 100 tokens total. Usage: tool search is not metered
  as a separate server tool (usage.server_tool_use has no tool-search
  field); definitions that search loads into context count as input
  tokens like any other definition. Tool search also works streamed and
  in Message Batches.
Exit 0=PASS, 1=FAIL.
"""
import json, sys
def check(d):
    f=[]
    dec=d.get("decision") or {}
    if not dec.get("decision_recorded"): f.append("TS-0 the Tool Search surface is not recorded as a decided surface - which tools load up front and which are discovered on demand is left to each request and habit, not a decision")
    if not dec.get("owner_recorded"): f.append("TS-0 no owner is recorded for tool-search correctness (deferral partition, discoverability, measured context savings) - a catalog that silently bloats context, or a tool Claude can never find, has no accountable reader")
    if not dec.get("catalog_inventoried"): f.append("TS-0 there is no inventory of the tool catalog (every tool, its token cost as a definition, and whether it is deferred or always loaded) - bloat and selection failure cannot be required where the catalog itself is uncounted")
    en=d.get("enablement") or {}
    if not en.get("variant_and_model_checked"): f.append("TS-1 the search variant and model support are not decided and checked (regex tool_search_tool_regex_20251119 builds Python re.search patterns; BM25 tool_search_tool_bm25_20251119 takes natural-language queries; the compatibility table must be read for the exact model - Opus 4.1 and earlier do not support tool search) - a request is built on a variant or model that cannot run it")
    if not en.get("deferral_partition_decided"): f.append("TS-1 the deferral partition is not decided (the search tool itself is never deferred, at least one tool must stay non-deferred or the request is a 400, and the 3-5 most frequently used tools stay non-deferred so they are callable without searching first) - either everything loads up front and the feature does nothing, or the always-needed tools pay a search round trip on every task")
    if not en.get("definitions_sent_in_full"): f.append("TS-1 it is not fixed that every tool definition is still sent in the tools array on every request, deferred ones included (defer_loading controls what enters context, not what is sent; the API needs the full definitions server-side to search and to expand tool_reference blocks, and computer / browser toolsets take defer_loading per member in configs - identical on every enabled member - never at entry level) - a deferred tool that was trimmed from the request can never be discovered or expanded")
    di=d.get("discoverability") or {}
    if not di.get("naming_and_descriptions_decided"): f.append("TS-2 tool names and descriptions are not written for search (both variants search names, descriptions, argument names and argument descriptions; names must be clear and descriptively namespaced with consistent service prefixes such as github_ or slack_ so one search matches a whole group, and descriptions must carry the keywords users actually use for the task) - a tool that exists but cannot be found by its own description is a tool the catalog does not have")
    if not di.get("category_prompt_decided"): f.append("TS-2 the system prompt does not name the available tool categories (a short section such as 'you can search for tools to interact with Slack, GitHub, and Jira' is what tells Claude a deferred capability exists at all) - Claude answers from the always-loaded set and never searches for the rest")
    if not di.get("discovery_monitored"): f.append("TS-2 discovered-tool usage is not monitored (watching which tools Claude actually discovers is the feedback loop that refines names and descriptions) - a systematically undiscoverable tool stays undiscoverable and is misread as a capability the model lacks")
    ct=d.get("continuation") or {}
    if not ct.get("history_preserved"): f.append("TS-3 the search history is not preserved verbatim (the assistant content - server_tool_use and tool_search_tool_result blocks included - is passed back unchanged, the same tools array is resent, and the API keeps expanding tool_reference blocks through history so discovered tools are reused in later turns without re-searching) - rewriting or dropping the search blocks breaks expansion or pays the search again every turn")
    if not ct.get("srvtoolu_never_answered"): f.append("TS-3 the srvtoolu_ rule is not fixed (never return a tool_result for the search call's srvtoolu_... ID - the search runs on Anthropic's servers and the API rejects a request that answers it; only the discovered tool's call gets a tool_result, exactly as in standard tool use) - one well-meant result block takes down the whole continuation")
    if not ct.get("empty_result_handled"): f.append("TS-3 an empty search result is not handled as a no-match (a search that matches nothing returns a tool_search_tool_search_result with an empty tool_references array, not an error) - a legitimate 'no such tool' is debugged as a failure, or papered over by inventing a call to a tool that was never loaded")
    ft=d.get("fit") or {}
    if not ft.get("fit_decided"): f.append("TS-4 the fit is not decided (use tool search at 10 or more tools, definitions over 10k tokens, selection accuracy dropping as tools are added - it degrades past roughly 30-50 available tools - aggregating multiple MCP servers, or a growing library; standard calling fits fewer than 10 tools, every tool used in every request, or under 100 definition tokens total) - deferral overhead is paid where it buys nothing, or withheld where definition bloat is the dominant cost")
    if not ft.get("context_measured"): f.append("TS-4 the context saving is not measured on this catalog (the reference setup - GitHub, Slack, Sentry, Grafana, Splunk - spends about 55k tokens on definitions before any work, and tool search typically cuts that by over 85 percent by loading only the 3-5 tools a request needs) - the feature is adopted or rejected on the headline percentage instead of this catalog's own definition-token count before and after")
    if not ft.get("limits_respected"): f.append("TS-4 the catalog limits are not respected (at most 10,000 deferred tools per request; each search returns up to 5 tools by default and limit may be set to any integer from 1 to 10,000; regex patterns are capped at 200 characters and BM25 queries at 500) - a search is sized as if it returned the whole catalog, or a long pattern fails as invalid input mid-task")
    cs=d.get("constraints") or {}
    if not cs.get("cache_control_separated"): f.append("TS-5 cache_control is not kept off deferred tools (a tool with defer_loading: true cannot also carry cache_control - the API returns a 400; the cache breakpoint goes on a non-deferred tool, and because deferred tools are excluded from the system-prompt prefix, deferral itself preserves the cache instead of recompiling it) - a caching habit applied uniformly breaks every request that defers that tool")
    if not cs.get("errors_read"): f.append("TS-5 the two error surfaces are not read apart (HTTP 400 stops the request - all tools deferred, or a tool_reference with no matching definition; execution failures arrive as HTTP 200 with error_code invalid_tool_input, unavailable - which is also how a search timeout is reported - or too_many_requests) - a rate limit or a malformed pattern is debugged as a model failure, or a 400 is retried as if it were transient")
    if not cs.get("mcp_and_custom_decided"): f.append("TS-5 the MCP and custom-search shapes are not decided (MCP deferral is set once on the mcp_toolset entry's default_config or per tool in configs, not on individual definitions; a custom search tool returns tool_reference blocks inside a normal tool_result and every referenced tool must be defined in the top-level tools parameter; usage is not metered separately - definitions loaded by search count as ordinary input tokens) - MCP tools are deferred in a place the API ignores, a custom reference points at an undefined tool, or search is budgeted as a priced server tool it is not")
    return f
if __name__=="__main__":
    data=json.load(open(sys.argv[1])); fails=check(data)
    if fails:
        print(f"FAIL ({len(fails)}):")
        [print(" -",x) for x in fails]; sys.exit(1)
    print("PASS"); sys.exit(0)
