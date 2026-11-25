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


def horizons(d):
    return all(type(d.get(key)) is int and d[key] > 0 for key in ('k', 'm'))


def interval_valid(value):
    i = obj(value)
    bounds = i.get('bounds')
    if not (i.get('type') in ('delta_method_ci', 'credible_interval', 'confidence_interval')
            and isinstance(bounds, list) and len(bounds) == 2
            and all(number(v) for v in bounds) and bounds[0] <= bounds[1]
            and number(i.get('full_data_reference'))
            and type(i.get('contains_reference')) is bool):
        return False
    return i['contains_reference'] == (bounds[0] <= i['full_data_reference'] <= bounds[1])


def fit_valid(value):
    f = obj(value)
    if f.get('reports_pass_power_and_auc') is False:
        return True
    return (f.get('reports_pass_power_and_auc') is True and f.get('same_fit') is True
            and text(f.get('pass_power_fit_id'))
            and f.get('pass_power_fit_id') == f.get('auc_fit_id'))


def claim_types_valid(c):
    kinds = c.get('claim_types')
    return (records(kinds, lambda kind: kind in ('absolute_inflation', 'ranking_reorder'))
            and len(set(kinds)) == len(kinds) and c.get('claims_separated') is True)


def check(state):
    d = obj(state)
    estimator, diagnostic = obj(d.get('estimator')), obj(d.get('improvability'))
    c = obj(d.get('contamination'))
    decomposition, calibration = obj(c.get('decomposition')), obj(c.get('calibration'))
    baseline = obj(c.get('clean_baseline'))
    kinds = c.get('claim_types')
    ranking_claim = isinstance(kinds, list) and 'ranking_reorder' in kinds
    return {
        'LB-0': (horizons(d) and type(d.get('extrapolation')) is bool
                 and d['extrapolation'] == (d['k'] > d['m'])),
        'LB-1': (horizons(d) and (d['k'] <= d['m']
                 or (text(estimator.get('type'))
                     and estimator.get('type') not in ('naive', 'y/m', 'direct', 'combinatorial')
                     and estimator.get('naive_y_over_m_transform_only') is False
                     and text(estimator.get('prior_family'))
                     and text(estimator.get('component_selection'))))),
        'LB-2': interval_valid(d.get('interval')),
        'LB-3': (diagnostic.get('used') is False
                 or (diagnostic.get('used') is True
                     and diagnostic.get('fitted_prior_dependence_disclosed') is True
                     and text(diagnostic.get('dependence_description')))),
        'LB-4': (horizons(d) and (d['k'] > d['m']
                 or (estimator.get('direct_or_combinatorial_prioritized') is True
                     and estimator.get('unconditional_mixture_superiority_claim') is False))),
        'LB-5': fit_valid(d.get('metrics_fit')),
        'CT-0': claim_types_valid(c),
        'CT-1': (type(c.get('discusses_ranking')) is bool
                 and (not ranking_claim or c['discusses_ranking'] is True)
                 and (c['discusses_ranking'] is False
                      or number(c.get('paraphrase_rank_correlation'), -1, 1))),
        'CT-2': (number(decomposition.get('uniform'))
                 and number(decomposition.get('differential'))
                 and (not ranking_claim or
                      (decomposition.get('differential_evidence') is True
                       and text(decomposition.get('evidence_description'))))),
        'CT-3': (number(calibration.get('known_dose'))
                 and number(calibration.get('known_dose_result'))
                 and number(calibration.get('negative_control_result'))),
        'CT-4': (text(baseline.get('reference')) and number(baseline.get('gap'))
                 and number(c.get('paraphrase_gap'))
                 and baseline.get('used_as_reference') is True),
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
    report = {'checker': 'lowbudget-eval-check', 'result': 'FAIL' if failed else 'PASS',
              'gates': {gate: 'PASS' if passed else 'FAIL' for gate, passed in gates.items()},
              'passed': len(gates)-len(failed), 'failed': len(failed), 'total': len(gates),
              'failed_gates': failed}
    if error is not None:
        report['error'] = error
    print(json.dumps(report, indent=2))
    return int(bool(failed))


if __name__ == '__main__':
    sys.exit(main())
