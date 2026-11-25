#!/usr/bin/env python3
"""task-budget-check: deterministic gate for the TASK BUDGETS surface.
Stdlib only, offline, free. Canonical source (read in full 2026-11-20):
Anthropic Claude Platform Docs "Task budgets"
https://platform.claude.com/docs/en/build-with-claude/task-budgets (236 lines)
Key facts: task_budget sits in output_config with beta header
task-budgets-2026-03-13; fields type="tokens", total, remaining (optional,
defaults to total). The server injects a countdown marker; the model paces
itself and finishes gracefully. The budget counts what Claude SEES that is
new this turn (thinking, tool calls, tool results, text) - resent history
is NOT recounted (worked example: 19,000 counted of a 100,000 budget while
~20,820 payload tokens were sent). A turn is everything in response to one
user message carrying NO tool results: such a message starts a fresh
budget; a message containing tool_result blocks (even alongside new
content) continues the turn. Server-side compaction during a turn does not
reset the budget; pre-turn tokens count only while earlier history remains
in context (the exclusion applies only across a server-side compaction).
For CLIENT-side compaction/rewriting, pass remaining on EVERY following
request, computed from removed messages only (leave out anything still
sent, incl. the summary); never decrement remaining on each request; for
full-history loops omit remaining and let the server track. Changing the
budget mid-conversation is allowed on the next request, but the value
participates in the rendered prompt, so a changed value misses cache
entries made under the old one. Advisory, NOT enforced: Claude may exceed
it mid-action; the hard limit is max_tokens (truncates, stop_reason
"max_tokens"). The two are independent - neither must be <= the other;
at xhigh/max effort set max_tokens >= 64k. Minimum total is 20,000 on every
supported model; smaller returns 400. Choose by measuring first: run a
representative sample WITHOUT a budget, sum usage.output_tokens across the
loop plus appended tool-result tokens, start from the p99. Effort is
complementary (effort = depth per step, budget = total breadth of work);
adaptive thinking tokens count and scale down as the budget depletes.
Caching: the countdown marker does not match across requests; mutating
remaining client-side invalidates any cache prefix containing it - set the
budget once on the initial request. Support (all Beta, header required):
Fable 5.2/5.1/5, Mythos 5.2/5.1/5, Opus 5.5/5/4.8/4.7, Sonnet 5.5, Haiku 5.5.
NOT supported: Sonnet 5, Opus 4.6, Sonnet 4.6, Haiku 4.5. Not supported on
Claude Code or Cowork surfaces; Messages API / Managed Agents only.
Distinct from: effort-check (depth per step), spend-limits-check (Console
dollar caps), usage-cost-check (reporting), context-window-check (window
accounting - task budgets appear there only as the fallback for models
without context awareness), compaction-check (summarization itself).
This gate is the advisory loop-wide pacing budget itself.
"""
import json, sys
CHECKS = [
 ("TB-0a","decided"), ("TB-0b","owner_recorded"), ("TB-0c","canonical_record"),
 ("TB-1a","setting_shape_and_beta_header"), ("TB-1b","countdown_marker_pacing"), ("TB-1c","counts_seen_new_only"),
 ("TB-2a","turn_definition_tool_result_boundary"), ("TB-2b","remaining_only_for_client_compaction"), ("TB-2c","mid_conversation_change_cache_cost"),
 ("TB-3a","advisory_not_enforced_max_tokens_hard"), ("TB-3b","independence_and_64k_floor"), ("TB-3c","minimum_20000_and_measure_first_p99"),
 ("TB-4a","effort_complementary_depth_vs_breadth"), ("TB-4b","adaptive_thinking_counts_scales_down"), ("TB-4c","caching_set_once_no_mutation"),
 ("TB-5a","supported_models_beta"), ("TB-5b","unsupported_models_guarded"), ("TB-5c","surface_limits_no_code_cowork"),
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
