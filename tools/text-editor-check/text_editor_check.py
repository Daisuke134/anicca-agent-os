#!/usr/bin/env python3
"""text-editor-check: deterministic gate for the TEXT EDITOR TOOL surface
(how file view/edit commands Claude requests are executed by the
application - exact-match replace, path safety, backups, truncation and
cost - is decided, not improvised per call site).
Stdlib only, offline.
Canonical source (read in full 2026-11-19):
- Anthropic Claude Platform Docs "Text editor tool"
  https://platform.claude.com/docs/en/agents-and-tools/tool-use/text-editor-tool
  (252 lines read in full): the tool is named str_replace_based_edit_tool,
  schema-less (schema built into the model, cannot be modified), type
  text_editor_20250728 for Claude 4 and later. Commands: view (file
  contents or directory listing; view_range is 1-indexed, -1 end means
  to end of file, files only not directories), str_replace (old_str must
  match exactly including whitespace and indentation), create (path +
  file_text), insert (insert_line = line AFTER which to insert, 0 =
  beginning of file). Optional max_characters controls truncation when
  viewing large files. Flow: Claude issues tool_use, the application
  runs the command and returns a tool_result in a new user message.
  Implementation guidance: build helper functions for the file
  operations and consider backup functionality to recover from mistakes.
  Security: validate file paths to prevent directory traversal, create
  backups before making changes, handle errors gracefully, implement
  permissions checks. Pricing: definition adds 974 input tokens on
  Claude 4.7 and later / Mythos Preview, 745 on 4.6 and earlier (type
  text_editor_20250728), plus the tokens of viewed/edited content.
  Combining tools: match the tool version with the model and account
  for the additional token usage of ALL tools in the request. Changelog:
  20250728 adds max_characters, otherwise identical to 20250429;
  20250429 REMOVED the undo_edit command (recovery is backups, not an
  undo command); 20250124 was the Sonnet 3.7 standalone; 20241022 was
  the initial release with undo_edit for the retired Sonnet 3.5.
Separation: this surface is NOT the bash tool (gated 2026-11-19 17:07,
shell commands in a persistent session) - here there is no shell at
all, only four structured file commands the application executes.
Exit 0=PASS, 1=FAIL.
"""
import json, sys
def check(d):
    f=[]
    dec=d.get("decision") or {}
    if not dec.get("decision_recorded"): f.append("TE-0 the text editor tool surface is not recorded as a decided surface - each call site decides for itself whether Claude edits files through this tool, through a shell, or not at all")
    if not dec.get("owner_recorded"): f.append("TE-0 no owner is recorded for the text editor tool surface (command execution, path safety, backups) - a bad edit has no accountable reader")
    if not dec.get("surfaces_inventoried"): f.append("TE-0 the surfaces that can request file edits are not inventoried (which agents/products use the text editor tool, which use bash, which get no file writes) - an uninventoried write surface is an unowned mutation path")
    cmd=d.get("commands") or {}
    if not cmd.get("all_four_commands_implemented"): f.append("TE-1 not all four commands are implemented (view, str_replace, create, insert) - a partial implementation makes Claude plan edits around commands that silently do not exist")
    if not cmd.get("view_range_semantics_correct"): f.append("TE-1 view_range semantics are not the source form (1-indexed start/end, -1 end reads to end of file, applies to files only not directories; view of a directory lists its contents) - off-by-one or directory-range handling corrupts what the model thinks it saw")
    if not cmd.get("str_replace_requires_exact_match"): f.append("TE-1 str_replace does not require old_str to match exactly, including whitespace and indentation - a fuzzy replace edits a location the model never named")
    saf=d.get("safety") or {}
    if not saf.get("paths_validated_against_traversal"): f.append("TE-2 file paths are not validated to prevent directory traversal - the editor is a write primitive, and an unvalidated path turns a prompt into a write anywhere the process can reach")
    if not saf.get("backups_created_before_changes"): f.append("TE-2 backups are not created before making changes (the source names backup functionality as the way to recover from mistakes) - since 20250429 there is no undo_edit command, so an edit without a backup has no recovery path at all")
    if not saf.get("permissions_checked"): f.append("TE-2 permissions are not checked before executing an edit command - a tool that writes wherever it is pointed, without a permission check, inherits every confused-deputy failure of the caller")
    loop=d.get("execution_loop") or {}
    if not loop.get("errors_handled_gracefully"): f.append("TE-3 errors are not handled gracefully and returned as tool_result errors (no-match, missing file, invalid range) - a crashed handler ends the turn instead of letting the model correct the edit it attempted")
    if not loop.get("max_characters_truncation_configured"): f.append("TE-3 max_characters is not configured for viewing large files (the 20250728 parameter exists precisely to control truncation) - one view of a large file can flood the context the edit depends on")
    if not loop.get("results_returned_as_tool_result"): f.append("TE-3 command results are not returned to Claude as a tool_result in a new user message continuing the conversation - results delivered any other way break the request/response contract the tool is defined over")
    ver=d.get("version_and_pairing") or {}
    if not ver.get("current_version_pinned"): f.append("TE-4 the tool version is not pinned to the current text_editor_20250728 for Claude 4 and later (schema-less; the schema is built into the model and cannot be modified) - an old pin (20250429 without max_characters, 20250124, retired 20241022) silently changes what the surface supports")
    if not ver.get("version_matched_to_model"): f.append("TE-4 the tool version is not matched to the model in use (the source: when combining tools, match the tool version with the model) - a version/model mismatch is a contract the model was never trained on")
    if not ver.get("no_undo_edit_assumption"): f.append("TE-4 the design still assumes an undo_edit command exists (removed in text_editor_20250429 and absent from 20250728) - recovery planned around a removed command is recovery that is not there when a bad edit lands")
    cost=d.get("cost") or {}
    if not cost.get("token_cost_counted"): f.append("TE-5 the text editor tool's token cost is not counted (definition adds 974 input tokens on Claude 4.7 and later, 745 on 4.6 and earlier, PLUS the tokens of viewed file contents and edit payloads) - file views are paid input, and a surface that does not count them cannot price a run")
    if not cost.get("combined_tool_cost_accounted"): f.append("TE-5 the additional token usage of ALL tools combined in a request is not accounted for (editor + bash + others stack per request) - pricing one tool at a time understates every multi-tool request")
    if not cost.get("reverified_on_model_change"): f.append("TE-5 version, pricing and limits are not re-verified when the model changes (the token add-on differs by model generation, 974 vs 745) - a model swap silently changes what the same editor surface costs")
    return f
if __name__=="__main__":
    data=json.load(open(sys.argv[1])); fails=check(data)
    if fails:
        print(f"FAIL ({len(fails)}):")
        [print(" -",x) for x in fails]; sys.exit(1)
    print("PASS"); sys.exit(0)
