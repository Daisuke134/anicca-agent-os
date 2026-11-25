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


def records(value, predicate):
    return isinstance(value, list) and bool(value) and all(predicate(row) for row in value)


def interval(value):
    return (isinstance(value, list) and len(value) == 2
            and all(number(v) for v in value) and value[0] <= value[1])


def comparison_valid(value):
    c = obj(value)
    if c.get('performed') is False:
        return True
    left, right = obj(c.get('left')), obj(c.get('right'))
    if not (c.get('performed') is True and text(c.get('metric'))
            and text(left.get('tradition')) and text(right.get('tradition'))
            and left['tradition'] != right['tradition']
            and interval(left.get('ci')) and interval(right.get('ci'))):
        return False
    order = ('left_below_right' if left['ci'][1] < right['ci'][0] else
             'right_below_left' if right['ci'][1] < left['ci'][0] else 'overlap')
    return c.get('ci_order') == order


def check(state):
    d = obj(state)
    p, cv = obj(d.get('predictor')), obj(d.get('validation'))
    cal, sensitivity = obj(d.get('calibration')), obj(d.get('sensitivity'))
    mechanisms, outcome = obj(d.get('mechanisms')), obj(d.get('outcome'))
    measurement = obj(d.get('no_reminder_measurement'))
    return {
        'BT-0': (p.get('source_type') in ('behavioural_trace', 'self_report', 'mixed')
                 and type(p.get('retention_or_effect_claim')) is bool
                 and not (p.get('source_type') == 'self_report'
                          and p.get('retention_or_effect_claim') is True)),
        'BT-1': (cv.get('unit') == 'user' and cv.get('method') in ('cv', 'holdout')
                 and cv.get('grouped_by_learner') is True),
        'BT-2': (cal.get('metric') in ('ece', 'mce', 'brier_score', 'log_loss',
                                       'calibration_slope', 'calibration_intercept')
                 and number(cal.get('value'))
                 and (cal['metric'].lower() != 'ece' or number(cal['value'], 0, 1))),
        'BT-3': (text(sensitivity.get('proximity_contamination'))
                 and sensitivity.get('excluded_and_recomputed') is True
                 and text(sensitivity.get('metric')) and number(sensitivity.get('value'))),
        'BT-4': comparison_valid(d.get('common_metric_comparison')),
        'HB-0': all(type(mechanisms.get(key)) is bool for key in
                    ('streak', 'freeze_or_emergency_reserve', 'social', 'push', 'reward')),
        'HB-1': (outcome.get('claimed_type') in ('retention', 'autonomous_habit')
                 and outcome.get('measured_type') in ('retention', 'autonomous_habit')
                 and not (outcome.get('claimed_type') == 'autonomous_habit'
                          and outcome.get('measured_type') == 'retention')),
        'HB-2': (outcome.get('claimed_type') == 'retention'
                 or (outcome.get('claimed_type') == 'autonomous_habit'
                     and measurement.get('reminders_absent') is True
                     and text(measurement.get('continuation_metric'))
                     and number(measurement.get('value'))
                     and text(measurement.get('observation_period')))),
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
    report = {'checker': 'trace-validity-check', 'result': 'FAIL' if failed else 'PASS',
              'gates': {gate: 'PASS' if passed else 'FAIL' for gate, passed in gates.items()},
              'passed': len(gates)-len(failed), 'failed': len(failed), 'total': len(gates),
              'failed_gates': failed}
    if error is not None:
        report['error'] = error
    print(json.dumps(report, indent=2))
    return int(bool(failed))


if __name__ == '__main__':
    sys.exit(main())
