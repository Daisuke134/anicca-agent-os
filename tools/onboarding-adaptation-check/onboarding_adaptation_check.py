#!/usr/bin/env python3
"""Deterministic section-3 gates, 2026-11-18. Python stdlib only."""
import json
import math
import sys
from pathlib import Path


def text(value):
    return isinstance(value, str) and bool(value.strip())


def number(value, lower=0, upper=math.inf):
    return type(value) in (int, float) and (type(value) is int or math.isfinite(value)) and lower <= value <= upper


def obj(value):
    return value if isinstance(value, dict) else {}


def records(value, predicate):
    return isinstance(value, list) and bool(value) and all(predicate(item) for item in value)


def strings(value):
    return records(value, text)


def performance(value):
    value = obj(value)
    return text(value.get("metric")) and number(value.get("value"), -math.inf) and text(value.get("evidence"))


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
        print("usage: " + Path(sys.argv[0]).name + " <surface-state.json>", file=sys.stderr)
        return 2
    try:
        with open(sys.argv[1], encoding="utf-8") as stream:
            state = json.load(stream, parse_constant=reject_constant, object_pairs_hook=unique_object)
        if not isinstance(state, dict):
            raise ValueError("Surface state must be a JSON object")
    except (OSError, ValueError) as error:
        print(json.dumps({"result": "ERROR", "error": str(error)}))
        return 2
    gates = check(state)
    failed = [gate for gate, passed in gates.items() if not passed]
    print(json.dumps({"checker": CHECKER, "result": "FAIL" if failed else "PASS",
                      "gates": {gate: "PASS" if passed else "FAIL" for gate, passed in gates.items()},
                      "passed": len(gates) - len(failed), "failed": len(failed),
                      "total": len(gates), "failed_gates": failed}, indent=2))
    return 1 if failed else 0

CHECKER = "onboarding-adaptation-check"
SOURCES = ("self", "algorithm", "default-unchanged")


def check(state):
    d = obj(state)
    goals = obj(d.get("goals"))
    routing = obj(d.get("routing"))
    tiers = obj(routing.get("baseline_tiers"))
    assignments = obj(routing.get("assignments"))
    rows = goals.get("users")
    source_records = records(rows, lambda row: isinstance(row, dict)
                            and text(row.get("user_id")) and row.get("source") in SOURCES)
    valid_assignments = (all(text(tiers.get(t)) for t in ("low", "middle", "high"))
                         and set(tiers) == set(assignments)
                         and all(text(definition) for definition in tiers.values())
                         and all(records(sources, lambda v: v in SOURCES) for sources in assignments.values()))
    routing_ok = (valid_assignments
                  and set(assignments["low"]) != {"self"}
                  and set(assignments["high"]) != {"algorithm"})
    if routing_ok and isinstance(rows, list):
        routing_ok = all(isinstance(row, dict) and text(row.get("tier"))
                         and row["tier"] in assignments
                         and row.get("source") in assignments[row["tier"]] for row in rows)
    algorithm = obj(d.get("algorithm"))
    algorithm_referenced = ((isinstance(rows, list) and any(obj(row).get("source") == "algorithm" for row in rows))
                            or any(isinstance(s, list) and "algorithm" in s for s in assignments.values()))
    algorithm_ok = ((algorithm.get("used") is False and not algorithm_referenced)
                    or (algorithm.get("used") is True and text(algorithm.get("observation_window"))
                        and text(algorithm.get("calculation"))))
    adaptation = obj(d.get("adaptation"))
    adaptation_ok = (adaptation.get("used") is False or
                     (adaptation.get("used") is True and strings(adaptation.get("first_run_signals"))
                      and text(adaptation.get("intent")) and number(adaptation.get("confidence"), 0, 1)
                      and text(adaptation.get("low_confidence_baseline_fallback"))
                      and text(adaptation.get("decision_log_path"))))
    evaluation = obj(d.get("evaluation"))
    values = evaluation.get("effects")
    evaluation_ok = ((evaluation.get("effects_present") is False and values == []) or
                     (evaluation.get("effects_present") is True
                      and records(values, lambda row: isinstance(row, dict)
                                  and text(row.get("metric")) and number(row.get("value"), -math.inf)
                                  and row.get("source") in ("production", "simulation")
                                  and row.get("reported_as") == row.get("source"))))
    return {
        "OG-0": all(text(d.get(k)) for k in ("surface_name", "onboarding_owner", "source_path")),
        "OG-1": (source_records and goals.get("all_users_covered") is True
                 and len({row["user_id"] for row in rows}) == len(rows)),
        "OG-2": routing_ok,
        "OG-3": algorithm_ok,
        "OG-4": adaptation_ok,
        "OG-5": evaluation_ok,
    }


if __name__ == "__main__":
    sys.exit(main())
