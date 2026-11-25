#!/usr/bin/env python3
"""code-execution-check: deterministic gate for the Code Execution surface
(how Claude's server-side sandboxed code execution - Bash + file operations
in Anthropic's container - is triggered, versioned, bounded, reused,
fed and drained of files, error-read, and priced, is decided, not left
to whatever each request happens to include).
Stdlib only, offline.
Canonical source (read in full 2026-11-19):
- Anthropic Claude Platform Docs "Code execution tool"
  https://platform.claude.com/docs/en/agents-and-tools/tool-use/code-execution-tool
  (422 lines read in full): Claude runs code for non-trivial math, data
  analysis / file parsing / visualization, algorithm execution and
  explicit run requests; it answers directly for simple arithmetic,
  well-known facts, factual / conversational / creative requests and
  simple conversions. Versions: code_execution_20250825 = Bash + file
  operations; code_execution_20260120 adds REPL state persistence and
  programmatic tool calling from inside the sandbox (Haiku 4.5 accepts
  the type but PTC and REPL persistence are unavailable there, so it
  behaves like 20250825); code_execution_20260521 is the same runtime
  with the 90-second per-cell wall-clock limit in the tool description
  (an over-limit cell returns a normal result with non-zero return_code
  and a detection_timeout status - distinct from the API-level
  execution_time_exceeded error). No beta header is required. Model
  support is read from capabilities.server_tools.code_execution.supported
  in the Models API - NOT the top-level capabilities.code_execution,
  which reports whether sandbox code can call the request's other tools.
  The tool adds two sub-tools (bash_code_execution,
  text_editor_code_execution) and needs no parameters beyond type/name.
  Container: Python 3.11, Linux x86_64, 5 GiB RAM, 5 GiB disk, 1 CPU,
  internet completely disabled, no runtime package installs (pre-installed
  libraries only: pandas/numpy/scipy/sklearn, matplotlib/seaborn,
  openpyxl/pillow/pypdf/reportlab, sympy, plus CLI tools rg/fd/sqlite).
  Files in: upload via the Files API and reference with a
  container_upload block. Files out: each bash call gets a fresh empty
  $OUTPUT_DIR; only top-level files there are captured as file_id entries
  in the result content and downloaded via the Files API - prompt Claude
  to copy into $OUTPUT_DIR and ls it in the same command, because Claude
  never sees the content list; a file written elsewhere stays in the
  container and can be copied out on container reuse. Downloaded media
  files (PNG/JPEG/GIF/WebP/TIFF/HEIC/AVIF/SVG/MP4/MOV/MP3/WAV/FLAC/M4A)
  carry signed C2PA Content Credentials identifying Anthropic as issuer
  (text/PDF/office files are not signed; re-encoding or metadata
  stripping removes the credential, so absence proves nothing).
  Container reuse: pass the response's container id back to keep files
  (and, on 20260120+, interpreter state); containers expire 30 days after
  creation, are checkpointed after about 5 minutes idle and restored on
  reuse inside the window; the response expires_at is a shorter rolling
  value, not the 30-day limit; an expired container errors - resend
  without the container parameter. Results: bash results carry stdout,
  stderr, return_code and the $OUTPUT_DIR content list; file-op results
  carry their own fields (view/create/str_replace). Errors: unavailable,
  execution_time_exceeded, invalid_tool_input, too_many_requests (all
  tools), output_file_too_large (bash), file_not_found (text editor).
  pause_turn: resend the paused response as-is WITH its container id -
  without it the continuation runs in a new container and the turn's
  files are lost. When Claude calls a client tool alongside code
  execution, the API returns the code execution call without its result;
  the result arrives after the client tool_result blocks are sent back.
  Multicomputer hazard: alongside client-side code tools (Bash tool,
  custom REPL) or the automatic code execution that web search / fetch
  provision, Claude can use the wrong environment or assume shared
  state - the system prompt must disambiguate the environments.
  Streaming delivers sub-tool input as input_json_delta and each result
  block whole in one content_block_start. Batches price code execution
  the same as Messages. Pricing: FREE when web_search_20260209+ or
  web_fetch_20260209+ is in the request (dynamic filtering's provisioned
  execution included; tokens only). Otherwise billed by execution time
  with a 5-minute minimum, tracked separately from tokens: 1,550 free
  hours per organization per month, then $0.05 per hour per container;
  if files are included, execution time is billed even if the tool is
  never called, because files are preloaded onto the container. Usage
  is tracked in the response. Retention: container data (artifacts,
  uploads, outputs) is retained up to 30 days; files created in the
  Files API persist until explicitly deleted.
Exit 0=PASS, 1=FAIL.
"""
import json, sys
def check(d):
    f=[]
    dec=d.get("decision") or {}
    if not dec.get("decision_recorded"): f.append("CX-0 the Code Execution surface is not recorded as a decided surface - whether server-side sandboxed execution is used at all, for which work and under what version, is left to each call site and habit, not a decision")
    if not dec.get("owner_recorded"): f.append("CX-0 no owner is recorded for code execution correctness (triggering, version, container lifecycle, file flow, spend) - code that ran in the wrong environment, or a container bill nobody expected, has no accountable reader")
    if not dec.get("surfaces_inventoried"): f.append("CX-0 there is no inventory of the execution surfaces (which work runs in Anthropic's sandbox, which runs client-side, which runs no code) - the free-with-web-tools path and the billed standalone path cannot be required where the surfaces are indistinguishable")
    trg=d.get("triggering") or {}
    if not trg.get("trigger_decided"): f.append("CX-1 triggering is not decided (run code for non-trivial math, data analysis, file parsing, visualization, algorithm execution and explicit run requests; answer directly for simple arithmetic, well-known facts, factual / conversational / creative requests and simple conversions; ask explicitly to force borderline cases) - the sandbox spins up for facts, or precision-sensitive computation is answered from memory")
    if not trg.get("version_decided"): f.append("CX-1 the tool version is not decided (code_execution_20250825 for Bash + file operations; 20260120 or later for REPL state persistence and programmatic tool calling - noting Haiku 4.5 accepts the type but behaves like 20250825; 20260521 adds the 90-second per-cell budget in the tool description; the current web search / fetch tools require 20260120 or later) - a surface expects persisted REPL state or programmatic calling its version cannot provide")
    if not trg.get("support_checked_via_models_api"): f.append("CX-1 per-model support is not checked via the Models API field capabilities.server_tools.code_execution.supported (the top-level capabilities.code_execution is a different field - whether sandbox code can call the request's other tools) - support is assumed from the wrong field and discovered from a failed request")
    env=d.get("environment") or {}
    if not env.get("limits_known"): f.append("CX-2 the container limits are not recorded (Python 3.11, Linux x86_64, 5 GiB RAM, 5 GiB workspace disk, 1 CPU, per-call maximum execution time) - jobs are designed for resources the sandbox does not have and fail at the limit instead of in the design")
    if not env.get("offline_preinstall_only_decided"): f.append("CX-2 the offline, pre-installed-only constraint is not decided (internet access is completely disabled and no packages can be downloaded or installed at runtime - only the pre-installed libraries and CLI tools exist) - a workflow silently depends on a package or a download the sandbox can never perform")
    if not env.get("container_reuse_decided"): f.append("CX-2 container reuse is not decided (pass the response container id back to keep created files - and on 20260120+, interpreter state; containers expire 30 days after creation, checkpoint after about 5 minutes idle and restore on reuse; the response expires_at is a shorter rolling value, not the 30-day limit; an expired container errors and the request is resent without the container parameter) - multi-request work restarts from an empty container, or an expired id is retried as if it could be restored")
    fil=d.get("files") or {}
    if not fil.get("file_input_decided"): f.append("CX-3 file input is not decided (own data files are uploaded through the Files API and referenced with a container_upload content block; CSV, Excel, JSON, XML, images and text are processable) - analysis is attempted on data the sandbox never received, pasted into context at full token cost instead")
    if not fil.get("file_output_decided"): f.append("CX-3 file output capture is not decided (each bash call gets a fresh empty $OUTPUT_DIR and only its top-level files are captured as file_id entries retrievable via the Files API; Claude never sees the content list, so the prompt must have it copy outputs into $OUTPUT_DIR and ls the directory in the same command; files written elsewhere stay in the container) - a generated chart or report exists inside the container and is reported as delivered while the caller holds nothing")
    if not fil.get("credentials_and_retention_understood"): f.append("CX-3 Content Credentials and retention are not understood (downloaded media files carry a signed C2PA manifest identifying Anthropic as issuer - text, PDF and office files are unsigned, and re-encoding or metadata stripping removes the credential so its absence proves nothing; container data is retained up to 30 days while Files API files persist until explicitly deleted) - a missing credential is misread as proof of non-AI origin, or sandbox outputs are assumed deleted / assumed permanent against the actual retention shape")
    exe=d.get("execution") or {}
    if not exe.get("results_and_errors_handled"): f.append("CX-4 results and errors are not handled as designed (bash results carry stdout, stderr, return_code and the $OUTPUT_DIR content list; errors include unavailable, execution_time_exceeded for a whole call, invalid_tool_input, too_many_requests, output_file_too_large for bash and file_not_found for the text editor; a programmatic-calling cell over its 90-second limit is NOT execution_time_exceeded - it is a normal result with non-zero return_code and a detection_timeout status) - a timed-out cell is read as an API failure, or a failed command's stderr is never read and its empty stdout is reported as the answer")
    if not exe.get("pause_turn_handled"): f.append("CX-4 pause_turn is not handled for code execution (resend the paused response as-is together with its container id - without the id the continuation runs in a new container and the turn's files are lost; when a client tool is called alongside code execution, the API returns the execution call without its result and the result arrives only after the client tool_result blocks are sent back) - a paused analysis is abandoned as finished, or continued in a fresh container that silently lost its files")
    if not exe.get("multicomputer_disambiguated"): f.append("CX-4 the multicomputer hazard is not disambiguated in the system prompt (server-side code execution runs in Anthropic's sandbox while client-provided Bash / REPL tools run in a separate controlled environment - and web search / fetch provision their own automatic code execution; without explicit system-prompt separation Claude can call the wrong environment or assume state is shared between them) - code runs where its files and state are not, and the missing output is misread as a failed computation")
    eco=d.get("economics") or {}
    if not eco.get("free_with_web_tools_accounted"): f.append("CX-5 the free-with-web-tools pricing is not accounted (when web_search_20260209 or later, or web_fetch_20260209 or later, is in the request, code execution in that request - including the execution dynamic filtering provisions automatically - carries no charge beyond token costs) - a search or fetch surface is billed in planning for execution it gets free, or a standalone surface is planned as free because a different surface was")
    if not eco.get("standalone_pricing_accounted"): f.append("CX-5 standalone pricing is not accounted (execution time is billed separately from tokens with a 5-minute minimum per container; each organization receives 1,550 free hours per month, then $0.05 per hour per container; usage is tracked in the response) - a long-running sandbox loop's bill is a per-container time line nobody budgeted, discovered from the invoice instead of the response usage")
    if not eco.get("preload_billing_accounted"): f.append("CX-5 file-preload billing is not accounted (when files are included in the request, execution time is billed even if the tool is never called, because the files are preloaded onto the container; streaming and Message Batches do not change the price shape - batches price code execution the same as Messages) - requests that merely carry files accrue execution charges nobody attributed, and batch jobs are costed as if the preload were free")
    return f
if __name__=="__main__":
    data=json.load(open(sys.argv[1])); fails=check(data)
    if fails:
        print(f"FAIL ({len(fails)}):")
        [print(" -",x) for x in fails]; sys.exit(1)
    print("PASS"); sys.exit(0)
