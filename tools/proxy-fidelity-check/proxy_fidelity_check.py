#!/usr/bin/env python3
"""Offline UP/DG/FA evidence gates; standard library only."""
import json
import math
import sys


def obj(value):
    return value if isinstance(value, dict) else {}


def number(value):
    return type(value) in (int, float) and math.isfinite(value)


def rate(value):
    return number(value) and 0 <= value <= 1


def text(value):
    return isinstance(value, str) and bool(value.strip())


def check(d):
    d = obj(d)
    p = obj(d.get('proxy'))
    s = obj(d.get('simulators'))
    dist = obj(d.get('distribution'))
    g = obj(d.get('grounding'))
    calibration = obj(d.get('calibration'))
    groups = obj(d.get('subgroups'))
    facets = obj(dist.get('facets'))
    rows = s.get('results')
    rows_ok = (isinstance(rows, list) and len(rows) >= 2
               and all(isinstance(r, dict) and text(r.get('name'))
                       and number(r.get('score')) and number(r.get('cost'))
                       and r['cost'] >= 0 for r in rows))
    if rows_ok:
        rows_ok = len({r['name'] for r in rows}) == len(rows)
    spread_ok = (rows_ok and number(s.get('score_range'))
                 and math.isclose(s['score_range'], max(r['score'] for r in rows)
                                  - min(r['score'] for r in rows), abs_tol=1e-9))
    gates = [
        ('UP-0', number(p.get('fidelity_score')) and text(p.get('fidelity_metric'))
         and p.get('measured_independently_of_agent_success') is True,
         'Record proxy fidelity separately from agent success.'),
        ('UP-1', rate(p.get('premature_disclosure_rate')),
         'Record premature disclosure rate in [0,1].'),
        ('UP-2', rate(p.get('successful_episode_violation_rate'))
         and number(p.get('interaction_change')) and text(p.get('interaction_change_unit'))
         and p.get('preserved_reward_implies_harmless') is False,
         'Record successful-episode violations and interaction change; retained reward is not harmlessness.'),
        ('UP-3', spread_ok and text(s.get('cost_fidelity_selection_reason')),
         'Compare at least two simulators, measured range, cost, and selection rationale.'),
        ('DG-0', all(number(dist.get(k)) and dist[k] >= 0
                     for k in ('backward_kl', 'forward_kl', 'js')),
         'Record backward KL, forward KL and JS separately.'),
        ('DG-1', all(all(number(obj(facets.get(f)).get(k))
                             and obj(facets.get(f))[k] >= 0
                             for k in ('capture', 'miss', 'hallucinate'))
                     for f in ('Requests', 'Responses', 'Context', 'Style', 'DAMSL', 'SGD')),
         'Record capture/miss/hallucinate for all six facets.'),
        ('DG-2', type(s.get('ensemble_used')) is bool
         and (s['ensemble_used'] is False or
              (rows_ok and text(s.get('complementarity_evidence')))),
         'Explicitly declare ensemble use and its distributional complementarity evidence.'),
        ('DG-3', g.get('source_type') in ('real-data-profile', 'handwritten-directive', 'ungrounded')
         and all(text(g.get(k)) for k in ('source_description', 'formalism_ceiling_check',
                                         'directive_amplification_check', 'anti_leakage_control')),
         'Declare grounding source, ceiling/amplification checks and anti-leakage control.'),
        ('FA-0', all(number(calibration.get(k)) for k in ('easy', 'medium', 'hard'))
         and text(d.get('calibration_metric')),
         'Record signed calibration error separately for easy, medium and hard bands.'),
        ('FA-1', all(number(groups.get(k)) for k in ('JP', 'EN'))
         and text(d.get('subgroup_metric')),
         'Record subgroup proxy quality, including JP and EN.'),
        ('FA-2', text(d.get('conversation_artifact_check')),
         'Record a conversation-artifact inspection result.'),
    ]
    return gates


def main():
    if len(sys.argv) != 2:
        print('usage: proxy_fidelity_check.py <state.json>')
        return 2
    try:
        with open(sys.argv[1], encoding='utf-8') as f:
            d = json.load(f, parse_constant=lambda value: (_ for _ in ()).throw(ValueError('nonfinite JSON number')))
        if not isinstance(d, dict):
            raise ValueError('state must be an object')
    except (OSError, ValueError) as exc:
        print(f'ERROR input: {exc}')
        return 2
    gates = check(d)
    for gate, ok, message in gates:
        print(f'{"PASS" if ok else "FAIL"} {gate} {message}')
    passed = sum(bool(ok) for _, ok, _ in gates)
    print(f'RESULT {"PASS" if passed == len(gates) else "FAIL"} pass={passed}/{len(gates)} fails={len(gates)-passed}')
    return 0 if passed == len(gates) else 1


if __name__ == '__main__':
    sys.exit(main())
