#!/usr/bin/env python3
"""mcp-code-check: deterministic gate for the MCP CODE-EXECUTION surface
(presenting MCP servers as code APIs on a filesystem instead of loading
every tool definition up front, discovering tools progressively with
search at selectable detail levels, filtering and transforming results
inside the execution environment before they reach the model, doing
loops / conditionals / error handling in code in a single step,
keeping intermediate results and PII out of the model context under
deterministic data-flow rules, running generated code sandboxed with
resource limits and monitoring, persisting state to files so work can
resume, saving working code as reusable skills, and measuring the
token / cost effect against the operational overhead).
Stdlib only, offline.
Canonical source (read in full 2026-11-18, Anthropic Engineering,
"Code execution with MCP: Building more efficient agents",
https://www.anthropic.com/engineering/code-execution-with-mcp,
published 2025-11-04):
- Two costs grow with MCP scale: tool definitions overload the context
  window (thousands of tools can mean hundreds of thousands of tokens
  before the request is read), and intermediate tool results flow
  through the model, often twice (a 2-hour transcript can add ~50,000
  tokens; large results can exceed the window and break the workflow,
  and copying data between calls invites mistakes).
- Fix: present MCP servers as code APIs. Generate a file tree, one
  file per tool; the agent lists ./servers, reads only the tool files
  it needs, and writes code that calls them. Reported effect in the
  article's example: 150,000 tokens -> 2,000 tokens (98.7% saving).
  Cloudflare published the same pattern as "Code Mode".
- Progressive disclosure: a search_tools tool with a detail-level
  parameter (name only / name+description / full definition) lets the
  agent conserve context while finding tools.
- Context-efficient results: filter / transform / aggregate / join in
  the execution environment; the agent sees 5 rows, not 10,000.
  Control flow (loops, conditionals, error handling, waiting) runs in
  code instead of alternating model calls, which also saves
  time-to-first-token latency.
- Privacy: intermediate results stay in the execution environment by
  default; the harness can tokenize PII so real values flow tool to
  tool but never through the model; deterministic rules can govern
  where data may flow.
- State and skills: filesystem access lets agents persist intermediate
  results and resume; working code can be saved as reusable functions,
  and adding SKILL.md turns them into structured skills - a growing
  toolbox.
- Cost of the pattern: running agent-generated code requires a secure
  execution environment with sandboxing, resource limits and
  monitoring; benefits must be weighed against that overhead.
Exit 0=PASS, 1=FAIL.
"""
import json, sys
def check(d):
    f=[]
    dec=d.get("decision") or {}
    if not dec.get("decision_recorded"): f.append("MC-0 the MCP code-execution surface is not recorded as a decided surface - whether tools are called directly or through code is left to per-agent habit")
    if not dec.get("owner_recorded"): f.append("MC-0 no owner is recorded for the tool-access surface - nobody is named to keep token overhead, sandboxing and data-flow rules honest")
    if not dec.get("canonical_source_recorded"): f.append("MC-0 the canonical source is not recorded (Anthropic code execution with MCP: tools as code APIs on a filesystem, progressive disclosure, results filtered in the execution environment, PII tokenization, sandboxed execution, state and skills) - every surface invents its own tool calling")
    di=d.get("disclosure") or {}
    if not di.get("presented_as_code_filesystem"): f.append("MC-1 tools are not presented as a code API / file tree (one file per tool under a servers directory the agent can browse) - there is no structure the model can navigate to find a tool without loading all of them")
    if not di.get("load_only_needed_on_demand"): f.append("MC-1 tool definitions are loaded all up front instead of only the ones the current task needs - thousands of tools mean hundreds of thousands of tokens spent before the request is even read")
    if not di.get("search_tools_with_detail_levels"): f.append("MC-1 there is no search_tools-style discovery with selectable detail levels (name only / name+description / full schema) - finding a tool costs the full definition every time")
    re_=d.get("results") or {}
    if not re_.get("filter_transform_in_execution_env"): f.append("MC-2 large results are not filtered / transformed in the execution environment before reaching the model - a 10,000-row result is read by the model instead of the 5 rows the task needs")
    if not re_.get("intermediate_results_stay_in_env"): f.append("MC-2 intermediate results flow through the model by default (often twice: out of one tool and into the next call) - a 2-hour transcript adds ~50,000 tokens and larger results break the workflow outright")
    if not re_.get("aggregations_joins_in_code"): f.append("MC-2 aggregations, joins across sources and field extraction are not done in code - the model copies data between calls, which is exactly where transcription mistakes enter")
    co=d.get("control") or {}
    if not co.get("loops_conditionals_error_handling_in_code"): f.append("MC-3 loops, conditionals, waiting and error handling are not expressed in code - every branch costs a model round-trip through the agent loop")
    if not co.get("complex_logic_single_step"): f.append("MC-3 complex multi-tool logic is not executed as a single program - the sequence is re-planned token by token instead of run once in the environment")
    if not co.get("latency_time_to_first_token_considered"): f.append("MC-3 time-to-first-token latency is not part of the design (code evaluating a conditional is faster than waiting for the model to evaluate it) - slow paths are indistinguishable from fast ones")
    pr=d.get("privacy") or {}
    if not pr.get("pii_tokenized_before_model"): f.append("MC-4 sensitive data is not tokenized by the harness before it can reach the model - real names, emails and phone numbers flow through the context and can be logged or processed by the agent")
    if not pr.get("deterministic_data_flow_rules"): f.append("MC-4 there are no deterministic rules for where data may flow (which source may feed which destination) - data movement is governed by model discretion instead of by the client")
    if not pr.get("sandboxed_limits_monitored_execution"): f.append("MC-4 agent-generated code does not run in a secure execution environment with sandboxing, resource limits and monitoring - the pattern's own stated cost is unpaid, so its benefits are unsafe to claim")
    ev=d.get("evolution") or {}
    if not ev.get("state_persisted_to_files_resumable"): f.append("MC-5 intermediate state is not persisted to files so work can resume and progress can be tracked - a long operation that dies restarts from zero")
    if not ev.get("reusable_functions_saved_as_skills"): f.append("MC-5 working code is not saved as reusable functions / skills (SKILL.md-structured) - every agent re-derives the same solution and the toolbox never compounds")
    if not ev.get("token_cost_measured_and_overhead_weighed"): f.append("MC-5 the token / cost effect is never measured before-and-after (the canonical example is 150,000 -> 2,000 tokens, 98.7%) and never weighed against sandboxing and operational overhead - an unmeasured efficiency claim is marketing, not engineering")
    return f
if __name__=="__main__":
    data=json.load(open(sys.argv[1])); fails=check(data)
    if fails:
        print(f"FAIL ({len(fails)}):")
        [print(" -",x) for x in fails]; sys.exit(1)
    print("PASS")
