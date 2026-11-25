#!/usr/bin/env python3
"""context-window-check: deterministic gate for the CONTEXT WINDOWS surface.
Stdlib only, offline, free. Canonical source (read in full 2026-11-20):
Anthropic Claude Platform Docs "Context windows"
https://platform.claude.com/docs/en/build-with-claude/context-windows (178 lines)
Key facts: everything in the request counts (system prompt, every message
incl. tool results/images/documents, tool definitions) plus the output incl.
extended thinking; usage reports consumption, and with prompt caching the
input count splits across input_tokens / cache_read_input_tokens /
cache_creation_input_tokens - all three count. Estimate first with the token
counting API. Sizes: Fable 5.2/5.1/5, Mythos 5.2/5.1/5/Preview, Opus
5.5/5/4.8/4.7/4.6, Sonnet 5.5/5/4.6, Haiku 5.5 = 1M (max output 128k);
others incl. Sonnet 4.5 (deprecated) = 200k. 1M is default, no beta header,
standard pricing except Haiku 5.5 prompts over 100k cost more. Media cap:
600 images/PDF pages (100 on 200k models); request size limits may hit first.
Thinking tokens are a subset of max_tokens, billed as output, count toward
rate limits; adaptive allocation varies. Previous thinking blocks are KEPT by
default on Opus 4.5+, Sonnet 4.6+, Haiku 5.5, Fable, Mythos; STRIPPED
automatically on earlier Opus/Sonnet and Haiku through 4.5; override via
thinking block clearing. Kept blocks are billed once as output, then as input
on later turns. In a tool cycle, return the entire unmodified thinking block
with its signature. Context awareness (auto-injected budget tags, never send
them yourself): Sonnet 5, Sonnet 4.6, Sonnet 4.5, Haiku 4.5 only; Opus 4.7+,
Sonnet 5.5, Fable, Mythos, Haiku 5.5 do NOT get the tags - use task budgets
(beta) instead. More context is not automatically better: context rot means
curation matters as much as capacity. Management: server-side compaction is
the primary strategy for long-running work; context editing (tool-result
clearing, thinking clearing) for specialized needs; cached prefixes still
occupy the window. Overflow: input alone over the window = 400
invalid_request_error ("prompt is too long") on every model; on 4.5+ models,
input + max_tokens over the window is ACCEPTED and generation stops with
stop_reason "model_context_window_exceeded"; earlier models return a
validation error unless the model-context-window-exceeded-2025-08-26 beta
header opts in.
Distinct from: compaction-check (summarization itself), context-editing-check
(clearing itself), context-engineering-check (curation strategy),
token-counting-check (the counting API itself), thinking-check (thinking
configuration). This gate is the window accounting itself: what counts, how
big it is per model, how thinking/media/cache consume it, who tracks the
budget, and what happens at overflow.
"""
import json, sys
CHECKS = [
 ("CW-0a","decided"), ("CW-0b","owner_recorded"), ("CW-0c","canonical_record"),
 ("CW-1a","everything_counts"), ("CW-1b","usage_and_cache_split_read"), ("CW-1c","preflight_token_counting"),
 ("CW-2a","size_by_model_known"), ("CW-2b","default_1m_pricing_nuance"), ("CW-2c","media_and_request_size_limits"),
 ("CW-3a","thinking_counts_subset_billing"), ("CW-3b","thinking_preservation_by_model"), ("CW-3c","thinking_tool_cycle_and_rebilling"),
 ("CW-4a","context_awareness_models_known"), ("CW-4b","context_awareness_absent_task_budgets"), ("CW-4c","context_rot_curation"),
 ("CW-5a","overflow_input_alone_400"), ("CW-5b","overflow_generation_stop_behavior"), ("CW-5c","management_stack_recorded"),
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
