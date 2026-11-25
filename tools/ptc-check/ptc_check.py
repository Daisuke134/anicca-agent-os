#!/usr/bin/env python3
"""ptc-check: deterministic gate for the Programmatic Tool Calling surface
(how tools are called from inside code execution instead of one model round
trip per call - allowed_callers, container continuation, result-message
shape, workload fit and measured token savings - is decided, not left to
whatever each request happens to include).
Stdlib only, offline.
Canonical source (read in full 2026-11-19):
- Anthropic Claude Platform Docs "Programmatic tool calling"
  https://platform.claude.com/docs/en/agents-and-tools/tool-use/programmatic-tool-calling
  (455 lines read in full): Claude writes Python code that calls tools as
  functions inside a code execution container; execution pauses per call,
  the API returns a tool_use block whose caller field names the code
  execution run (tool_id = the server_tool_use block id), the caller
  supplies the result, and intermediate results never enter the context
  window - only the final code output does. Requires the code execution
  tool at version code_execution_20260120 or later; Haiku 4.5 accepts
  those versions but does not support programmatic calling, so support is
  checked per model via the Models API field
  capabilities.code_execution.supported. allowed_callers decides per tool:
  ["direct"] (default), ["code_execution_20260120"], or both; the 20260120
  and 20260521 caller versions are interchangeable in allowed_callers and
  responses always tag the caller as code_execution_20260120. Containers
  are the code execution containers: a pending programmatic call makes the
  container ID REQUIRED on the continuation request (the API rejects the
  request without it) and the same tools array must be resent; containers
  expire 30 days after creation, are checkpointed after about 5 minutes
  of inactivity, and expires_at is a shorter rolling value, not the
  30-day limit. A user message answering pending programmatic calls may
  contain ONLY tool_result blocks (no text), must answer every pending
  call in one message, and each result's content must be a string or text
  blocks only. Pause vs completion is told apart by stop_reason
  ("tool_use") and each tool_use block's caller. Token economics: on
  BrowseComp / DeepSearchQA, programmatic calling on top of search tools
  improved performance by an average of 11 percent on 24 percent fewer
  input tokens; on a 75-tool project-management agent benchmark billed
  input tokens fell roughly 38 percent with no accuracy change; on
  tau2-bench (one or two sequential calls per turn) scores were unchanged
  and cost ran roughly 8 percent MORE; production traffic with 10-49 tool
  definitions typically saves 20-40 percent. Strong fit: fan-out across
  many items, large results that can be filtered / aggregated before
  reaching context, agentic search. Weak fit: strictly sequential
  reasoning-dependent chains, few small calls (especially the first turn,
  where container + script overhead can exceed savings), tools needing
  immediate user feedback between calls. Measure billed input tokens with
  and without allowed_callers on a representative sample before enabling
  broadly. Each programmatic call counts individually toward the same
  rate limits as regular calls. Incompatibilities: strict: true tools are
  not supported; tool_choice cannot force programmatic calling and naming
  a tool whose allowed_callers omits "direct" in tool_choice is a 400
  invalid_request_error; disable_parallel_tool_use: true is unsupported.
  A custom tool whose input_schema contains a recursive (circular) $ref
  cannot be enabled - the request fails 400 with "Circular $ref
  detected"; workarounds are keeping the tool direct-only or unrolling
  the recursion. MCP connector tools and the computer use / browser use
  toolsets accept only "direct" and can never be called programmatically.
  Tool results come back as strings that can contain arbitrary content
  including code: validate results from external sources or user input
  before the running code interprets them (code injection risk). Tool
  design for code: document output format in detail (JSON structure,
  field types) because Claude deserializes results in code, return
  structured machine-readable data, keep responses concise. Timeout: if
  a result does not arrive within about 4 minutes the pending call raises
  TimeoutError in Claude's running code (visible in stderr, Claude
  typically retries); the paused response's expires_at falls AFTER that
  timeout and is not the deadline - respond as soon as possible, put
  timeouts on your own tool execution, chunk long operations. Tool errors
  are delivered to the code, which can handle them; invalid_tool_input
  surfaces as error_code on the code_execution_tool_result error block.
  Debugging: log all tool calls and results, check the caller field to
  confirm programmatic calls, monitor container IDs for proper reuse,
  test tools independently before enabling. Reuse containers across
  related requests to keep state and batch similar operations into one
  code execution. Pricing is the code execution pricing; container data
  (artifacts and outputs) is retained up to 30 days.
Exit 0=PASS, 1=FAIL.
"""
import json, sys
def check(d):
    f=[]
    dec=d.get("decision") or {}
    if not dec.get("decision_recorded"): f.append("PT-0 the Programmatic Tool Calling surface is not recorded as a decided surface - which tools Claude may call from inside code execution, directly, or both, is left to each call site and habit, not a decision")
    if not dec.get("owner_recorded"): f.append("PT-0 no owner is recorded for programmatic calling correctness (caller configuration, continuation protocol, measured savings) - a workflow that silently pays direct-call token costs, or breaks on a rejected continuation, has no accountable reader")
    if not dec.get("surfaces_inventoried"): f.append("PT-0 there is no inventory of the tool-calling surfaces (which tools are direct-only, which are code-execution-only, which allow both) - savings and breakage cannot be required where the surfaces are indistinguishable")
    en=d.get("enablement") or {}
    if not en.get("allowed_callers_decided"): f.append("PT-1 allowed_callers is not decided per tool (adding code_execution_20260120 or later to a tool's allowed_callers is what makes it callable from code; omitting the field means direct-only; the 20260120 and 20260521 caller versions are interchangeable and responses always tag the caller as code_execution_20260120) - multi-call workflows keep paying one model round trip and full result tokens per call, or a tool is exposed to code that was designed for direct calls")
    if not en.get("model_capability_checked"): f.append("PT-1 model support is not checked before sending (programmatic calling requires the code execution tool at code_execution_20260120 or later, and Haiku 4.5 accepts those tool versions WITHOUT supporting programmatic calling; the Models API field capabilities.code_execution.supported is the check) - a request is built on a model that silently cannot run it")
    if not en.get("tool_design_for_code"): f.append("PT-1 tools are not designed for code consumption (Claude deserializes results inside its code, so output format - JSON structure and field types - must be documented in the tool description, results returned as structured machine-readable data, and responses kept concise) - the generated code guesses at result shapes and fails or misreads them at runtime")
    ct=d.get("continuation") or {}
    if not ct.get("container_id_threaded"): f.append("PT-2 the container ID is not threaded through continuations (while a programmatic call is pending, the container ID from the paused response is REQUIRED on the result request - the API rejects the request without it - and the same tools array, code execution tool included, must be resent; containers expire 30 days after creation and checkpoint after about 5 minutes idle) - the paused code cannot resume and the workflow restarts or errors")
    if not ct.get("result_message_shape_decided"): f.append("PT-2 the result message shape is not decided (a user message answering pending programmatic calls may contain ONLY tool_result blocks - no text at all - must answer every pending call in that one message, and each result's content must be a string or text blocks; image and document blocks are rejected) - a helpful sentence added after the results, or one unanswered pending call, breaks the continuation")
    if not ct.get("caller_and_stop_reason_read"): f.append("PT-2 pause vs completion is not read from the response (a paused response has stop_reason tool_use and a tool_use block whose caller names a code execution version, and caller.tool_id matches the call to its code execution server_tool_use block) - a still-running workflow is read as finished, or a finished one is fed results it no longer waits for")
    ft=d.get("fit") or {}
    if not ft.get("fit_decided"): f.append("PT-3 the workload fit is not decided (strong fit: fan-out across many items, large results filterable before context, agentic search; weak fit: strictly sequential reasoning-dependent chains, few small calls - especially on the first turn, where container and script overhead can exceed the savings - and tools needing immediate user feedback between calls) - programmatic calling is enabled where its fixed overhead is the whole cost, or withheld where round trips dominate")
    if not ft.get("savings_measured"): f.append("PT-3 savings are not measured before broad enablement (measure billed input tokens with and without allowed_callers on a representative sample: internal evaluations show roughly 38 percent fewer billed input tokens on a 75-tool agent benchmark at equal accuracy and 20-40 percent typical savings at 10-49 tool definitions, but roughly 8 percent MORE cost on sequential one-to-two-call turns in tau2-bench) - the feature is adopted or rejected on the headline number instead of this workload's shape")
    if not ft.get("rate_limits_counted"): f.append("PT-3 rate limits are not counted per call (programmatic calls are subject to the same rate limits as regular tool calls and each call from code counts individually) - a fan-out loop that is cheap in tokens is sized as if it were cheap in calls and hits the limit mid-run")
    cs=d.get("constraints") or {}
    if not cs.get("incompatibilities_respected"): f.append("PT-4 the feature incompatibilities are not respected (tools with strict: true are unsupported programmatically; tool_choice cannot force programmatic calling, and naming a tool whose allowed_callers omits direct in tool_choice returns 400 invalid_request_error; disable_parallel_tool_use: true is unsupported) - a request fails at send time on a combination that was knowable from the tool definitions")
    if not cs.get("schema_and_exclusions_checked"): f.append("PT-4 schema limits and excluded toolsets are not checked (a custom tool whose input_schema contains a recursive circular $ref fails the whole request with 400 Circular $ref detected when a code execution caller is listed - keep it direct-only or unroll the recursion; MCP connector tools and the computer use / browser use toolsets accept only direct and can never be called programmatically) - one recursive schema or one connector tool takes down a request whose other tools were fine")
    if not cs.get("result_validation_decided"): f.append("PT-4 tool results are not validated before the code uses them (results return as strings that can contain any content, including code snippets or executable commands; results built from external sources or user input carry code injection risk if the running code interprets them) - untrusted data is executed or trusted inside the sandbox because it arrived through a tool")
    op=d.get("operations") or {}
    if not op.get("timeout_handling_decided"): f.append("PT-5 the pending-call timeout is not handled (if a result does not arrive within about 4 minutes the pending call raises TimeoutError inside Claude's running code, visible in stderr, and Claude typically retries; the paused response's expires_at falls after that timeout and is NOT the deadline - results must be returned as soon as possible, own tool execution needs its own timeouts, and long operations should be chunked) - a slow tool is debugged as a model failure, or results are scheduled against a deadline that is already too late")
    if not op.get("debugging_decided"): f.append("PT-5 debugging practice is not decided (log all tool calls and results, check the caller field to confirm a call was programmatic, monitor container IDs for proper reuse, and test each tool independently before enabling programmatic calling; tool execution errors are delivered to the code to handle, and invalid_tool_input surfaces as error_code on the code_execution_tool_result error block) - a broken flow is diagnosed from the final answer instead of the call record")
    if not op.get("retention_and_reuse_decided"): f.append("PT-5 container retention and reuse are not decided (container data, artifacts and outputs are retained up to 30 days; expires_at is a shorter rolling value and does not report the 30-day limit; related requests should reuse the container to keep state and batch similar operations into one execution; pricing follows code execution) - state is rebuilt per request at full overhead, or artifacts are assumed gone - or kept - on the wrong retention clock")
    return f
if __name__=="__main__":
    data=json.load(open(sys.argv[1])); fails=check(data)
    if fails:
        print(f"FAIL ({len(fails)}):")
        [print(" -",x) for x in fails]; sys.exit(1)
    print("PASS"); sys.exit(0)
