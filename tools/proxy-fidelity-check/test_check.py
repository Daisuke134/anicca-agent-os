import copy
import json
from pathlib import Path
import unittest

from proxy_fidelity_check import check


class GateTests(unittest.TestCase):
    def setUp(self):
        self.good = json.loads((Path(__file__).parent / 'fixtures/conforming.json').read_text())

    def failures(self, data):
        return {gate for gate, ok, _ in check(data) if not ok}

    def test_conforming(self):
        self.assertEqual(self.failures(self.good), set())

    def test_missing_and_malformed_sections_fail(self):
        self.assertEqual(len(self.failures({})), 11)
        for key in self.good:
            data = copy.deepcopy(self.good)
            data[key] = []
            check(data)

    def test_boolean_is_not_rate(self):
        self.good['proxy']['premature_disclosure_rate'] = True
        self.assertIn('UP-1', self.failures(self.good))

    def test_ensemble_requires_evidence_but_comparison_is_not_ensemble(self):
        del self.good['simulators']['complementarity_evidence']
        self.assertIn('DG-2', self.failures(self.good))
        self.good['simulators']['ensemble_used'] = False
        self.assertNotIn('DG-2', self.failures(self.good))

    def test_duplicate_simulators_and_incorrect_range_fail(self):
        self.good['simulators']['score_range'] = 0
        self.assertIn('UP-3', self.failures(self.good))
        self.good['simulators']['score_range'] = 0.1
        self.good['simulators']['results'][1]['name'] = 'A'
        self.assertIn('UP-3', self.failures(self.good))

    def test_one_missing_facet_fails(self):
        del self.good['distribution']['facets']['DAMSL']['miss']
        self.assertIn('DG-1', self.failures(self.good))


if __name__ == '__main__':
    unittest.main()
