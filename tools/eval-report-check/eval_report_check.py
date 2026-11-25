#!/usr/bin/env python3
"""Deterministic EV-0..5 report gate; stdlib, offline, exit 0=PASS/1=FAIL.

Schema: N trials per case, M cases; categories [{name, definition, weight}],
models [{name, counts: M x K integers, posterior_mean, credible_interval}],
prior: K positive concentrations (default ones), credible_level (default .95),
primary_metric='posterior_mean', comparison={status: 'winner'|'unresolved'|
'not_applicable', winner: model name}, max_interval_width, allocation_rule,
evidence=[{kind: execution_trace|audit_log|environment_snapshot|final_artifact,
path: ...}], trajectory_opaque, dimensions=[{name,score,important,minimum}],
overall_pass (boolean). Alternative dimensions require task_rubric text.

Hariri et al. https://arxiv.org/html/2510.04265v4 Algorithm 1 / section 2.5:
independent per-case Dirichlet posteriors; exact weighted mean and variance,
variance of the case average = sum(case variances)/M**2. Interval is the
paper's Gaussian approximation, clipped to the rubric support, NOT an exact
Dirichlet quantile (especially for small M). Shared category weights/prior
make models comparable. Reported numbers must match within 1e-6 absolute.
FAIL count counts gates, not individual missing fields. EV-3 is warning-only.
"""
import json
import math
import sys
from statistics import NormalDist


def number(x):
    return type(x) in (int, float) and math.isfinite(x)


def text(x):
    return isinstance(x, str) and bool(x.strip())


def require(ok, message):
    if not ok:
        raise ValueError(message)


def posterior(counts, weights, prior, level=.95):
    """Closed-form Dirichlet moments and approximate central credible interval."""
    means, variances = [], []
    for row in counts:
        a = [n + p for n, p in zip(row, prior)]
        total = math.fsum(a)
        mean = math.fsum(v * w for v, w in zip(a, weights)) / total
        variance = math.fsum(v * (w - mean)**2 for v, w in zip(a, weights)) / (total * (total + 1))
        means.append(mean)
        variances.append(variance)
    mean = math.fsum(means) / len(counts)
    variance = math.fsum(variances) / len(counts)**2
    radius = NormalDist().inv_cdf((1 + level) / 2) * math.sqrt(variance)
    return {'mean': mean, 'variance': variance,
            'interval': [max(min(weights), mean-radius), min(max(weights), mean+radius)]}


def evaluate(d):
    results, computed = [], {}
    def gate(n, fn, warning=False):
        try:
            detail = fn()
            results.append((f'EV-{n}', 'PASS', detail or 'recorded and valid'))
        except (ValueError, TypeError, KeyError, AttributeError, OverflowError) as e:
            results.append((f'EV-{n}', 'WARN' if warning else 'FAIL', str(e)))

    def trials():
        require(isinstance(d, dict), 'report must be an object')
        n, m, cats, models = d.get('N'), d.get('M'), d.get('categories'), d.get('models')
        require(type(n) is int and n > 0 and type(m) is int and m > 0, 'missing/invalid N trials per case or M cases')
        require(isinstance(cats, list) and len(cats) >= 2, 'at least two outcome categories required')
        names = [c['name'] for c in cats]
        require(all(text(v) for v in names) and len(set(names)) == len(names), 'category names must be unique')
        require(all(text(c.get('definition')) for c in cats), 'outcome category definitions required')
        weights = [c['weight'] for c in cats]
        require(all(number(w) for w in weights) and max(weights) > min(weights), 'finite, nonconstant rubric weights required')
        prior = d.get('prior', [1.0]*len(cats))
        require(isinstance(prior, list) and len(prior) == len(cats) and all(number(p) and p > 0 for p in prior), 'invalid Dirichlet prior')
        level = d.get('credible_level', .95)
        require(number(level) and 0 < level < 1, 'credible_level must be between zero and one')
        require(isinstance(models, list) and bool(models), 'model trial counts missing')
        names = [model['name'] for model in models]
        require(all(text(v) for v in names) and len(set(names)) == len(names), 'model names must be unique')
        pending = {}
        for model in models:
            rows = model.get('counts')
            require(isinstance(rows, list) and len(rows) == m, 'counts must contain M case rows')
            for row in rows:
                require(isinstance(row, list) and len(row) == len(cats) and all(type(v) is int and v >= 0 for v in row), 'counts must be nonnegative integers for every category')
                require(sum(row) == n, 'each case count total must equal N')
            pending[model['name']] = posterior(rows, weights, prior, level)
        computed.update(pending)
        return f'N={n}, M={m}, categories={len(cats)}; counts validated'

    def estimates():
        require(computed, 'posterior cannot be computed: valid trial counts required')
        require(d.get('primary_metric') == 'posterior_mean', 'primary metric must be posterior_mean plus credible_interval; Pass@k alone is insufficient')
        for model in d['models']:
            p = computed[model['name']]
            mean, ci = model.get('posterior_mean'), model.get('credible_interval')
            require(number(mean) and math.isclose(mean, p['mean'], rel_tol=0, abs_tol=1e-6), 'missing/incorrect reported posterior mean')
            require(isinstance(ci, list) and len(ci) == 2 and all(number(x) for x in ci), 'credible_interval must contain two finite numbers')
            require(all(math.isclose(x,y,rel_tol=0,abs_tol=1e-6) for x,y in zip(ci,p['interval'])), 'reported interval does not match computed interval')
        return 'reported means and intervals match computed Dirichlet moments'

    def comparison():
        c = d.get('comparison', {})
        require(computed, 'comparison unavailable without valid trial counts')
        status = c.get('status')
        require(status in ('winner','unresolved','not_applicable'), 'explicit winner/unresolved/not_applicable status required')
        if status == 'not_applicable':
            require(len(computed) == 1, 'multiple models require a comparison decision')
        if status != 'winner':
            require(not c.get('winner'), 'winner contradicts comparison status')
            return status
        winner = c.get('winner')
        require(winner in computed and len(computed) > 1, 'winner must name a model with an evaluated opponent')
        lo = computed[winner]['interval'][0]
        for name, p in computed.items():
            if name != winner:
                require(lo > p['interval'][1], f'winner {winner} is not strictly above {name}: intervals overlap/touch or winner is lower')
        return f'{winner}: strictly separated intervals'

    def allocation():
        width = d.get('max_interval_width')
        require(number(width) and width > 0, 'pre-specified max_interval_width missing; next assessment requires allocation policy')
        require(computed, 'width cannot be assessed without trial counts; next assessment requires allocation policy')
        wide = [name for name,p in computed.items() if p['interval'][1]-p['interval'][0] > width]
        if wide:
            require(text(d.get('allocation_rule')), 'wide intervals: '+', '.join(wide)+'; missing allocation rule (required next assessment)')
        return 'allocation rule recorded' if wide else 'all computed widths within threshold'

    def evidence():
        rows = d.get('evidence')
        require(isinstance(rows,list) and bool(rows), 'evidence paths missing; artifact-only reports must explicitly set trajectory_opaque=true')
        kinds = {'execution_trace','audit_log','environment_snapshot','final_artifact'}
        require(all(r.get('kind') in kinds and text(r.get('path')) for r in rows), 'each evidence entry needs a recognized kind and path')
        if all(r['kind'] == 'final_artifact' for r in rows):
            require(d.get('trajectory_opaque') is True, 'artifact-only evidence requires trajectory_opaque=true')
        return 'evidence routes recorded (path contents are not verified offline)'

    def dimensions():
        rows = d.get('dimensions')
        require(isinstance(rows,list) and bool(rows), 'dimension-level scores and importance/floors missing')
        names = [r['name'] for r in rows]
        require(all(text(n) for n in names) and len(set(names)) == len(names), 'unique dimension names required')
        require({'Completion','Safety','Robustness'} <= set(names) or text(d.get('task_rubric')), 'Completion/Safety/Robustness or named task-adaptive rubric required')
        require(type(d.get('overall_pass')) is bool, 'overall_pass must be boolean')
        for r in rows:
            require(number(r.get('score')) and type(r.get('important')) is bool, 'finite dimension score and explicit importance required')
            if r['important']:
                require(number(r.get('minimum')), 'important dimension requires minimum')
                require(not(d['overall_pass'] and r['score'] < r['minimum']), 'dimension masking: '+r['name']+' below minimum despite overall pass')
        return 'dimensions separated; no important dimension masked'

    for i, fn in enumerate((trials,estimates,comparison,allocation,evidence,dimensions)):
        gate(i, fn, warning=(i == 3))
    return results, computed


def check(d):
    return [f'{g} {detail}' for g,status,detail in evaluate(d)[0] if status == 'FAIL']


def main():
    try:
        if len(sys.argv) != 2:
            raise ValueError('usage: python3 eval_report_check.py <json>')
        with open(sys.argv[1], encoding='utf-8') as f:
            d = json.load(f)
        results, computed = evaluate(d)
    except (OSError, ValueError) as e:
        print(f'FAIL (1):\n - INPUT FAIL: {e}')
        return 1
    fails = sum(status == 'FAIL' for _,status,_ in results)
    print(f'FAIL ({fails}):' if fails else 'PASS')
    for gate,status,detail in results:
        print(f' - {gate} {status}: {detail}')
    for name,p in computed.items():
        lo,hi = p['interval']
        print(f' - POSTERIOR {name}: mean={p["mean"]:.9f} interval=[{lo:.9f}, {hi:.9f}] width={hi-lo:.9f} (Gaussian approximation)')
    return int(bool(fails))


if __name__ == '__main__':
    sys.exit(main())
