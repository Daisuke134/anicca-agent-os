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
    metrics, claim = obj(d.get('metrics')), obj(d.get('claim'))
    pre, effects = obj(d.get('precommitment')), obj(d.get('effects'))
    audit = obj(d.get('mismatch_audit'))
    definitions = [obj(metrics.get(key)).get('definition')
                   for key in ('adoption', 'engagement', 'adherence')]
    return {
        'FC-0': (all(text(v) for v in definitions)
                 and len({v.strip().casefold() for v in definitions}) == 3),
        'FC-1': d.get('allocation_method') in ('randomized', 'nonrandomized'),
        'FC-2': (d.get('fit_type') in ('perceived', 'personalized', 'none')
                 and claim.get('fit_type') == d['fit_type']
                 and type(d.get('recommendations_change_with_answers')) is bool
                 and d['recommendations_change_with_answers'] == (d['fit_type'] == 'personalized')),
        'FC-3': (pre.get('used') is False
                 or (pre.get('used') is True
                     and all(text(pre.get(key)) for key in ('when', 'where', 'trigger')))),
        'FC-4': (all(number(obj(effects.get(key)).get('value'))
                     and text(obj(effects.get(key)).get('measure'))
                     and type(obj(effects.get(key)).get('improvement_supported')) is bool
                     for key in ('starts', 'opens', 'active_days'))
                 and text(claim.get('text'))
                 and claim.get('outcome_type') in ('starts', 'opens', 'active_days', 'habit', 'continuation')
                 and (claim['outcome_type'] not in ('habit', 'continuation')
                      or obj(effects.get('active_days')).get('improvement_supported') is True)),
        'FC-5': (text(audit.get('self_reported_needs'))
                 and text(audit.get('recommended_categories'))
                 and text(audit.get('comparison_result'))),
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
    report = {'checker': 'fit-ceiling-check', 'result': 'FAIL' if failed else 'PASS',
              'gates': {gate: 'PASS' if passed else 'FAIL' for gate, passed in gates.items()},
              'passed': len(gates)-len(failed), 'failed': len(failed), 'total': len(gates),
              'failed_gates': failed}
    if error is not None:
        report['error'] = error
    print(json.dumps(report, indent=2))
    return int(bool(failed))


if __name__ == '__main__':
    sys.exit(main())
