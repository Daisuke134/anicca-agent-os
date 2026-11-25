#!/usr/bin/env python3
"""Offline BS evidence gates; standard library only."""
import json
import math
import sys


def obj(value):
    return value if isinstance(value, dict) else {}


def number(value):
    return type(value) in (int, float) and math.isfinite(value)


def text(value):
    return isinstance(value, str) and bool(value.strip())


def check(d):
    d = obj(d)
    tasks = obj(d.get('tasks'))
    population = obj(d.get('population'))
    process = obj(d.get('process'))
    bias = obj(d.get('rule_misapplication'))
    gates = [
        ('BS-0', all(text(obj(tasks.get(task)).get('metric'))
                     and number(obj(tasks.get(task)).get('value'))
                     for task in ('measurement', 'individual_prediction', 'population_simulation')),
         'Record separate metrics and values for all three tasks.'),
        ('BS-1', number(population.get('effect_size_mae')) and population['effect_size_mae'] >= 0
         and text(population.get('desirability_inflation_check'))
         and text(population.get('individual_variation_compression_check')),
         'Record effect-size MAE, desirability inflation and individual-variation compression checks.'),
        ('BS-2', all(number(process.get(k)) and 0 <= process[k] <= 1
                     for k in ('reasoning_to_conclusion_fidelity', 'conclusion_to_action_fidelity'))
         and process.get('extraction_method') == 'explicit-tag'
         and text(process.get('conclusion_tag'))
         and process.get('tag_machine_checked') is True
         and process.get('free_text_extraction_mismatch_as_model_trait') is False,
         'Separate both fidelity stages, machine-check explicit tags, and distinguish extraction artifacts.'),
        ('BS-3', text(bias.get('directional_bias_probe'))
         and text(bias.get('probe_result'))
         and bias.get('assumes_single_upstream_cause') is False,
         'Probe directional bias in rule misapplication without assuming a single upstream cause.'),
    ]
    return gates


def main():
    if len(sys.argv) != 2:
        print('usage: behavior_process_check.py <state.json>')
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
