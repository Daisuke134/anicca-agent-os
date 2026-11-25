import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('checker', ROOT / 'mrt_moderator_check.py')
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class ModeratorTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT / 'fixtures/conforming.json').read_text())

    def passed(self, gate):
        return dict((g, ok) for g, ok, _ in checker.check(self.data))[gate]

    def test_fixture_exit_codes(self):
        for name, code, count in [('conforming', 0, 6), ('control', 1, 0), ('anicca-assumed', 1, 0)]:
            result = subprocess.run([sys.executable, str(ROOT / 'mrt_moderator_check.py'), str(ROOT / 'fixtures' / (name + '.json'))], capture_output=True, text=True)
            self.assertEqual(result.returncode, code, result.stderr)
            self.assertIn(f'pass={count}/6', result.stdout)

    def test_exploratory_posthoc_is_accepted(self):
        self.data['declaration'].update(before_analysis=False, claim_kind='exploratory')
        self.assertTrue(self.passed('MV-0'))
        self.data['declaration']['claim_kind'] = 'confirmatory'
        self.assertFalse(self.passed('MV-0'))

    def test_stratum_omission_and_cherry_picking(self):
        self.data['consistency']['stratum_effects'].pop('ios-late')
        self.assertFalse(self.passed('MV-1'))
        self.setUp()
        self.data['consistency']['general_moderator_claim'] = True
        self.assertFalse(self.passed('MV-1'))

    def test_consistent_positive_effects(self):
        self.data['consistency'].update(stratum_effects={s:'positive' for s in self.data['declaration']['strata']}, conclusion='consistent', general_moderator_claim=True)
        self.assertTrue(self.passed('MV-1'))

    def test_forecasting_does_not_imply_policy_value(self):
        self.data['policy_value']['forecasting_only'] = True
        self.assertFalse(self.passed('MV-3'))
        self.data['policy_value'] = {'claimed':False}
        self.assertTrue(self.passed('MV-3'))

    def test_underpowered_and_uncontrolled_efficacy(self):
        self.data['power']['claim_kind'] = 'efficacy'
        self.assertFalse(self.passed('MV-5'))
        self.data['power'].update(adequate=True, controlled=False)
        self.assertFalse(self.passed('MV-5'))

    def test_outcome_omission_and_invalid_measurements(self):
        self.data['outcomes']['results'].pop('positive_affect')
        self.assertFalse(self.passed('MV-4'))
        self.setUp()
        for value in [True, '0.5', float('nan'), float('inf')]:
            self.data['outcomes']['results']['resilience']['effect'] = value
            self.assertFalse(self.passed('MV-4'))

    def test_malformed_sections_fail_without_exception(self):
        for key in list(self.data):
            if key == 'app':
                continue
            for value in [None, [], 'bad', 3]:
                changed = copy.deepcopy(self.data)
                changed[key] = value
                self.assertTrue(any(not ok for _, ok, _ in checker.check(changed)))

    def test_bad_cli_and_root(self):
        script = str(ROOT / 'mrt_moderator_check.py')
        for args in [[], ['/dev/null'], ['/does/not/exist']]:
            self.assertEqual(subprocess.run([sys.executable, script] + args, capture_output=True).returncode, 2)
        result = subprocess.run([sys.executable, script, '/dev/stdin'], input='[]', capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)


if __name__ == '__main__':
    unittest.main()
