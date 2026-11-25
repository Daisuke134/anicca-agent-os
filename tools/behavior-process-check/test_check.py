import copy
import json
from pathlib import Path
import unittest

from behavior_process_check import check


class GateTests(unittest.TestCase):
    def setUp(self):
        self.good = json.loads((Path(__file__).parent / 'fixtures/conforming.json').read_text())

    def failures(self, data):
        return {gate for gate, ok, _ in check(data) if not ok}

    def test_conforming(self):
        self.assertEqual(self.failures(self.good), set())

    def test_missing_and_malformed_sections_fail(self):
        self.assertEqual(len(self.failures({})), 4)
        for key in self.good:
            data = copy.deepcopy(self.good)
            data[key] = []
            check(data)

    def test_direction_only_cannot_replace_mae(self):
        del self.good['population']['effect_size_mae']
        self.good['population']['direction_agreement'] = 1.0
        self.assertIn('BS-1', self.failures(self.good))

    def test_invalid_fidelity_and_unchecked_tag_fail(self):
        self.good['process']['reasoning_to_conclusion_fidelity'] = True
        self.assertIn('BS-2', self.failures(self.good))
        self.good['process']['reasoning_to_conclusion_fidelity'] = 0.8
        self.good['process']['tag_machine_checked'] = False
        self.assertIn('BS-2', self.failures(self.good))

    def test_free_text_extraction_is_not_model_fidelity(self):
        self.good['process']['extraction_method'] = 'free-text'
        self.assertIn('BS-2', self.failures(self.good))

    def test_single_cause_assumption_fails(self):
        self.good['rule_misapplication']['assumes_single_upstream_cause'] = True
        self.assertIn('BS-3', self.failures(self.good))


if __name__ == '__main__':
    unittest.main()
