#!/usr/bin/env python3
"""Deterministic section-2 reporting gates; Python standard library only."""
import json
import math
import sys
from pathlib import Path


def text(value):
    return isinstance(value, str) and bool(value.strip())


def number(value, lower=-math.inf, upper=math.inf):
    return (type(value) in (int, float)
            and (type(value) is int or math.isfinite(value)) and lower <= value <= upper)


def obj(value):
    return value if isinstance(value, dict) else {}


def check(state):
    d = obj(state)
    claim, outcome = obj(d.get('claim')), obj(d.get('distal_outcome'))
    points, uncertainty = obj(d.get('decision_points')), obj(d.get('uncertainty'))
    routine = obj(d.get('routine_elicitation'))
    bounds = d.get('probability_bounds')
    kinds = ('proximal', 'distal')
    return {
        'DP-0': (d.get('estimand_type') in kinds
                 and claim.get('outcome_type') in kinds
                 and ((d['estimand_type'] != 'distal' and claim['outcome_type'] != 'distal')
                      or (text(outcome.get('name')) and text(outcome.get('measurement_time'))))),
        'DP-1': (d.get('policy_class') == 'stochastic'
                 and isinstance(bounds, list) and len(bounds) == 2
                 and all(number(v) for v in bounds) and 0 < bounds[0] <= bounds[1] < 1),
        'DP-2': (type(points.get('count')) is int and points['count'] > 0
                 and type(points.get('many')) is bool and text(points.get('classification_reason'))
                 and (points['many'] is False or text(d.get('stabilization')))),
        'DP-3': (type(claim.get('optimal')) is bool
                 and uncertainty.get('type') in ('simultaneous_band', 'pointwise', 'none', 'other')
                 and (uncertainty['type'] == 'simultaneous_band'
                      or text(uncertainty.get('nonuse_reason')))
                 and not (claim['optimal'] is True and uncertainty['type'] == 'pointwise')),
        'DP-4': (routine.get('used') is False
                 or (routine.get('used') is True
                     and type(routine.get('playback_check')) is bool
                     and text(routine.get('fragmentation_audit'))
                     and routine.get('availability_receptivity_separated') is True
                     and text(routine.get('availability_record'))
                     and text(routine.get('receptivity_record')))),
        'DP-5': (text(claim.get('text')) and d.get('estimand_type') in kinds
                 and claim.get('outcome_type') == d['estimand_type']
                 and d.get('measured_outcome_type') == claim['outcome_type']),
    }


def reject_constant(value):
    raise ValueError('Non-finite JSON number: ' + value)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate JSON key: ' + key)
        result[key] = value
    return result


def main():
    error = None
    state = {}
    try:
        if len(sys.argv) != 2:
            raise ValueError('usage: ' + Path(sys.argv[0]).name + ' <state.json>')
        with open(sys.argv[1], encoding='utf-8') as stream:
            state = json.load(stream, parse_constant=reject_constant, object_pairs_hook=unique_object)
        if not isinstance(state, dict):
            raise ValueError('State must be a JSON object')
    except (OSError, ValueError, RecursionError) as exc:
        error = str(exc)
        state = {}
    gates = check(state)
    failed = [gate for gate, passed in gates.items() if not passed]
    report = {'checker': 'distal-policy-check', 'result': 'FAIL' if failed else 'PASS',
              'gates': {gate: 'PASS' if passed else 'FAIL' for gate, passed in gates.items()},
              'passed': len(gates)-len(failed), 'failed': len(failed), 'total': len(gates),
              'failed_gates': failed}
    if error is not None:
        report['error'] = error
    print(json.dumps(report, indent=2))
    return int(bool(failed))


if __name__ == '__main__':
    sys.exit(main())
