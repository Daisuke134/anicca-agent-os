import copy
import json
from pathlib import Path
import unittest

from repetition_schedule_check import evaluate


class RepetitionChecks(unittest.TestCase):
    def setUp(self):
        self.good = json.loads((Path(__file__).parent / 'fixtures/good.json').read_text())

    def failures(self, document):
        return {gate for gate, status, _ in evaluate(document) if status == 'FAIL'}

    def test_conforming_and_original_gates(self):
        self.assertEqual(self.failures(self.good), set())
        self.good['decisions'][0].pop('context')
        self.assertEqual(self.failures(self.good), {'HL-1'})

    def test_simulated_claim_cannot_be_real(self):
        self.good['comparison']['reported_population'] = 'real_learners'
        self.assertEqual(self.failures(self.good), {'SR3-0'})

    def test_evidence_categories(self):
        for kind in ('real_learners', 'simulated_learners', 'operational_logs'):
            self.good['comparison'].update(evidence_type=kind, reported_population=kind)
            self.assertEqual(self.failures(self.good), set())

    def test_three_distinct_baselines_and_classical_required(self):
        for change in ('short', 'duplicate', 'nonclassical', 'protocol'):
            d = copy.deepcopy(self.good)
            rows = d['comparison']['baselines']
            if change == 'short':
                rows.pop()
            elif change == 'duplicate':
                rows[1]['name'] = rows[0]['name'].upper()
            elif change == 'nonclassical':
                rows[0]['classical'] = False
            else:
                rows[0]['protocol'] = 'different'
            self.assertEqual(self.failures(d), {'SR3-1'})

    def test_confusion_claim_requires_separate_results(self):
        self.good['comparison']['semantic_confusion'].pop('confusable')
        self.assertEqual(self.failures(self.good), {'SR3-2'})
        self.good['comparison']['claims_confusion_robustness'] = False
        self.assertEqual(self.failures(self.good), set())

    def test_cost_nonfinite_negative_and_boolean_rejected(self):
        for value in (float('nan'), float('inf'), -1, True):
            self.good['comparison']['inference_cost']['amount_per_decision'] = value
            self.assertEqual(self.failures(self.good), {'SR3-2'})

    def test_conditional_cost_and_zero_cost(self):
        self.good['comparison']['inference_cost']['amount_per_decision'] = 0
        self.assertEqual(self.failures(self.good), set())
        self.good['comparison'].pop('inference_cost')
        self.assertEqual(self.failures(self.good), {'SR3-2'})
        self.good['comparison']['llm_every_decision'] = False
        self.assertEqual(self.failures(self.good), set())

    def test_missing_and_malformed_comparison(self):
        for value in (None, [], 'recorded', 1):
            self.good['comparison'] = value
            self.assertEqual(self.failures(self.good), {'SR3-0', 'SR3-1', 'SR3-2'})

    def test_nonobject_input_fails_all_gates(self):
        for value in (None, [], 'text', 1):
            self.assertEqual(len(self.failures(value)), 8)


if __name__ == '__main__':
    unittest.main()
