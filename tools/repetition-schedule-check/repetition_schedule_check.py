#!/usr/bin/env python3
"""Offline stdlib HL-0..4 and SR3-0..2 checker, exit 0=PASS/1=FAIL.
Schema demonstrated by fixtures/good.json. Each decision must record all three
feature groups, a recall probability or half life and trigger threshold,
separate item difficulty and learner ability, and named top factors.
FAIL count counts gates; check(d) returns failure messages like reference tool.
"""
import json
import math
import sys


def number(x):
    return type(x) in (int,float) and math.isfinite(x)


def text(x):
    return isinstance(x,str) and bool(x.strip())


def require(ok, message):
    if not ok:
        raise ValueError(message)


def evaluate(d):
    results = []
    def ownership():
        require(text(d.get('owner')), 'one named owner required')
        require(d.get('surface') in ('in_app','notification'), 'surface must be in_app or notification')

    def decisions():
        rows = d.get('decisions')
        require(isinstance(rows,list) and bool(rows), 'nonempty decision records required')
        require(all(isinstance(r,dict) for r in rows), 'decisions must be objects')
        return rows

    def features():
        groups = {'item': ('difficulty','frequency','past_outcomes'),
                  'learner': ('session_count','mean_accuracy','ability'),
                  'context': ('elapsed_since_last','time_of_day','day_of_week')}
        for i,r in enumerate(decisions()):
            for group,keys in groups.items():
                obj = r.get(group)
                require(isinstance(obj,dict) and all(k in obj and obj[k] is not None for k in keys), f'decision {i}: missing {group} feature group/fields')
            item, learner, context = r['item'],r['learner'],r['context']
            require(number(item['difficulty']) and number(item['frequency']) and item['frequency'] >= 0 and isinstance(item['past_outcomes'],list) and all(type(v) is bool for v in item['past_outcomes']), 'invalid item features')
            require(type(learner['session_count']) is int and learner['session_count'] >= 0 and number(learner['mean_accuracy']) and 0 <= learner['mean_accuracy'] <= 1 and number(learner['ability']), 'invalid learner features')
            require(number(context['elapsed_since_last']) and context['elapsed_since_last'] >= 0 and text(context['time_of_day']) and type(context['day_of_week']) is int and 0 <= context['day_of_week'] <= 6, 'invalid context features (weekday 0..6)')

    def threshold():
        for r in decisions():
            p,h,t = r.get('recall_probability'),r.get('half_life'),r.get('trigger_threshold')
            require((number(p) and 0 <= p <= 1) or (number(h) and h > 0), 'recall probability or positive half-life missing; fixed calendar interval alone fails')
            require(number(t) and 0 < t < 1, 'recall trigger_threshold must be between zero and one')

    def separation():
        for r in decisions():
            require(number(r.get('item',{}).get('difficulty')) and number(r.get('learner',{}).get('ability')), 'separate item difficulty and learner ability required; combined score is insufficient')

    def explanation():
        for r in decisions():
            factors = r.get('top_factors')
            require(isinstance(factors,list) and bool(factors) and all(text(f) for f in factors), 'named top factors required for each decision')

    def comparison():
        obj = d.get('comparison')
        require(isinstance(obj, dict), 'comparison object required')
        return obj

    def evidence():
        obj = comparison()
        kinds = ('real_learners', 'simulated_learners', 'operational_logs')
        require(obj.get('evidence_type') in kinds, 'declare evidence_type: real_learners, simulated_learners or operational_logs')
        require(obj.get('reported_population') == obj['evidence_type'], 'reported population must match evidence; simulated scores cannot be real-learner results')

    def baselines():
        obj = comparison()
        rows = obj.get('baselines')
        require(text(obj.get('protocol')), 'comparison protocol required')
        require(isinstance(rows, list) and len(rows) >= 3 and all(isinstance(r, dict) for r in rows), 'at least three baseline objects required')
        require(all(text(r.get('name')) for r in rows) and len({r['name'].strip().casefold() for r in rows}) == len(rows), 'baseline names must be nonempty and distinct')
        require(all(type(r.get('classical')) is bool for r in rows) and any(r['classical'] for r in rows), 'at least one classical baseline must be identified')
        require(all(r.get('protocol') == obj['protocol'] for r in rows), 'all baselines must use the comparison protocol')

    def confusion_and_cost():
        obj = comparison()
        require(type(obj.get('claims_confusion_robustness')) is bool, 'declare whether confusion robustness is claimed')
        if obj['claims_confusion_robustness']:
            rows = obj.get('semantic_confusion')
            require(isinstance(rows, dict), 'separate semantic confusion results required')
            for group in ('confusable', 'non_confusable'):
                result = rows.get(group)
                require(isinstance(result, dict) and type(result.get('sample_size')) is int and result['sample_size'] > 0 and number(result.get('success_rate')) and 0 <= result['success_rate'] <= 1, 'each semantic group requires positive sample_size and success_rate in [0, 1]')
        require(type(obj.get('llm_every_decision')) is bool, 'declare whether LLM inference occurs each decision')
        if obj['llm_every_decision']:
            cost = obj.get('inference_cost')
            require(isinstance(cost, dict) and number(cost.get('amount_per_decision')) and cost['amount_per_decision'] >= 0 and text(cost.get('currency')) and text(cost.get('measurement_basis')), 'per-decision inference amount, currency and measurement basis required')

    gates = list(zip(('HL-0', 'HL-1', 'HL-2', 'HL-3', 'HL-4'),
                     (ownership, features, threshold, separation, explanation)))
    gates += [('SR3-0', evidence), ('SR3-1', baselines), ('SR3-2', confusion_and_cost)]
    for gate,fn in gates:
        try:
            require(isinstance(d,dict), 'schedule must be an object')
            fn()
            results.append((gate,'PASS','recorded and valid'))
        except (ValueError,TypeError,KeyError,AttributeError) as e:
            results.append((gate,'FAIL',str(e)))
    return results


def check(d):
    return [f'{g} {detail}' for g,status,detail in evaluate(d) if status == 'FAIL']


def main():
    try:
        if len(sys.argv) != 2:
            raise ValueError('usage: python3 repetition_schedule_check.py <json>')
        with open(sys.argv[1], encoding='utf-8') as f:
            results = evaluate(json.load(f))
    except (OSError,ValueError) as e:
        print(f'FAIL (1):\n - INPUT FAIL: {e}')
        return 1
    fails = sum(status == 'FAIL' for _,status,_ in results)
    print(f'FAIL ({fails}):' if fails else 'PASS')
    for gate,status,detail in results:
        print(f' - {gate} {status}: {detail}')
    return int(bool(fails))


if __name__ == '__main__':
    sys.exit(main())
