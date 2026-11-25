#!/usr/bin/env python3
"""prompting-check: deterministic gate for the PROMPTING BEST PRACTICES surface.
Stdlib only, offline, free. Canonical source (read in full 2026-11-20):
Anthropic Claude Platform Docs "Prompting best practices"
https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices (539 lines)
Key facts: prerequisites are success criteria + empirical evals + a first draft.
Be clear/direct/specific (format, constraints, sequential steps; colleague test);
give context/motivation; examples relevant+diverse+structured in <example> tags;
XML tags consistent/descriptive, nested for hierarchy; role in system prompt.
Long context (20k+): long data at TOP above query/instructions/examples, each doc
in <document> with <document_content>/<source>, ground answers in quotes first.
Format control: tell what TO do (not what not to do), XML format indicators,
match prompt style to desired output style. Tool use: explicit action language
("suggest" yields suggestions); Opus 4.5/4.6 overtrigger on aggressive MUST
language - soften; steer parallel tool calling explicitly (boost toward ~100%
or damp). Thinking: 4.6+ adaptive thinking, budget_tokens deprecated and a 400
on 4.7+ - control depth via effort; prefer general instructions ("think
thoroughly") over prescriptive step plans; multishot works with thinking; ask
for self-check except Opus 5 (over-verification - remove the instruction).
Prefill on last assistant turn unsupported from 4.6 - migrate away.
Agentic: multiwindow workflows (first window sets framework/tests, structured
tests.json, setup scripts, fresh-vs-compact choice, verification tools, state in
structured JSON + git + incremental progress); confirm before hard-to-reverse /
shared-system actions (Opus 4.6); subagents orchestrate natively - well-defined
tools, watch overuse (Opus 4.6/5 spawn for simple grep) and add damping guidance;
self-correction chaining (draft -> review -> refine) when intermediates must be
inspected. Model-specific page for your model comes FIRST.
"""
import json, sys
CHECKS = [
 ("PB-0a","decided"), ("PB-0b","owner_recorded"), ("PB-0c","canonical_record"),
 ("PB-1a","clear_direct_specific"), ("PB-1b","context_motivation_given"), ("PB-1c","examples_relevant_diverse_structured"),
 ("PB-2a","xml_tags_consistent_nested"), ("PB-2b","role_in_system_prompt"), ("PB-2c","long_context_top_quotes_first"),
 ("PB-3a","positive_format_instructions"), ("PB-3b","tool_direction_calibrated"), ("PB-3c","parallel_tool_calling_steered"),
 ("PB-4a","adaptive_thinking_migrated"), ("PB-4b","general_instructions_over_prescriptive"), ("PB-4c","self_check_calibrated"),
 ("PB-5a","prefill_migrated"), ("PB-5b","multiwindow_state_practices"), ("PB-5c","autonomy_safety_and_subagent_damping"),
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
