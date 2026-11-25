#!/usr/bin/env python3
"""Offline PA-0..PA-5 document gates. Standard library only."""
import json
import math
import sys


def number(value):
    return type(value) is int or (type(value) is float and math.isfinite(value))


def text(value):
    return isinstance(value, str) and bool(value.strip())


def section(data, name):
    value = data.get(name)
    return value if isinstance(value, dict) else {}


def check(data):
    b = section(data, 'baseline')
    comparable = (text(b.get('name')) and b.get('non_llm') is True
                  and b.get('strongest_comparator') is True
                  and number(b.get('synthetic_score')) and number(b.get('baseline_score'))
                  and b.get('higher_is_better') in (True, False)
                  and type(b.get('higher_is_better')) is bool)
    below = comparable and ((b['synthetic_score'] < b['baseline_score']) if b['higher_is_better']
                            else (b['synthetic_score'] > b['baseline_score']))
    pa0 = comparable and (not below or (b.get('conclusion') == 'below-baseline'
                                      and b.get('used_as_evidence') is False))
    a = section(data, 'human_anchor')
    pa1 = (a.get('kind') in ('same-people', 'other-people') and number(a.get('score'))
           and text(a.get('reference')))
    s = section(data, 'joint_structure')
    pa2 = (all(text(s.get(k)) for k in ('item_correlations', 'latent_structure', 'reliability'))
           and number(s.get('within_person_sd_ratio')) and s['within_person_sd_ratio'] >= 0
           and s.get('marginals_only_validity_claim') is False)
    n = section(data, 'negative_controls')
    pa3 = (n.get('human_null_established') is True and text(n.get('reference'))
           and type(n.get('paths_tested')) is int and n['paths_tested'] > 0
           and type(n.get('synthetic_significant_paths')) is int
           and 0 <= n['synthetic_significant_paths'] <= n['paths_tested'])
    h = section(data, 'held_out')
    pa4 = (h.get('training_data') == 'synthetic' and h.get('test_data') == 'held-out-human'
           and text(h.get('metric')) and number(h.get('value')) and text(h.get('split_reference')))
    g = section(data, 'segment_gap')
    pa5 = (number(g.get('synthetic_to_real_ratio')) and g['synthetic_to_real_ratio'] >= 0
           and type(g.get('decision_reversal')) is bool and text(g.get('comparison')))
    messages = [
        'strongest non-LLM comparison; below-baseline evidence must be withheld',
        'named same-people or other-people human anchor with measured score',
        'joint structure and measured within-person SD ratio; no marginal-only validity claim',
        'human-null negative controls and synthetic significant-path count',
        'synthetic training evaluated on held-out humans, preserving negative metrics',
        'measured segment-gap inflation and decision-reversal inspection',
    ]
    return [(f'PA-{i}', bool(ok), messages[i]) for i, ok in enumerate((pa0, pa1, pa2, pa3, pa4, pa5))]


def main():
    if len(sys.argv) != 2:
        print('usage: psychometric_audit_check.py <state.json>', file=sys.stderr)
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
