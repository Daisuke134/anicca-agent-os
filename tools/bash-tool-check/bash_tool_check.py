#!/usr/bin/env python3
"""bash-tool-check: deterministic gate for the CLIENT BASH TOOL surface
(how shell commands Claude requests are executed in an application-owned
persistent session - who owns the session, the timeout and the safety
checks - is decided, not improvised per call site).
Stdlib only, offline.
Canonical source (read in full 2026-11-19):
- Anthropic Claude Platform Docs "Bash tool"
  https://platform.claude.com/docs/en/agents-and-tools/tool-use/bash-tool
  (215 lines read in full): the bash tool is a CLIENT tool - Claude does
  not run commands; it returns a tool_use block naming the command, the
  application runs it in a bash session it owns and returns stdout and
  stderr together in a tool_result. One bash process stays alive across
  calls so working directory, environment variables and created files
  persist. The API is stateless: nothing about the session travels
  between requests, so the application determines when the session
  starts, how long it lives and when to restart it. restart:true kills
  the shell and starts clean (cwd, env, processes gone) and the result
  must confirm the restart. Several tool_use blocks in one response run
  in order in the same session, results returned in one user message.
  Definition is schema-less: only type and name (name must be "bash");
  current version bash_20250124, no beta header, every model from
  Sonnet 3.7 onward; bash_20241022 works only with the retired Oct 2024
  Sonnet 3.5 and needs the computer-use beta header. Implementation:
  a sentinel line marks where each command's output ends in the live
  pipe; a complete implementation also needs a timeout that kills the
  shell and every process it started when a command hangs, then
  restarts the session. Safety example is a tripwire, not a boundary:
  an allowlist beats a blocklist, the spaced-operator check does not
  catch an operator glued to a word (cat data.txt|grep x), and the real
  control is isolation - run the whole session inside a container or
  VM. Security beyond isolation: validate with an allowlist, set
  resource limits (CPU/memory/disk, e.g. ulimit), log every command and
  its output for audit, redact credentials and secrets from output
  before returning it. Errors: return the message as tool_result with
  is_error:true. Pricing: the definition adds 325 input tokens on
  Claude 4.7 and later (244 on 4.6 and earlier), plus the tokens of
  command outputs, error messages and large file contents. Limits:
  no interactive commands (vim, less, password prompts, anything
  waiting on stdin), no GUI, output is not truncated by the API (an
  oversized request is rejected - truncate in the application before
  returning), and there is no streaming (output reaches Claude only
  with the next request's tool_result). Pairs with the text editor
  tool.
Separation: this surface is NOT the server-side code execution tool
(Anthropic's own sandboxed container, gated 2026-11-19 08:07) - here
execution, persistence and safety all live in OUR application.
Exit 0=PASS, 1=FAIL.
"""
import json, sys
def check(d):
    f=[]
    dec=d.get("decision") or {}
    if not dec.get("decision_recorded"): f.append("BA-0 the client bash tool surface is not recorded as a decided surface - each call site decides for itself whether Claude gets a shell, and through which tool (client bash vs server code execution vs none)")
    if not dec.get("owner_recorded"): f.append("BA-0 no owner is recorded for the bash tool surface (session ownership, timeout, safety checks) - a hung or unsafe shell has no accountable reader")
    if not dec.get("surfaces_inventoried"): f.append("BA-0 the surfaces that can request shell execution are not inventoried (which agents/products use client bash, which use server code execution, which get no shell) - an uninventoried shell surface is an unowned execution path")
    ses=d.get("session") or {}
    if not ses.get("persistent_session_owned"): f.append("BA-1 no single long-lived bash process is owned across calls (the source form: state - cwd, env vars, created files - persists between commands) - a fresh shell per call silently breaks the multistep workflows the tool is for")
    if not ses.get("restart_handled"): f.append("BA-1 restart:true is not handled as specified (kill the shell, start a new one, return a tool_result confirming the restart; a restarted session starts clean) - without it a poisoned or hung session can only be abandoned, not recovered in-protocol")
    if not ses.get("session_lifecycle_owned_client_side"): f.append("BA-1 session lifecycle is not recorded as client-owned (the API is stateless; the application determines when the session starts, how long it lives and when to restart it) - a design that expects the API to remember the shell will lose state it never owned")
    loop=d.get("execution_loop") or {}
    if not loop.get("stdout_stderr_returned_together"): f.append("BA-2 command output is not returned as stdout and stderr together in the tool_result (errors must land where they occurred in the output) - separated or dropped stderr hides the failure the next command depends on")
    if not loop.get("errors_returned_with_is_error"): f.append("BA-2 failures are not returned with is_error:true and the message as the tool_result content - a failed command reported as success output teaches the model to build on a step that never ran")
    if not loop.get("large_output_truncated_by_app"): f.append("BA-2 large outputs are not truncated in the application before returning them (the API does not truncate tool results; an oversized request is rejected) - one cat of a large file can kill the whole request instead of being cut by the owner of the session")
    saf=d.get("safety") or {}
    if not saf.get("allowlist_not_blocklist"): f.append("BA-3 command validation is not an allowlist (the source: a blocklist misses any command it did not anticipate) - blocklist-only validation is a list of yesterday's dangerous commands")
    if not saf.get("isolation_is_the_enforcement_boundary"): f.append("BA-3 isolation is not the recorded enforcement boundary (the source is explicit: the allowlist/operator check is a tripwire for obvious mistakes, not an enforcement boundary - it misses an operator glued to a word; the real control is running the whole session inside a container or a VM) - a tripwire treated as a wall is the classic bash-tool failure")
    if not saf.get("timeout_and_resource_limits"): f.append("BA-3 there is no timeout that kills the shell and every process it started when a command hangs (then restarts the session), and no resource limits on the shell process (CPU, memory, disk, e.g. ulimit) - a hanging or runaway command holds the session and the host with it")
    sec=d.get("security") or {}
    if not sec.get("every_command_and_output_logged"): f.append("BA-4 not every command and its output is logged for audit - an unlogged shell is an execution path with no trace, and untraced work cannot be verified or reconstructed after an incident")
    if not sec.get("secrets_redacted_from_output"): f.append("BA-4 credentials and secrets are not redacted from command output before it is returned to Claude - shell output is the highest-bandwidth secret leak in an agent system (env dumps, config cats, error traces), and once returned it is in the conversation")
    if not sec.get("no_interactive_or_gui_assumption"): f.append("BA-4 the design does not exclude interactive and GUI commands (no vim, less, password prompts or anything waiting on stdin; command-line only; no streaming back) - a command waiting for input hangs the session until the timeout, and a prompt answered by habit is an approval nobody gave")
    cost=d.get("cost_and_version") or {}
    if not cost.get("current_version_pinned"): f.append("BA-5 the tool version is not pinned to the current bash_20250124 (no beta header; bash_20241022 works only with the retired Oct 2024 Sonnet 3.5 and needs the computer-use beta header) - an old pin is a retired-model dependency wearing a tool definition")
    if not cost.get("token_cost_counted"): f.append("BA-5 the bash tool's token cost is not counted (definition adds 325 input tokens on Claude 4.7 and later, 244 on 4.6 and earlier, PLUS the tokens of command outputs, error messages and large file contents) - shell output is paid input, and a surface that does not count it cannot price a run")
    if not cost.get("reverified_on_model_change"): f.append("BA-5 version, pricing and limits are not re-verified when the model changes (token add-on differs by model generation; model support is stated per version) - a model swap silently changes what the same shell surface costs and accepts")
    return f
if __name__=="__main__":
    data=json.load(open(sys.argv[1])); fails=check(data)
    if fails:
        print(f"FAIL ({len(fails)}):")
        [print(" -",x) for x in fails]; sys.exit(1)
    print("PASS"); sys.exit(0)
