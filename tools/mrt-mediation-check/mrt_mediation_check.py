#!/usr/bin/env python3
"""Deterministic MM-0..MM-5 reporting gates; Python standard library only."""
import itertools
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


def factorial_evidence(value):
    value = obj(value)
    factors = value.get('factors')
    if not (isinstance(factors, dict) and len(factors) >= 2
            and all(text(name) and records(levels, text) and len(levels) >= 2
                    and len(set(levels)) == len(levels) for name, levels in factors.items())):
        return False
    names = sorted(factors)
    arms = value.get('arms')
    if not records(arms, lambda arm: isinstance(arm, dict) and set(arm) == set(names)
                   and all(text(arm[name]) and arm[name] in factors[name] for name in names)):
        return False
    actual = [tuple(arm[name] for name in names) for arm in arms]
    # Count first to avoid expanding a huge declared Cartesian product.
    complete = (len(actual) == math.prod(len(factors[name]) for name in names)
                and len(set(actual)) == len(actual)
                and set(actual) == set(itertools.product(*(factors[name] for name in names))))
    return (complete and records(value.get('interaction_contrasts'), text)
            and value.get('preregistered') is True
            and records(value.get('selection_basis'), text)
            and 'interaction' in value['selection_basis'])


def mediation_evidence(d):
    claim = d.get('mediation_claim')
    distal = d.get('distal_claim')
    if type(claim) is not bool or type(distal) is not bool:
        return False
    effects = d.get('distal_effects')
    if distal and not (obj(obj(d.get('design')).get('outcomes')).get('distal_present') is True
                       and records(effects, lambda item: item in ('direct', 'indirect', 'total'))):
        return False
    if not claim:
        return (obj(d.get('estimator')).get('numeric_mediation_claim') is False
                and (not distal or effects == ['total']))
    mediator = obj(d.get('mediator'))
    estimands = obj(d.get('estimands'))
    return (text(mediator.get('definition')) and text(mediator.get('measurement_time'))
            and mediator.get('nearest_after_treatment') is True
            and all(text(estimands.get(key)) for key in ('direct', 'indirect', 'total'))
            and records(d.get('identification_assumptions'), text))


def randomization_evidence(value):
    value = obj(value)
    if value.get('fixed') is True:
        return True
    clipping = obj(value.get('clipping'))
    return (value.get('fixed') is False and text(value.get('algorithm_version'))
            and number(clipping.get('lower'), 0, 1) and number(clipping.get('upper'), 0, 1)
            and clipping['lower'] < clipping['upper']
            and value.get('actual_probability_logged') is True
            and value.get('fixed_probability_assumed') is False)


def check(state):
    d = obj(state)
    design = obj(d.get('design'))
    outcomes = obj(design.get('outcomes'))
    estimator = obj(d.get('estimator'))
    proximal = obj(d.get('proximal_outcomes'))
    treatment = design.get('treatment_type')
    return {
        'MM-0': (treatment in ('binary', 'categorical', 'factorial')
                 and records(outcomes.get('proximal_types'), text)
                 and type(outcomes.get('distal_present')) is bool),
        'MM-1': mediation_evidence(d),
        'MM-2': (estimator.get('robustness') in ('multiply_robust', 'doubly_robust', 'none')
                 and type(estimator.get('cross_fitting')) is bool
                 and type(estimator.get('numeric_mediation_claim')) is bool
                 and (estimator['numeric_mediation_claim'] is False
                      or (estimator['robustness'] != 'none' and d.get('mediation_claim') is True))),
        'MM-3': ((treatment == 'factorial' and factorial_evidence(d.get('factorial')))
                 or (treatment in ('binary', 'categorical')
                     and obj(d.get('factorial')).get('not_applicable') is True)),
        'MM-4': randomization_evidence(d.get('randomization')),
        'MM-5': (records(proximal.get('engagement'), text) and records(proximal.get('target_behavior'), text)
                 and proximal.get('cross_outcome_inference') is False
                 and d.get('feasibility_as_efficacy') is False),
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
    report = {'checker': 'mrt-mediation-check', 'result': 'FAIL' if failed else 'PASS',
              'gates': {gate: 'PASS' if passed else 'FAIL' for gate, passed in gates.items()},
              'passed': len(gates)-len(failed), 'failed': len(failed), 'total': len(gates),
              'failed_gates': failed}
    if error is not None:
        report['error'] = error
    print(json.dumps(report, indent=2))
    return int(bool(failed))


if __name__ == '__main__':
    sys.exit(main())
