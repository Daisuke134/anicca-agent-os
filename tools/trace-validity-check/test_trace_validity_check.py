import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from trace_validity_check import check

ROOT = Path(__file__).resolve().parent


class CheckerTests(unittest.TestCase):
    def setUp(self):
        self.state = json.loads((ROOT / 'fixtures/compliant.json').read_text())

    def test_fixtures(self):
        expected = {'compliant': [], 'anicca-current': ['BT-0', 'BT-1', 'BT-2', 'BT-3', 'BT-4', 'HB-0', 'HB-1', 'HB-2'], 'control': ['BT-0', 'BT-1', 'BT-3', 'HB-1', 'HB-2']}
        for fixture, failed in expected.items():
            with self.subTest(fixture=fixture):
                result = subprocess.run([sys.executable, '-B', str(ROOT / 'trace_validity_check.py'),
                                         str(ROOT / 'fixtures' / (fixture + '.json'))],
                                        capture_output=True, text=True)
                report = json.loads(result.stdout)
                self.assertEqual(report['failed_gates'], failed)
                self.assertEqual(report['passed'], 8-len(failed))
                self.assertEqual(report['failed'], len(failed))
                self.assertEqual(result.returncode, int(bool(failed)))

    def test_each_missing_section_fails_its_gate(self):
        for key, gate in [('predictor', 'BT-0'), ('validation', 'BT-1'), ('calibration', 'BT-2'), ('sensitivity', 'BT-3'), ('common_metric_comparison', 'BT-4'), ('mechanisms', 'HB-0'), ('outcome', 'HB-1'), ('no_reminder_measurement', 'HB-2')]:
            with self.subTest(key=key):
                state = copy.deepcopy(self.state)
                del state[key]
                self.assertFalse(check(state)[gate])

    def test_malformed_sections_do_not_crash(self):
        for key in self.state:
            if key == 'fixture_note':
                continue
            for value in (None, [], 'true', True, 1):
                with self.subTest(key=key, value=value):
                    state = copy.deepcopy(self.state)
                    state[key] = value
                    self.assertFalse(all(check(state).values()))

    def test_invalid_cli_inputs_fail_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'bad.json'
            for raw in ('[]', '{', '{"x":NaN}', '{"x":1,"x":2}', '{"x":Infinity}'):
                path.write_text(raw)
                result = subprocess.run([sys.executable, '-B', str(ROOT / 'trace_validity_check.py'), str(path)],
                                        capture_output=True, text=True)
                report = json.loads(result.stdout)
                self.assertEqual(result.returncode, 1)
                self.assertIn('error', report)
                self.assertEqual(report['failed'], 8)
            for args in ([], [str(Path(folder)/'missing.json')]):
                result = subprocess.run([sys.executable, '-B', str(ROOT / 'trace_validity_check.py'), *args],
                                        capture_output=True, text=True)
                self.assertEqual(result.returncode, 1)
                self.assertIn('error', json.loads(result.stdout))

    def test_empty_state_fails_every_gate(self):
        self.assertEqual(list(check({}).values()), [False]*8)

    def test_individual_gate_rejections(self):
        cases = [
            ('predictor', 'source_type', 'unknown', 'BT-0'),
            ('predictor', 'retention_or_effect_claim', 'false', 'BT-0'),
            ('validation', 'grouped_by_learner', False, 'BT-1'),
            ('validation', 'method', 'random_split', 'BT-1'),
            ('calibration', 'metric', 'auc', 'BT-2'),
            ('calibration', 'value', True, 'BT-2'),
            ('calibration', 'value', float('nan'), 'BT-2'),
            ('calibration', 'value', float('inf'), 'BT-2'),
            ('calibration', 'value', -0.1, 'BT-2'),
            ('sensitivity', 'value', None, 'BT-3'),
            ('sensitivity', 'excluded_and_recomputed', 'true', 'BT-3'),
            ('common_metric_comparison', 'ci_order', 'overlap', 'BT-4'),
            ('mechanisms', 'push', 0, 'HB-0'),
            ('outcome', 'claimed_type', 'habit', 'HB-1'),
            ('no_reminder_measurement', 'value', None, 'HB-2'),
        ]
        for section, field, value, gate in cases:
            with self.subTest(section=section, field=field, value=value):
                state = copy.deepcopy(self.state)
                state[section][field] = value
                self.assertFalse(check(state)[gate])

    def test_self_report_without_effect_claim(self):
        self.state['predictor'] = {'source_type':'self_report', 'retention_or_effect_claim':False}
        self.assertTrue(check(self.state)['BT-0'])

    def test_retention_and_no_comparison_exemptions(self):
        self.state['outcome'] = {'claimed_type':'retention', 'measured_type':'retention'}
        del self.state['no_reminder_measurement']
        self.state['common_metric_comparison'] = {'performed':False}
        self.assertTrue(all(check(self.state).values()))

    def test_holdout_and_other_calibration(self):
        self.state['validation']['method'] = 'holdout'
        self.state['calibration'] = {'metric':'calibration_intercept', 'value':-0.2}
        self.assertTrue(all(check(self.state).values()))

    def test_ci_order_including_touching_bounds(self):
        c = self.state['common_metric_comparison']
        for left, right, order in [([0,1],[1,2],'overlap'),
                                    ([2,3],[0,1],'right_below_left'),
                                    ([0,2],[1,3],'overlap')]:
            c['left']['ci'], c['right']['ci'], c['ci_order'] = left, right, order
            self.assertTrue(check(self.state)['BT-4'])
        for ci in ([2,1], [0], [False,1], [0,float('inf')]):
            c['left']['ci'] = ci
            self.assertFalse(check(self.state)['BT-4'])

    def test_all_mechanisms_must_be_declared_even_if_absent(self):
        for key in self.state['mechanisms']:
            state = copy.deepcopy(self.state)
            del state['mechanisms'][key]
            self.assertFalse(check(state)['HB-0'])


if __name__ == '__main__':
    unittest.main()
