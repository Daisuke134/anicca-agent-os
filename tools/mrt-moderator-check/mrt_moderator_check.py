#!/usr/bin/env python3
"""Offline MV-0..MV-5 document gates. Standard library only."""
import json
import math
import sys


def text(value):
    return isinstance(value, str) and bool(value.strip())


def names(value):
    return isinstance(value, list) and bool(value) and all(text(x) for x in value) and len(set(value)) == len(value)


def section(data, key):
    value = data.get(key)
    return value if isinstance(value, dict) else {}


def number(value):
    return type(value) is int or (type(value) is float and math.isfinite(value))


def check(data):
    d = section(data, 'declaration')
    mv0 = (names(d.get('moderators')) and names(d.get('stratification_factors'))
           and names(d.get('strata'))
           and (d.get('before_analysis') is True or
                (d.get('before_analysis') is False and d.get('claim_kind') == 'exploratory')))
    c = section(data, 'consistency')
    strata = d.get('strata') if names(d.get('strata')) else []
    effects = c.get('stratum_effects')
    complete = (bool(strata) and isinstance(effects, dict) and set(effects) == set(strata)
                and all(v in ('positive', 'negative', 'null') for v in effects.values()))
    consistent = complete and len(set(effects.values())) == 1 and 'null' not in effects.values()
    mv1 = complete and ((consistent and c.get('conclusion') == 'consistent') or
                        (not consistent and c.get('conclusion') == 'inconsistent'
                         and c.get('general_moderator_claim') is False))
    p = section(data, 'surface_personalization')
    mv2 = (text(p.get('factor')) and p.get('tested_independently') is True
           and p.get('result') in ('positive', 'negative', 'null')
           and p.get('reported_result') == p.get('result')
           and p.get('personalization_alone_is_evidence') is False)
    v = section(data, 'policy_value')
    mv3 = (v.get('claimed') is False or
           (v.get('claimed') is True and v.get('policy_assignment_randomized') is True
            and v.get('control') == 'random-allocation' and text(v.get('comparison_reference'))
            and v.get('forecasting_only') is False))
    o = section(data, 'outcomes')
    rows = o.get('results')
    mv4 = (names(o.get('declared_proximal')) and isinstance(rows, dict)
           and set(rows) == set(o['declared_proximal'])
           and all(isinstance(r, dict) and number(r.get('effect'))
                   and r.get('result') in ('positive', 'negative', 'null') for r in rows.values())
           and o.get('generalized_to_other_outcomes') is False)
    power = section(data, 'power')
    mv5 = (type(power.get('adequate')) is bool and text(power.get('assessment'))
           and type(power.get('controlled')) is bool
           and power.get('claim_kind') in ('efficacy', 'feasibility')
           and (power['adequate'] or power['claim_kind'] == 'feasibility')
           and (power['controlled'] or power['claim_kind'] != 'efficacy'))
    messages = [
        'moderators and strata declared before analysis or explicitly exploratory',
        'complete declared strata; inconsistent effects cannot support a general moderator claim',
        'surface personalization independently tested and null reported honestly',
        'policy value requires randomized policy comparison against random allocation',
        'all declared proximal outcomes separately reported without cross-outcome generalization',
        'power assessed; underpowered and uncontrolled results cannot claim efficacy',
    ]
    return [(f'MV-{i}', bool(ok), messages[i]) for i, ok in enumerate((mv0, mv1, mv2, mv3, mv4, mv5))]


def main():
    if len(sys.argv) != 2:
        print('usage: mrt_moderator_check.py <state.json>', file=sys.stderr)
        return 2
    try:
        with open(sys.argv[1], encoding='utf-8') as source:
            data = json.load(source)
        if not isinstance(data, dict):
            raise ValueError('top-level JSON must be an object')
    except (OSError, ValueError) as error:
        print(f'ERROR {error}', file=sys.stderr)
        return 2
    results = check(data)
    for gate, passed, reason in results:
        print(f'{"PASS" if passed else "FAIL"} {gate} {reason}')
    passed = sum(item[1] for item in results)
    print(f'RESULT {"PASS" if passed == 6 else "FAIL"} pass={passed}/6 fails={6-passed}')
    return 0 if passed == 6 else 1


if __name__ == '__main__':
    sys.exit(main())
