#!/usr/bin/env python3
"""Deterministic DF-0..DF-7 reporting gates, 2026-11-19; stdlib only."""
import json
import math
import sys
from pathlib import Path


def text(value):
    return isinstance(value, str) and bool(value.strip())


def number(value, lower=-math.inf, upper=math.inf):
    return type(value) in (int, float) and (type(value) is int or math.isfinite(value)) and lower <= value <= upper


def obj(value):
    return value if isinstance(value, dict) else {}


def records(value, predicate):
    return isinstance(value, list) and bool(value) and all(predicate(item) for item in value)


def metric(value):
    value = obj(value)
    return text(value.get("metric")) and number(value.get("value"))


def contrast(value):
    value = obj(value)
    test = obj(value.get("test"))
    interval = obj(value.get("interval"))
    inference = (text(test.get("method")) and number(test.get("p_value"), 0, 1)) or (
        number(interval.get("lower")) and number(interval.get("upper"))
        and interval["lower"] <= interval["upper"]
        and number(interval.get("confidence"), 0, 1) and 0 < interval["confidence"] < 1)
    return text(value.get("effect_size_metric")) and number(value.get("effect_size")) and bool(inference)


def outcome_report(value):
    value = obj(value)
    groups = value.get("groups")
    return (records(groups, lambda row: text(obj(row).get("outcome")) and metric(row))
            and len({row["outcome"] for row in groups}) == len(groups) and len(groups) >= 2
            and contrast(value.get("contrast")))


def check(state):
    d = obj(state)
    measurement = obj(d.get("measurement"))
    behavior = obj(d.get("behavior"))
    leakage = obj(d.get("knowledge_leakage"))
    likeness = obj(d.get("human_likeness"))
    reliability = obj(d.get("reliability"))
    coverage = obj(reliability.get("coverage"))
    calibration = obj(d.get("calibration"))
    domains = leakage.get("domains")
    paired = (records(domains, lambda row: text(obj(row).get("domain"))
                      and contrast(obj(row).get("paired_contrast")))
              and len({row["domain"] for row in domains}) == len(domains))
    sensitivity = obj(likeness.get("judge_sensitivity"))
    sensitivity_ok = ((sensitivity.get("performed") is False and text(sensitivity.get("note")))
                      or (sensitivity.get("performed") is True
                          and records(sensitivity.get("judges"), text)
                          and len(set(sensitivity["judges"])) >= 2
                          and text(sensitivity.get("result"))))
    controls = obj(likeness.get("controls"))
    return {
        "DF-0": (d.get("ground_truth_type") in (
            "real_consequential_outcome", "assigned_goal_roleplay", "human_reference_dialogue", "none")
            and type(d.get("decision_claimed")) is bool
            and not (d["decision_claimed"] and d["ground_truth_type"] == "assigned_goal_roleplay")),
        "DF-1": outcome_report(d.get("outcome_conditioned")),
        "DF-2": (all(number(obj(behavior.get(rate)).get(source), 0, 1)
                     for rate in ("resistance", "deliberation", "disengagement")
                     for source in ("real", "simulation"))
                 and (behavior.get("repair_claimed") is False
                      or (behavior.get("repair_claimed") is True
                          and outcome_report(behavior.get("post_repair_outcome_conditioned"))))),
        "DF-3": (type(measurement.get("teacher_forced")) is bool
                 and type(measurement.get("same_perceiver")) is bool
                 and (measurement["teacher_forced"] or measurement["same_perceiver"]
                      or measurement.get("uncontrolled") is True)),
        "DF-4": (leakage.get("persona_has_unknown_targets") is False
                 or (leakage.get("persona_has_unknown_targets") is True
                     and records(leakage.get("pairs"), lambda row:
                                 text(obj(row).get("real_item")) and text(obj(row).get("fabricated_twin")))
                     and text(leakage.get("twin_construction"))
                     and contrast(leakage.get("paired_contrast")) and paired
                     and (metric(leakage.get("human_low_knowledge_baseline"))
                          or leakage.get("conditional_on_twin_adequacy") is True))),
        "DF-5": (likeness.get("claimed") is False
                 or (likeness.get("claimed") is True
                     and likeness.get("separate_from_task_success") is True
                     and records(likeness.get("lexical_metrics"), metric)
                     and records(likeness.get("judge_metrics"), metric)
                     and metric(controls.get("human_human")) and metric(controls.get("proxy_proxy"))
                     and sensitivity_ok)),
        "DF-6": (metric(reliability.get("R1")) and metric(reliability.get("R2"))
                 and reliability.get("cross_level_improvement_inferred") is False
                 and text(reliability.get("profile_informativeness_evidence"))
                 and type(coverage.get("n")) is int and coverage["n"] > 0
                 and text(coverage.get("variance_stability")) and text(coverage.get("bias_assessment"))),
        "DF-7": (calibration.get("claimed") is False
                 or (calibration.get("claimed") is True
                     and calibration.get("type") in ("direct_fidelity", "transferable_structure")
                     and records(calibration.get("reference_questions"), text)
                     and type(calibration.get("cold_start")) is bool
                     and type(calibration.get("target_has_human_data")) is bool
                     and calibration["cold_start"] != calibration["target_has_human_data"]
                     and calibration.get("level") in ("individual", "distribution"))),
    }


def reject_constant(value):
    raise ValueError("Non-finite JSON number: " + value)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key: " + key)
        result[key] = value
    return result


def main():
    if len(sys.argv) != 2:
        print("usage: " + Path(sys.argv[0]).name + " <simulator-evaluation.json>", file=sys.stderr)
        return 2
    try:
        with open(sys.argv[1], encoding="utf-8") as stream:
            state = json.load(stream, parse_constant=reject_constant, object_pairs_hook=unique_object)
        if not isinstance(state, dict):
            raise ValueError("Simulator evaluation must be a JSON object")
    except (OSError, ValueError) as error:
        print(json.dumps({"result": "ERROR", "error": str(error)}))
        return 2
    gates = check(state)
    failed = [gate for gate, passed in gates.items() if not passed]
    print(json.dumps({"checker": "decision-fidelity-check", "result": "FAIL" if failed else "PASS",
                      "gates": {gate: "PASS" if passed else "FAIL" for gate, passed in gates.items()},
                      "passed": len(gates) - len(failed), "failed": len(failed),
                      "total": len(gates), "failed_gates": failed}, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
