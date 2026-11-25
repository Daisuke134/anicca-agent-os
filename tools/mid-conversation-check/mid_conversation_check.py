#!/usr/bin/env python3
"""mid-conversation-check: deterministic gate for the MID-CONVERSATION SYSTEM MESSAGES surface.
Stdlib only, offline, free. Canonical source (read in full 2026-11-19):
Anthropic Claude Platform Docs "Mid-conversation system messages and tool changes"
https://platform.claude.com/docs/en/build-with-claude/mid-conversation-system-messages
Key facts: appending {"role":"system"} mid-conversation preserves the cached prefix
(hash order tools -> system -> messages); editing top-level system or tools invalidates it.
Content-carrying system messages must follow a user turn (or assistant ending in server
tool result), must end messages or be followed by an assistant turn, cannot be first.
Turn-scoped clear_at="next_user_message" needs beta mid-conversation-system-clear-at-2026-08-21,
is text-only (no tool blocks / output_config / cache_control), cleared copies are resent verbatim.
Tool changes via tool_addition/tool_removal blocks (beta inline-tools-2026-09-15 /
mid-conversation-tool-changes-2026-07-01); full set declared up front; at least one
non-deferred tool unless the inline exception applies; limits 10,000 tools / 4MB.
Never place untrusted content (tool output, retrieved docs, web) in a system message.
Sonnet 5.5 / Haiku 5.5: relay user words as a text block in the user turn, not in system.
Exit 0 = all pass, 1 = any fail. null/unverified counts as fail (recorded as such)."""
import json, sys
def check(d):
    r = {}
    r["MCS-0a_surface_decided"] = d.get("decided") is True and bool(d.get("owner")) and bool(d.get("source"))
    r["MCS-0b_mid_discovery_use"] = d.get("used_for_mid_session_instructions") is True
    r["MCS-0c_toplevel_reserved"] = d.get("top_level_reserved_for_whole_conversation") is True
    r["MCS-1a_placement_follows"] = d.get("follows_user_or_server_tool_assistant") is True
    r["MCS-1b_placement_ends"] = d.get("ends_or_followed_by_assistant") is True and d.get("is_first_message") is False
    r["MCS-1c_phrasing_and_relay"] = d.get("phrased_as_fact_not_override") is True and d.get("relay_only_own_user_input") is True
    r["MCS-2a_caching_enabled"] = d.get("caching_explicitly_enabled") is True
    r["MCS-2b_after_breakpoint"] = d.get("appended_after_breakpoint") is True
    r["MCS-2c_append_not_edit"] = d.get("never_edit_or_remove_sent_system") is True and d.get("evolve_by_appending_new") is True
    r["MCS-3a_clearat_beta_header"] = d.get("clear_at_beta_header_sent") is True
    r["MCS-3b_turnscoped_text_only"] = d.get("turn_scoped_text_only") is True and d.get("turn_scoped_no_cache_control") is True
    r["MCS-3c_cleared_resent_verbatim"] = d.get("cleared_resent_verbatim") is True
    r["MCS-4a_full_set_upfront"] = d.get("full_tool_set_declared_upfront") is True
    r["MCS-4b_changes_via_blocks_beta"] = d.get("tool_changes_via_system_blocks") is True and d.get("tool_change_beta_header_sent") is True
    r["MCS-4c_nondeferred_and_limits"] = d.get("at_least_one_non_deferred_or_inline_exception") is True and d.get("tool_limits_respected") is True
    r["MCS-5a_no_untrusted_in_system"] = d.get("no_untrusted_content_in_system") is True
    r["MCS-5b_model_supported_checked"] = d.get("model_support_checked_before_use") is True
    r["MCS-5c_sonnet_haiku_relay_exception"] = d.get("sonnet55_haiku55_relay_in_user_turn") is True
    r["pass_count"] = sum(1 for v in r.values() if v is True)
    r["fail_count"] = sum(1 for v in r.values() if v is False)
    r["pass"] = r["fail_count"] == 0
    return r
if __name__ == "__main__":
    v = check(json.load(open(sys.argv[1])))
    print(json.dumps(v, indent=2)); sys.exit(0 if v["pass"] else 1)
