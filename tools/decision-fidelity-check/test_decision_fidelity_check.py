"""Behavioral regression tests; no external dependencies or extra fixtures."""
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import decision_fidelity_check as checker

ROOT = Path(__file__).parent


class GateTests(unittest.TestCase):
    def setUp(self):
        self.state = json.loads((ROOT / 'fixtures/compliant.json').read_text())

    def test_fixture_exits_and_gates(self):
        for name, failed in [('compliant', []), ('anicca-documented', [f'DF-{i}' for i in range(8)]),
                             ('control', ['DF-1', 'DF-2'])]:
            with self.subTest(name=name):
                run = subprocess.run([sys.executable, str(ROOT / 'decision_fidelity_check.py'),
                                      str(ROOT / 'fixtures' / (name + '.json'))], capture_output=True, text=True)
                self.assertEqual(run.returncode, int(bool(failed)))
                self.assertEqual(json.loads(run.stdout)['failed_gates'], failed)

    def test_required_evidence_cannot_be_removed(self):
        paths = {
            'DF-0': ['ground_truth_type', 'decision_claimed'],
            'DF-1': ['outcome_conditioned.groups', 'outcome_conditioned.contrast'],
            'DF-2': ['behavior.resistance.real', 'behavior.deliberation.simulation',
                     'behavior.disengagement', 'behavior.post_repair_outcome_conditioned'],
            'DF-3': ['measurement.teacher_forced', 'measurement.same_perceiver'],
            'DF-4': ['knowledge_leakage.pairs', 'knowledge_leakage.domains',
                     'knowledge_leakage.paired_contrast', 'knowledge_leakage.conditional_on_twin_adequacy'],
            'DF-5': ['human_likeness.lexical_metrics', 'human_likeness.judge_metrics',
                     'human_likeness.controls.human_human', 'human_likeness.controls.proxy_proxy',
                     'human_likeness.judge_sensitivity', 'human_likeness.separate_from_task_success'],
            'DF-6': ['reliability.R1', 'reliability.R2', 'reliability.profile_informativeness_evidence',
                     'reliability.coverage.n', 'reliability.coverage.variance_stability',
                     'reliability.coverage.bias_assessment', 'reliability.cross_level_improvement_inferred'],
            'DF-7': ['calibration.type', 'calibration.reference_questions', 'calibration.cold_start',
                     'calibration.target_has_human_data', 'calibration.level'],
        }
        for gate, fields in paths.items():
            for path in fields:
                for replacement in [None, '', [], {}, 'missing']:
                    with self.subTest(gate=gate, path=path, replacement=replacement):
                        state = copy.deepcopy(self.state)
                        keys = path.split('.')
                        node = state
                        for key in keys[:-1]:
                            node = node[key]
                        if replacement == 'missing':
                            del node[keys[-1]]
                        else:
                            node[keys[-1]] = replacement
                        self.assertFalse(checker.check(state)[gate])

    def test_conditional_declarations(self):
        for section, key, gate in [('knowledge_leakage', 'persona_has_unknown_targets', 'DF-4'),
                                   ('human_likeness', 'claimed', 'DF-5'), ('calibration', 'claimed', 'DF-7')]:
            for declaration, expected in [(True, False), (False, True), (None, False), ('false', False), (0, False)]:
                with self.subTest(section=section, declaration=declaration):
                    self.state[section] = {key: declaration}
                    self.assertEqual(checker.check(self.state)[gate], expected)

    def test_gate_boundaries(self):
        self.state['ground_truth_type'] = 'assigned_goal_roleplay'
        self.assertFalse(checker.check(self.state)['DF-0'])
        self.state['decision_claimed'] = False
        self.assertTrue(checker.check(self.state)['DF-0'])
        self.state['measurement'] = {'teacher_forced': False, 'same_perceiver': False}
        self.assertFalse(checker.check(self.state)['DF-3'])
        self.state['measurement']['uncontrolled'] = True
        self.assertTrue(checker.check(self.state)['DF-3'])
        self.state['calibration']['target_has_human_data'] = True
        self.assertFalse(checker.check(self.state)['DF-7'])
        self.state['reliability']['cross_level_improvement_inferred'] = True
        self.assertFalse(checker.check(self.state)['DF-6'])
        self.state['knowledge_leakage'].pop('conditional_on_twin_adequacy')
        self.state['knowledge_leakage']['human_low_knowledge_baseline'] = {'metric': 'gap', 'value': 0.1}
        self.assertTrue(checker.check(self.state)['DF-4'])

    def test_contrast_and_numeric_validation(self):
        contrast = {'effect_size_metric': 'd', 'effect_size': 0.34,
                    'test': {'method': 'permutation', 'p_value': 0.001}}
        self.assertTrue(checker.contrast(contrast))  # No invented effect-size cutoff.
        for bad in [True, '0.1', float('inf'), float('nan')]:
            contrast['effect_size'] = bad
            self.assertFalse(checker.contrast(contrast))
        self.state['outcome_conditioned']['groups'][1]['outcome'] = 'buyer'
        self.assertFalse(checker.check(self.state)['DF-1'])
        for bad in [-0.1, 1.1, True, '0.5']:
            self.state['behavior']['resistance']['real'] = bad
            self.assertFalse(checker.check(self.state)['DF-2'])

    def test_invalid_input_cli(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
            path = Path(temporary) / 'input.json'
            for content in ['[]', '{', '{"a":1,"a":2}', '{"a":NaN}', '{"a":Infinity}']:
                path.write_text(content)
                run = subprocess.run([sys.executable, str(ROOT / 'decision_fidelity_check.py'), str(path)],
                                     capture_output=True, text=True)
                self.assertEqual(run.returncode, 2)
                self.assertEqual(json.loads(run.stdout)['result'], 'ERROR')


if __name__ == '__main__':
    unittest.main()
