#!/usr/bin/env python3
"""workflow-pattern-check: deterministic gate for the WORKFLOW PATTERNS
surface (choosing the simplest composable pattern per task: single
augmented LLM call, prompt chaining, routing, parallelization,
orchestrator-workers, evaluator-optimizer, or a fully autonomous agent).
Stdlib only, offline.
Canonical source (read in full 2026-11-18, Anthropic Engineering,
"Building effective agents", Erik Schluntz / Barry Zhang, published
2024-12-19, updated 2026-10-09,
https://www.anthropic.com/engineering/building-effective-agents,
295 lines read via browser.open):
- Distinction: workflows orchestrate LLMs and tools through predefined
  code paths; agents let the LLM dynamically direct its own process and
  tool usage. Both are agentic systems.
- Start with the simplest solution possible; add complexity only when
  it demonstrably improves outcomes. Agentic systems trade latency and
  cost for task performance; measure that tradeoff. For many apps,
  optimizing single LLM calls with retrieval and in-context examples
  is enough.
- Frameworks simplify low-level work but add abstraction that obscures
  prompts and responses and tempts complexity; start with LLM APIs
  directly, and if a framework is used, understand the code underneath.
- Building block: the augmented LLM (retrieval, tools, memory) with
  capabilities tailored to the use case and an easy, well-documented
  interface for the LLM.
- Prompt chaining: decompose into fixed subtasks, each call easier,
  with programmatic gates on intermediate steps; trades latency for
  accuracy.
- Routing: classify input, direct to specialized follow-up prompts /
  tools / models (easy questions to small cheap models, hard ones to
  capable models); separation of concerns.
- Parallelization: sectioning (independent subtasks in parallel) and
  voting (same task multiple times for confidence / diverse outputs).
- Orchestrator-workers: a central LLM dynamically breaks the task
  down, delegates to workers, synthesizes; fits when subtasks cannot
  be predicted in advance (unlike parallelization, subtasks are not
  pre-defined).
- Evaluator-optimizer: one call generates, another evaluates and
  feeds back in a loop; fits only with clear evaluation criteria and
  when feedback demonstrably improves the response.
- Agents: for open-ended problems where steps cannot be predicted or
  hardcoded; the agent gets ground truth from the environment at each
  step, pauses at checkpoints or blockers, and runs under stopping
  conditions (e.g. max iterations); autonomy means higher cost and
  compounding-error risk, so test extensively in sandboxed
  environments with guardrails.
- Three principles: simplicity in design, transparency (explicitly
  show planning steps), and a carefully crafted agent-computer
  interface (ACI) with the same effort as HCI: tool documentation,
  example usage, edge cases, format choices that give the model room
  to think and avoid formatting overhead, poka-yoke arguments (the
  SWE-bench lesson: requiring absolute filepaths removed a whole
  class of errors); the team spent more time optimizing tools than
  the overall prompt.
- Patterns are building blocks, not prescriptions: combine and
  customize, measure performance, iterate.
Exit 0=PASS, 1=FAIL.
"""
import json, sys
def check(d):
    f=[]
    dec=d.get("decision") or {}
    if not dec.get("decision_recorded"): f.append("WF-0 the workflow-pattern surface is not recorded as a decided surface - whether a task gets a single call, a workflow, or an autonomous agent is left to per-loop habit")
    if not dec.get("owner_recorded"): f.append("WF-0 no owner is recorded for pattern selection and its cost/latency consequences - every loop invents its own shape")
    if not dec.get("pattern_inventory_classified"): f.append("WF-0 there is no inventory classifying each agentic surface by pattern (single call / chaining / routing / parallelization / orchestrator-workers / evaluator-optimizer / agent) - misfit between task shape and pattern shape is invisible")
    sim=d.get("simplicity") or {}
    if not sim.get("simplest_first_single_call_considered"): f.append("WF-1 the simplest solution is not tried first (a single optimized LLM call with retrieval and in-context examples) - multi-step agentic systems are built for tasks a single call would settle")
    if not sim.get("complexity_tradeoff_measured"): f.append("WF-1 the tradeoff is not measured (agentic systems trade latency and cost for task performance, and complexity is added only when it demonstrably improves outcomes) - complexity is added on intuition")
    if not sim.get("framework_abstraction_understood"): f.append("WF-1 frameworks are used without understanding the code underneath (or direct API use first) - abstraction layers obscure the underlying prompts and responses and make debugging and right-sizing harder")
    wf=d.get("workflow_patterns") or {}
    if not wf.get("chaining_with_programmatic_gates"): f.append("WF-2 prompt chaining is not used with programmatic gates on intermediate steps for cleanly decomposable fixed subtasks - chains run ungated, so an early wrong step compounds silently")
    if not wf.get("routing_by_category_and_cost"): f.append("WF-2 inputs are not routed by category to specialized prompts/tools/models (easy/common to small cost-efficient models, hard/unusual to capable models) - optimizing one prompt for every input hurts the other inputs")
    if not wf.get("parallelization_sectioning_and_voting"): f.append("WF-2 parallelization is not used in its two forms (sectioning independent subtasks for speed/focus, voting the same task multiple times for confidence) - serial single attempts carry tasks that parallel attempts would settle")
    adv=d.get("advanced_patterns") or {}
    if not adv.get("orchestrator_workers_dynamic_subtasks"): f.append("WF-3 orchestrator-workers is not available for tasks whose subtasks cannot be predicted in advance (central model breaks down, delegates, synthesizes) - unpredictable work is forced into pre-defined chains")
    if not adv.get("evaluator_optimizer_only_with_clear_criteria"): f.append("WF-3 evaluator-optimizer is not used as a bounded loop where it fits (clear evaluation criteria, feedback demonstrably improves the response) - generation ships without a structured critique loop, or loops run without criteria")
    if not adv.get("agents_only_for_open_ended_unpredictable"): f.append("WF-3 autonomous agents are not restricted to open-ended problems where steps cannot be predicted or hardcoded and the environment is trusted - autonomy (and its compounding-error risk) is spent on well-defined tasks a workflow would do predictably")
    ops=d.get("agent_operations") or {}
    if not ops.get("ground_truth_from_environment_each_step"): f.append("WF-4 agents do not gain ground truth from the environment at each step (tool results, code execution, landed artifacts) to assess progress - progress is asserted from the model's own narrative")
    if not ops.get("stopping_conditions_and_checkpoints"): f.append("WF-4 agents run without stopping conditions (maximum iterations / budget) and without pausing at checkpoints or blockers for feedback - an autonomous loop has no firm edge")
    if not ops.get("sandboxed_testing_and_guardrails"): f.append("WF-4 agentic systems are not tested extensively in sandboxed environments with appropriate guardrails before trusted runs - compounding errors are discovered in production")
    aci=d.get("aci_and_maintenance") or {}
    if not aci.get("transparency_planning_steps_shown"): f.append("WF-5 transparency is not maintained (the agent's planning steps are not explicitly shown) - a system whose plan cannot be read cannot be corrected mid-flight")
    if not aci.get("aci_documented_tested_poka_yoke"): f.append("WF-5 the agent-computer interface is not crafted with HCI-level effort (tool documentation with examples, edge cases and boundaries; formats that give the model room to think and avoid formatting overhead; poka-yoke arguments such as requiring absolute paths; tool use tested with many example inputs) - tool mistakes are treated as model mistakes")
    if not aci.get("measure_iterate_combine_only_when_improves"): f.append("WF-5 performance is not measured and iterated, and patterns are not combined/customized only when that demonstrably improves outcomes - pattern choice is frozen at first build")
    return f
if __name__=="__main__":
    data=json.load(open(sys.argv[1])); fails=check(data)
    if fails:
        print(f"FAIL ({len(fails)}):")
        [print(" -",x) for x in fails]; sys.exit(1)
    print("PASS")
