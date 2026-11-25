#!/usr/bin/env python3
"""Gate SU-0..SU-6: synthetic-user data sufficiency for onboarding.
Sources: Cassi/What-IF fidelity data (5 demographic fields ~70%, dense qualitative + memory/reflection ~85%),
Generative Agents memory/reflection/planning architecture, founder directive 2026-11-14 (more data, synthetic user first).
Stdlib only. Usage: synthetic_user_check.py <state.json> ; exit 0 PASS, 1 FAIL.
"""
import json, sys
REQUIRED_DOMAINS = {"goal","pain","frequency","triggers","attempted_solutions","receptivity_time","values_identity"}
def check(s):
    fails, warns = [], []
    if not s.get("synthetic_object_exists"): fails.append("SU-0: no synthetic-user object/schema built from answers")
    qs = s.get("questions", [])
    unmapped = [q.get("id") for q in qs if not q.get("synthetic_field")]
    if unmapped: fails.append(f"SU-1: questions with no synthetic field: {unmapped}")
    if len(qs) < 7: fails.append(f"SU-1b: only {len(qs)} question steps (<7; winner I am uses ~25 steps, founder: questions are too few)")
    covered = set(s.get("domains_covered", []))
    missing = sorted(REQUIRED_DOMAINS - covered)
    if missing: fails.append(f"SU-2: required domains missing: {missing}")
    if not s.get("has_free_text_input"): fails.append("SU-3: no dense qualitative (free-text/open) input; multiple-choice demographics alone cap fidelity at ~70%")
    if not s.get("memory_stream"): fails.append("SU-4: no memory stream (answers/history not stored retrievably)")
    if not s.get("reflection_step"): fails.append("SU-5: no reflection step deriving conclusions before first intervention")
    if not s.get("planning_from_reflection"): fails.append("SU-5b: first intervention not selected from reflection/planning")
    if s.get("claims_replacement_of_humans"): fails.append("SU-6: claims synthetic replaces real humans (screening only; finalists validated with real responses)")
    if not s.get("fidelity_validated_against_real"): fails.append("SU-6b: fidelity never validated against real user responses")
    return fails, warns
def main():
    s = json.load(open(sys.argv[1]))
    fails, warns = check(s)
    for w in warns: print("WARN", w)
    for f in fails: print("FAIL", f)
    print(f"RESULT: {'PASS' if not fails else 'FAIL'} ({len(fails)} fails, {len(warns)} warns)")
    sys.exit(0 if not fails else 1)
if __name__ == "__main__": main()
