#!/usr/bin/env python3
"""search-results-check: deterministic gate for the SEARCH RESULTS surface
(how retrieved own content is handed to the model as citable
search_result blocks - schema, delivery method, citation control,
block granularity, tool-result purity, error shape - is decided,
not pasted into prompts as unattributed plain text).
Stdlib only, offline, free.
Canonical source (read in full 2026-11-20):
Anthropic Claude Platform Docs "Search results"
https://platform.claude.com/docs/en/build-with-claude/search-results (223 lines)
Key facts: search_result content blocks let Claude cite your own content
the same way it cites web search results, for RAG. Two delivery methods:
(1) from tool calls - custom tools return search results (dynamic RAG;
force the call with tool_choice so retrieval runs every time);
(2) as top-level content in user messages (pre-fetched, cached,
external search services, testing). Schema required fields:
type="search_result", source (any stable string - a URL or an internal
identifier such as kb://article-1234), title, content (array of text
blocks; each item type="text" with a non-empty text string). Text only
inside content - images and other media are not supported there.
Optional: citations {enabled} (DISABLED by default; set true explicitly;
ALL search results in a request must use the same setting) and
cache_control (e.g. {"type": "ephemeral"}) sitting alongside citations
on the same block. Citations are automatic when enabled - no special
prompting - but a prompt asking for only JSON may yield few or no
citations. Response citations: type is always "search_result_location",
with source, title (string or null), cited_text (the full text of the
cited block slice content[start_block_index:end_block_index] joined;
NOT counted toward output tokens), search_result_index (0-based across
all search_result blocks in the request, in appearance order across
messages and tool results), start_block_index, and end_block_index
(exclusive, always greater than start). The text block is the minimal
citable unit: Claude cites whole blocks, not substrings, so split
content into smaller focused blocks for finer citation boundaries;
one combined block means every citation returns the full text.
Mixing: both methods can be mixed in one conversation and the index
counts all blocks in request order. In user messages search_result
blocks can sit alongside any other content block (text, image,
document). Tool results are stricter: if any block in a tool_result
content array is a search_result, ALL of its blocks must be
search_result - mixing returns a validation error; supporting text
goes inside a search result's content array, where it also becomes
citable. Errors: when a search fails or returns nothing, return a
plain text block describing the outcome (e.g. "No results found.")
instead of raising an error, so Claude explains it and the
conversation continues. Result limits: return only the most relevant
results to avoid context overflow. Best practice: clear permanent
source URLs, descriptive titles that accurately reflect content,
consistent source formats and formatting, break long content into
logical blocks. Limitations: search_result blocks can appear ONLY in
user messages (including inside tool results); assistant messages
carrying them are rejected. When the web search tool is enabled in
the same request, citations must be enabled on ALL search_result
blocks. Availability: Messages API and Managed Agents, all models.
Distinct from: citations-check (the Citations feature over documents -
same whole-block model for custom content documents, different input
surface), web-tools-check (the web search tool itself - here your own
retrieved content is the source), prompt-caching-check (caching itself;
here only where cache_control sits), structured-output-check (a
JSON-only prompt can starve citations - the structured-data-with-
citations pattern is a separate page, not asserted here).
"""
import json, sys
CHECKS = [
 ("SR-0a","decided"), ("SR-0b","owner_recorded"), ("SR-0c","canonical_record"),
 ("SR-1a","schema_required_fields"), ("SR-1b","content_text_blocks_nonempty_text_only"), ("SR-1c","stable_source_and_accurate_title"),
 ("SR-2a","two_delivery_methods_chosen"), ("SR-2b","tool_result_all_search_result_purity"), ("SR-2c","user_messages_only_assistant_rejected"),
 ("SR-3a","citations_enabled_explicitly_default_off"), ("SR-3b","same_citations_setting_all_results"), ("SR-3c","web_search_tool_requires_citations_all"),
 ("SR-4a","citation_fields_and_index_semantics"), ("SR-4b","whole_block_minimal_unit_split_for_granularity"), ("SR-4c","cited_text_free_and_slice_definition"),
 ("SR-5a","failure_returns_plain_text_block"), ("SR-5b","result_limits_relevance_and_consistency"), ("SR-5c","cache_control_on_block_and_json_prompt_caveat"),
]
def main(path):
    d = json.load(open(path))
    fails = [cid for cid, key in CHECKS if d.get(key) is not True]
    for cid, key in CHECKS:
        print(f"{'PASS' if d.get(key) is True else 'FAIL'} {cid} {key}")
    print(f"TOTAL {len(CHECKS)-len(fails)}/{len(CHECKS)} pass, {len(fails)} fail")
    return 1 if fails else 0
if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
