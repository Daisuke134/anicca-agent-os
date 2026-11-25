#!/usr/bin/env python3
"""Offline EC-0..2 / RA-0..2 document gates; explicit as_of makes runs repeatable."""
from datetime import date
import json
import math
import sys


def obj(value):
    return value if isinstance(value, dict) else {}


def text(value):
    return isinstance(value, str) and bool(value.strip())


def number(value):
    return type(value) in (int, float) and math.isfinite(value)


def day(value):
    try:
        return date.fromisoformat(value) if isinstance(value, str) and len(value) == 10 else None
    except ValueError:
        return None


def rankings(signals, reducer):
    """Competition ranks preserve ties rather than inventing an ordering."""
    values = {name: reducer(scores) for name, scores in signals.items()}
    return {name: 1 + sum(other > score for other in values.values())
            for name, score in values.items()}


def check(d):
    d = obj(d)
    fails = []
    def gate(code, ok, message):
        if not ok:
            fails.append(f'{code} {message}')

    scores = d.get('scores')
    scores = scores if isinstance(scores, list) else []
    records = bool(scores) and all(isinstance(s, dict) for s in scores)
    def metadata(s):
        start, end = day(s.get('valid_from')), day(s.get('expires_on'))
        return (text(s.get('id')) and number(s.get('value')) and text(s.get('formality_tier'))
                and text(s.get('scope')) and start is not None and end is not None and start <= end)
    gate('EC-0', records and all(metadata(s) for s in scores)
         and len({s['id'] for s in scores}) == len(scores),
         'each score needs value, formality, scope and a valid validity window')
    agg = obj(d.get('aggregation'))
    signals = obj(agg.get('signals'))
    signal_ok = bool(signals) and all(text(k) and isinstance(v, list) and len(v) >= 2
        and all(number(x) for x in v) for k, v in signals.items())
    signal_ok = signal_ok and len({len(v) for v in signals.values()}) == 1
    ranks_ok = False
    if signal_ok:
        mean = rankings(signals, lambda xs: sum(xs) / len(xs))
        weakest = rankings(signals, min)
        reported_mean = obj(agg.get('mean_ranks'))
        reported_weakest = obj(agg.get('weakest_link_ranks'))
        ranks_ok = (all(type(x) is int for x in [*reported_mean.values(), *reported_weakest.values()])
                    and reported_mean == mean and reported_weakest == weakest
                    and (mean == weakest or agg.get('rank_disagreement_disclosed') is True))
    gate('EC-1', (agg.get('multiple_signals') is False and not signals) or (
        agg.get('multiple_signals') is True and agg.get('higher_is_better_normalized') is True and ranks_ok),
         'declare aggregation; report computed mean/weakest-link ranks and any disagreement')
    as_of = day(d.get('as_of'))
    def current(s):
        start, end, measured = (day(s.get(k)) for k in ('valid_from', 'expires_on', 'reevaluated_on'))
        if None in (start, end, measured, as_of) or not measured <= start <= end or measured > as_of:
            return False
        used = s.get('used_for_current_claim')
        return type(used) is bool and (used is False or start <= as_of <= end)
    gate('EC-2', records and all(current(s) for s in scores),
         'record reevaluation date; current claims must fall inside the score validity window')
    audit = obj(d.get('audit'))
    regime = obj(audit.get('regime'))
    gate('RA-0', audit.get('statistical_result') in ('positive', 'negative', 'inconclusive')
         and regime.get('iid_assumption') in ('met', 'violated', 'unknown')
         and type(regime.get('benchmark_size')) is int and regime['benchmark_size'] > 0
         and text(regime.get('power_at_benchmark_size')) and text(regime.get('reference_set_source')),
         'record detector result, IID validity, benchmark power and reference-set source')
    gate('RA-1', text(audit.get('provenance'))
         and audit.get('statistical_detection_separate_from_provenance') is True
         and audit.get('negative_detection_substitutes_for_provenance') is False,
         'separate statistical detection from provenance; a negative cannot replace provenance')
    gate('RA-2', type(audit.get('distribution_shift')) is bool
         and text(audit.get('suspect_validation_distribution_comparison'))
         and (audit['distribution_shift'] is False or audit.get('false_positive_risk_disclosed') is True),
         'record distribution comparison and false-positive risk under shift')
    return fails


def main():
    if len(sys.argv) != 2:
        print('usage: eval_claim_check.py <state.json>'); return 2
    try:
        with open(sys.argv[1], encoding='utf-8') as f:
            d = json.load(f)
        if not isinstance(d, dict):
            raise ValueError('state must be a JSON object')
    except (OSError, ValueError) as exc:
        print(f'ERROR {exc}', file=sys.stderr); return 2
    fails = check(d)
    for code in ('EC-0', 'EC-1', 'EC-2', 'RA-0', 'RA-1', 'RA-2'):
        print(next((f'FAIL {x}' for x in fails if x.startswith(code + ' ')), f'PASS {code}'))
    print(f"RESULT {'FAIL' if fails else 'PASS'} pass={6-len(fails)}/6 fails={len(fails)}")
    return int(bool(fails))


if __name__ == '__main__':
    sys.exit(main())
