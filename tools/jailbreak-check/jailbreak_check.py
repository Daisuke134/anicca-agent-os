#!/usr/bin/env python3
"""jailbreak-check: deterministic gate for the JAILBREAK / PROMPT-INJECTION defense surface.
Stdlib only, offline, free. Canonical source (read in full 2026-11-20):
Anthropic Claude Platform Docs "Mitigate jailbreaks and prompt injections"
https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/mitigate-jailbreaks (77 lines)
Key facts: two threat models - (1) jailbreaks/direct injection, user is adversary;
(2) indirect injection, user trusted but third-party content (webpages, emails,
documents, tool results) carries adversarial instructions. Direct defenses:
harmlessness screens with a lightweight model (Claude Haiku 5.5) using structured
outputs for a parseable classification, and a screen response with
stop_reason "refusal" must be treated as a HARMFUL verdict (the screener's own
safety classifiers can decline); input validation filtering known injection
patterns (an LLM can generalize from known jailbreak examples); prompt
engineering that states ethical/legal boundaries and how to refuse; respond to
repeat offenders (throttle/ban, tell them they violate usage policies).
Indirect defenses: untrusted content ONLY in tool_result blocks, never in system
prompts or plain user text blocks (Claude is trained to treat tool-result
instructions with skepticism); label what the content is and where it came from
(tool description / result structure); state in the system prompt that tool /
document / search content is untrusted data and must never override the system
prompt or the user's original request; JSON-encode untrusted strings so escaping
gives unambiguous delimiters (attacker cannot break out by closing a quote/tag);
do NOT put your own instructions in tool results (they may be ignored/flagged) -
send them in a following user turn or a mid-conversation system message; least
privilege (no unneeded secrets, sandboxed tools, narrow permissions); screen tool
OUTPUTS with the same lightweight-model pattern before Claude acts, returning
content as tool_result only if the screen reports no injection, verdict via
structured outputs so the app can branch; red-team your own agent before deploy
with documents/emails/tool outputs containing deliberate injections; continuous
monitoring of outputs for successful injection, iterating prompts/validation/
filtering; advanced: chain/layer safeguards (enterprise-grade defense in depth).
"""
import json, sys
CHECKS = [
 ("JB-0a","decided"), ("JB-0b","owner_recorded"), ("JB-0c","canonical_record"),
 ("JB-1a","prescreen_lightweight_structured"), ("JB-1b","screen_refusal_is_harmful"), ("JB-1c","input_validation_patterns"),
 ("JB-2a","system_prompt_refusal_policy"), ("JB-2b","repeat_offender_response"), ("JB-2c","output_monitoring_loop"),
 ("JB-3a","untrusted_only_tool_results"), ("JB-3b","source_labeling"), ("JB-3c","system_prompt_untrusted_policy"),
 ("JB-4a","json_encode_untrusted"), ("JB-4b","own_instructions_not_in_tool_results"), ("JB-4c","least_privilege_sandbox"),
 ("JB-5a","screen_tool_outputs"), ("JB-5b","redteam_before_deploy"), ("JB-5c","chain_layered_defense"),
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
