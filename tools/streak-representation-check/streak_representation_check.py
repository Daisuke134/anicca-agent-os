#!/usr/bin/env python3
"""Offline ST-0..ST-4 document gates. Stdlib only; see README and fixtures."""
import json
import math
import sys


def obj(value):
    return value if isinstance(value, dict) else {}


def text(value):
    return isinstance(value, str) and bool(value.strip())


def rate(value):
    return type(value) in (int, float) and math.isfinite(value) and 0 <= value <= 1


def check(d):
    d = obj(d)
    fails = []
    def gate(code, ok, message):
        if not ok:
            fails.append(f'{code} {message}')

    behavior = obj(d.get('actual_behavior'))
    representation = obj(d.get('representation'))
    conditions = representation.get('conditions')
    gate('ST-0', text(behavior.get('measure')) and text(behavior.get('observation_window'))
         and isinstance(conditions, list) and all(isinstance(x, str) for x in conditions)
         and set(conditions) == {'intact', 'broken', 'no-log'}
         and representation.get('separate_from_actual_behavior') is True,
         'record actual behavior separately from intact/broken/no-log representation')
    rates = obj(d.get('continuation_rates'))
    valid = all(rate(rates.get(x)) for x in ('intact', 'broken', 'no-log'))
    gate('ST-1', valid and text(d.get('comparison_protocol'))
         and type(d.get('display_harm_recorded')) is bool
         and (rates['broken'] > rates['no-log'] or d['display_harm_recorded'] is True)
         and d.get('benefit_claim_based_only_on_intact_gap') is False,
         'compare broken with no-log; record harm when broken <= no-log')
    attribution = obj(d.get('attribution'))
    groups = attribution.get('groups')
    gate('ST-2', isinstance(groups, list) and bool(groups)
         and all(x in ('self', 'external', 'system') for x in groups)
         and attribution.get('self_external_pooled') is False
         and text(attribution.get('analysis_by_attribution')),
         'record interruption attribution and keep self separate from external')
    repair = obj(d.get('repair'))
    gate('ST-3', type(repair.get('available')) is bool
         and repair.get('may_remain_below_intact') is True
         and repair.get('equivalent_to_intact_claim') is False,
         'declare repair availability and residual deficit; never claim equivalence')
    cost = obj(d.get('consideration'))
    kinds = cost.get('types')
    gate('ST-4', type(cost.get('offered')) is bool
         and (cost.get('offered') is False or (
             isinstance(kinds, list) and bool(kinds) and all(text(x) for x in kinds)
             and cost.get('included_in_mechanism_inventory') is True)),
         'declare paid/ad/other consideration and inventory any paid protection')
    return fails


def main():
    if len(sys.argv) != 2:
        print('usage: streak_representation_check.py <state.json>'); return 2
    try:
        with open(sys.argv[1], encoding='utf-8') as f:
            d = json.load(f)
        if not isinstance(d, dict):
            raise ValueError('state must be a JSON object')
    except (OSError, ValueError) as exc:
        print(f'ERROR {exc}', file=sys.stderr); return 2
    fails = check(d)
    failed = {x.split()[0] for x in fails}
    for i in range(5):
        code = f'ST-{i}'
        print(next((f'FAIL {x}' for x in fails if x.startswith(code + ' ')), f'PASS {code}'))
    print(f"RESULT {'FAIL' if fails else 'PASS'} pass={5-len(failed)}/5 fails={len(failed)}")
    return int(bool(fails))


if __name__ == '__main__':
    sys.exit(main())
