#!/usr/bin/env python3
"""agent-skills-check: deterministic gate for the AGENT SKILLS surface
(a skill is a folder with SKILL.md whose YAML frontmatter name+description
is pre-loaded as level 1 of progressive disclosure, whose body is level 2
loaded only when relevant, and whose bundled files are level 3 loaded only
as needed; deterministic work belongs in pre-written scripts run without
loading code or data into context; skills are developed starting from
evaluation on representative tasks, monitored in real use and iterated,
capturing successful approaches and mistakes; skills from less-trusted
sources are audited before use, including dependencies and external
network instructions). Stdlib only, offline.
Canonical source (read in full 2026-11-18, Anthropic Engineering,
"Equipping agents for the real world with Agent Skills",
https://www.anthropic.com/research/equipping-agents-for-the-real-world-with-agent-skills,
published 2025-10-16, updated 2025-12-18 as open standard):
- Anatomy: directory + SKILL.md, required frontmatter name/description
  pre-loaded at startup (level 1), body read when relevant (level 2),
  bundled files referenced by name and read only as needed (level 3+);
  bundled context is effectively unbounded because the agent need not
  read it all into the window.
- Code execution: sorting by token generation is far more expensive than
  running an algorithm; pre-written scripts run without loading script
  or data into context, and code is deterministic, consistent, repeatable.
- Structure for scale: split an unwieldy SKILL.md into separate files,
  keep mutually exclusive / rarely co-used contexts on separate paths to
  cut tokens, make clear whether code is to be run or read as reference.
- Developing/evaluating: start with evaluation (representative tasks,
  observe struggles/gaps, build incrementally); think from the agent's
  perspective (monitor real use, unexpected trajectories, overreliance;
  name/description decide triggering); iterate with the agent (capture
  successful approaches and common mistakes into the skill, self-reflect
  when it goes off track).
- Security: install only from trusted sources; for less-trusted sources
  thoroughly audit all bundled files before use, paying attention to
  code dependencies, bundled resources, and instructions/code that
  connect to potentially untrusted external network sources.
Exit 0=PASS, 1=FAIL.
"""
import json, sys
def check(d):
    f=[]
    dec=d.get("decision") or {}
    if not dec.get("decision_recorded"): f.append("SK-0 the agent skills surface is not recorded as a decided surface - which work must be a skill, and in what form, is left to per-task habit")
    if not dec.get("owner_recorded"): f.append("SK-0 no owner is recorded for the skills library - nobody is named to keep the catalogue honest, deduplicated and current")
    if not dec.get("canonical_source_recorded"): f.append("SK-0 the canonical source is not recorded (Anthropic equipping agents with Agent Skills: folder + SKILL.md, progressive disclosure, scripts for deterministic work, evaluation-first development, audit before use) - every author invents their own skill shape")
    ana=d.get("anatomy") or {}
    if not ana.get("skill_metadata_name_description"): f.append("SK-1 skills do not all carry the required YAML frontmatter name and description - the agent cannot know when each skill should be used without loading it")
    if not ana.get("bundled_files_referenced_by_name"): f.append("SK-1 bundled files are not referenced by name from SKILL.md and loaded only as needed - detail either bloats the core file or is undiscoverable")
    if not ana.get("progressive_disclosure_audited"): f.append("SK-1 progressive disclosure is not audited (metadata pre-loaded only, body on relevance, bundled files on need) - the three levels are assumed from the platform, never verified per skill")
    st=d.get("structure") or {}
    if not st.get("unwieldy_skill_split_into_files"): f.append("SK-2 there is no rule enforced to split an unwieldy SKILL.md into separate referenced files - core files grow until they crowd out the task itself")
    if not st.get("mutually_exclusive_contexts_separate_paths"): f.append("SK-2 mutually exclusive or rarely co-used contexts are not kept on separate paths - every run pays tokens for contexts it will not use")
    if not st.get("code_role_explicit_run_or_reference"): f.append("SK-2 it is not made clear per script whether the agent should run it directly or read it into context as reference - code is misused in both directions")
    ce=d.get("code_execution") or {}
    if not ce.get("deterministic_work_as_scripts"): f.append("SK-3 deterministic operations are not packaged as pre-written scripts - the model re-derives by token generation what an algorithm does cheaper and reliably")
    if not ce.get("scripts_run_without_loading_code_or_data"): f.append("SK-3 scripts are not run without loading the script and its data into context - the token saving that justifies code execution is given back")
    if not ce.get("script_repeatability_verified"): f.append("SK-3 script repeatability is not verified (same input, same output, run in the real workflow) - 'deterministic' is asserted, not measured")
    dv=d.get("development") or {}
    if not dv.get("start_with_evaluation_representative_tasks"): f.append("SK-4 skills are not built starting from evaluation: representative tasks run first, struggles and context gaps observed, then built incrementally - skills anticipate needs the agent does not have and miss the ones it does")
    if not dv.get("monitor_real_use_and_iterate"): f.append("SK-4 real use of skills is not monitored for unexpected trajectories or overreliance on certain contexts, with iteration from those observations - a skill's failure modes stay invisible")
    if not dv.get("capture_success_and_mistakes_into_skill"): f.append("SK-4 successful approaches and common mistakes are not captured back into the skill (with self-reflection when it goes off track) - every agent relearns the same lesson")
    sec=d.get("security") or {}
    if not sec.get("trusted_sources_only"): f.append("SK-5 there is no trusted-sources-only rule for installing skills - any found skill can enter the library on discovery alone")
    if not sec.get("audit_bundled_files_before_use"): f.append("SK-5 skills from less-trusted sources are not thoroughly audited before use (all bundled files read, code dependencies and bundled resources inspected) - a skill is software installed on trust")
    if not sec.get("external_network_instructions_checked"): f.append("SK-5 instructions or code that connect to potentially untrusted external network sources are not specifically checked - exfiltration and unintended actions hide in the least-read file")
    return f
if __name__=="__main__":
    data=json.load(open(sys.argv[1])); fails=check(data)
    if fails:
        print(f"FAIL ({len(fails)}):")
        [print(" -",x) for x in fails]; sys.exit(1)
    print("PASS")
