import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('checker', ROOT / 'psychometric_audit_check.py')
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT / 'fixtures/conforming.json').read_text())

    def passed(self, gate):
        return dict((g, ok) for g, ok, _ in checker.check(self.data))[gate]

    def test_fixture_exit_codes(self):
        for name, code, count in [('conforming', 0, 6), ('control', 1, 0), ('anicca-assumed', 1, 0)]:
            result = subprocess.run([sys.executable, str(ROOT / 'psychometric_audit_check.py'), str(ROOT / 'fixtures' / (name + '.json'))], capture_output=True, text=True)
            self.assertEqual(result.returncode, code, result.stderr)
            self.assertIn(f'pass={count}/6', result.stdout)

    def test_honest_below_baseline_and_negative_r2_pass(self):
        self.assertTrue(all(ok for _, ok, _ in checker.check(self.data)))
        self.data['baseline']['used_as_evidence'] = True
        self.assertFalse(self.passed('PA-0'))

    def test_lower_is_better_comparison(self):
        self.data['baseline'].update(higher_is_better=False, synthetic_score=0.3, baseline_score=0.2, used_as_evidence=True)
        self.assertFalse(self.passed('PA-0'))
        self.data['baseline']['used_as_evidence'] = False
        self.assertTrue(self.passed('PA-0'))

    def test_invalid_measurements(self):
        for value in [True, '0.5', float('nan'), float('inf'), -1]:
            self.data['joint_structure']['within_person_sd_ratio'] = value
            self.assertFalse(self.passed('PA-2'))

    def test_invalid_negative_control_counts(self):
        for value in [True, -1, 8, 1.5]:
            self.data['negative_controls']['synthetic_significant_paths'] = value
            self.assertFalse(self.passed('PA-3'))

    def test_malformed_sections_fail_without_exception(self):
        for key in list(self.data):
            if key == 'app':
                continue
            for value in [None, [], 'bad', 3]:
                changed = copy.deepcopy(self.data)
                changed[key] = value
                self.assertTrue(any(not ok for _, ok, _ in checker.check(changed)))

    def test_bad_cli_and_root(self):
        script = str(ROOT / 'psychometric_audit_check.py')
        for args in [[], ['/dev/null'], ['/does/not/exist']]:
            self.assertEqual(subprocess.run([sys.executable, script] + args, capture_output=True).returncode, 2)
        result = subprocess.run([sys.executable, script, '/dev/stdin'], input='[]', capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)


if __name__ == '__main__':
    unittest.main()
