#!/usr/bin/env python3
"""Deterministic PS-0..PS-5 reporting gates; Python standard library only."""
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


def attribute_provenance(claim):
    claim = obj(claim)
    if claim.get('type') != 'attribute':
        return claim.get('type') in ('stance', 'ranking')
    if claim.get('enriched') is False:
        return True
    return (claim.get('enriched') is True and text(claim.get('source'))
            and claim.get('audit') in ('supported', 'partially_supported', 'unsupported')
            and type(claim.get('fabrication')) is bool
            and type(claim.get('stereotyping')) is bool)


def prediction_evidence(value):
    value = obj(value)
    correlations = value.get('correlations')
    return (type(value.get('study_count')) is int and value['study_count'] > 0
            and type(value.get('participant_count')) is int and value['participant_count'] > 0
            and records(correlations, lambda row: text(obj(row).get('metric'))
                        and number(obj(row).get('value'), -1, 1))
            and len({row['metric'] for row in correlations}) == len(correlations)
            and number(value.get('minimum_correlation'), -1, 1)
            and value['minimum_correlation'] == min(row['value'] for row in correlations)
            and type(value.get('fitted_not_forecast')) is bool)


def check(state):
    d = obj(state)
    claims = d.get('claims')
    audit = obj(d.get('stability_audit'))
    revisions = audit.get('revisions')
    mechanism = obj(d.get('mechanism'))
    kinds = ('neutral_paraphrase', 'substantive_addition', 'multimodal')
    return {
        'PS-0': records(claims, lambda row: obj(row).get('type') in ('stance', 'attribute', 'ranking')
                        and text(obj(row).get('population'))),
        'PS-1': (audit.get('neutral_present') is True
                 and records(revisions, lambda row: obj(row).get('type') in kinds
                             and number(obj(row).get('directional_shift'))
                             and number(obj(row).get('transition_rate'), 0, 1))
                 and sorted(row['type'] for row in revisions) == sorted(kinds)),
        'PS-2': (text(mechanism.get('name')) and isinstance(mechanism.get('settings'), dict)
                 and bool(mechanism['settings'])
                 and all(text(key) and value is not None for key, value in mechanism['settings'].items())),
        'PS-3': (records(claims, attribute_provenance) and d.get('diversity_as_validity') is False),
        'PS-4': (d.get('provenance_claimed_as_realism') is False
                 and (d.get('realism_claim') is False
                      or (d.get('realism_claim') is True and text(d.get('human_calibration_reference'))))),
        'PS-5': (d.get('predictive_claim') is False
                 or (d.get('predictive_claim') is True and prediction_evidence(d.get('human_studies')))),
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
    report = {'checker': 'provenance-stability-check', 'result': 'FAIL' if failed else 'PASS',
              'gates': {gate: 'PASS' if passed else 'FAIL' for gate, passed in gates.items()},
              'passed': len(gates)-len(failed), 'failed': len(failed), 'total': len(gates),
              'failed_gates': failed}
    if error is not None:
        report['error'] = error
    print(json.dumps(report, indent=2))
    return int(bool(failed))


if __name__ == '__main__':
    sys.exit(main())
