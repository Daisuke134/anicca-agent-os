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

CHECKER = "receptivity-check"


def check(state):
    d = obj(state)
    calibration = obj(d.get("calibration"))
    rates = obj(d.get("rates"))
    receptivity = obj(d.get("receptivity"))
    effect = obj(d.get("effects"))
    self_trigger = obj(d.get("self_trigger"))
    transfer = obj(d.get("transfer"))
    horizons = receptivity.get("horizons_minutes")
    horizon_set = (records(horizons, lambda v: number(v) and v > 0)
                   and len(set(horizons)) >= 2)
    label_handling = (receptivity.get("label_shortage_handling_used") is False or
                      (receptivity.get("label_shortage_handling_used") is True
                       and text(receptivity.get("label_shortage_handling"))))
    outcomes = effect.get("outcomes")
    separated = records(outcomes, lambda row: isinstance(row, dict)
                        and text(row.get("trigger_type"))
                        and row.get("outcome_type") in ("psychological", "physiological", "behavioral")
                        and text(row.get("record")))
    controls = effect.get("control_arms")
    controlled = (effect.get("trigger_effect_claimed") is False or
                  (effect.get("trigger_effect_claimed") is True and
                   records(controls, lambda arm: isinstance(arm, dict)
                           and text(arm.get("type")) and text(arm.get("record")))))
    no_transfer = transfer.get("used") is False
    return {
        "TR-0": all(text(d.get(k)) for k in ("surface_name", "trigger_owner", "source_path")),
        "TR-1": all(text(calibration.get(k)) for k in
                    ("period", "individual_threshold_method", "exclusion_rules", "refractory_period")),
        "TR-2": (number(rates.get("usable_decision_fraction"), 0, 1)
                 and number(rates.get("triggers_per_day"))
                 and number(rates.get("detection_adherence"), 0, 1)
                 and number(rates.get("intervention_adherence"), 0, 1)),
        "TR-3": (horizon_set and label_handling and
                 ((receptivity.get("form") == "time_to_event" and text(receptivity.get("time_to_event_record")))
                  or (receptivity.get("form") == "multi_horizon" and text(receptivity.get("cross_horizon_stability"))))),
        "TR-4": separated and controlled,
        "TR-5": (self_trigger.get("present") is False or
                 (self_trigger.get("present") is True
                  and type(self_trigger.get("self_count")) is int and self_trigger["self_count"] >= 0
                  and type(self_trigger.get("automatic_count")) is int and self_trigger["automatic_count"] >= 0)),
        "CG-0": (no_transfer or (transfer.get("used") is True
                  and performance(transfer.get("within_performance"))
                  and performance(transfer.get("transfer_performance")))),
        "CG-1": (no_transfer or (transfer.get("used") is True
                  and transfer.get("feature_handling") in ("shared", "union")
                  and text(transfer.get("missing_feature_handling"))
                  and (transfer.get("warm_start_claimed") is False or
                       (transfer.get("warm_start_claimed") is True
                        and transfer.get("transfer_measured") is True
                        and performance(transfer.get("transfer_performance"))
                        and text(transfer.get("warm_start_evidence")))))),
    }


if __name__ == "__main__":
    sys.exit(main())
