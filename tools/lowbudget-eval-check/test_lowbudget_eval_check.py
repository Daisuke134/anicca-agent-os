import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from lowbudget_eval_check import check

ROOT = Path(__file__).resolve().parent


class CheckerTests(unittest.TestCase):
    def setUp(self):
        self.state = json.loads((ROOT / 'fixtures/compliant.json').read_text())

    def test_fixtures(self):
        expected = {'compliant': [], 'anicca-current': ['LB-0', 'LB-1', 'LB-2', 'LB-3', 'LB-4', 'LB-5', 'CT-0', 'CT-1', 'CT-2', 'CT-3', 'CT-4'], 'control': ['LB-1', 'LB-3', 'LB-5', 'CT-0', 'CT-1', 'CT-2', 'CT-3', 'CT-4']}
        for fixture, failed in expected.items():
            with self.subTest(fixture=fixture):
                result = subprocess.run([sys.executable, '-B', str(ROOT / 'lowbudget_eval_check.py'),
                                         str(ROOT / 'fixtures' / (fixture + '.json'))],
                                        capture_output=True, text=True)
                report = json.loads(result.stdout)
                self.assertEqual(report['failed_gates'], failed)
                self.assertEqual(report['passed'], 11-len(failed))
                self.assertEqual(report['failed'], len(failed))
                self.assertEqual(result.returncode, int(bool(failed)))

    def test_each_missing_section_fails_its_gate(self):
        for key, gate in [('k', 'LB-0'), ('m', 'LB-0'), ('extrapolation', 'LB-0'), ('estimator', 'LB-1'), ('interval', 'LB-2'), ('improvability', 'LB-3'), ('metrics_fit', 'LB-5'), ('contamination', 'CT-0')]:
            with self.subTest(key=key):
                state = copy.deepcopy(self.state)
                del state[key]
                self.assertFalse(check(state)[gate])

    def test_malformed_sections_do_not_crash(self):
        for key in self.state:
            if not isinstance(self.state[key], dict):
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
                result = subprocess.run([sys.executable, '-B', str(ROOT / 'lowbudget_eval_check.py'), str(path)],
                                        capture_output=True, text=True)
                report = json.loads(result.stdout)
                self.assertEqual(result.returncode, 1)
                self.assertIn('error', report)
                self.assertEqual(report['failed'], 11)
            for args in ([], [str(Path(folder)/'missing.json')]):
                result = subprocess.run([sys.executable, '-B', str(ROOT / 'lowbudget_eval_check.py'), *args],
                                        capture_output=True, text=True)
                self.assertEqual(result.returncode, 1)
                self.assertIn('error', json.loads(result.stdout))

    def test_empty_state_fails_every_gate(self):
        self.assertEqual(list(check({}).values()), [False]*11)

    def test_horizon_boundary_and_invalid_types(self):
        for k, m in [(5,5),(4,5)]:
            self.state.update(k=k, m=m, extrapolation=False)
            self.state['estimator'] = {'type':'combinatorial',
                'direct_or_combinatorial_prioritized':True,
                'unconditional_mixture_superiority_claim':False}
            self.assertTrue(all(check(self.state).values()))
            self.state['estimator']['direct_or_combinatorial_prioritized'] = False
            self.assertFalse(check(self.state)['LB-4'])
        for k in (True, 0, -1, 5.0, '5', None):
            self.state['k'] = k
            self.assertFalse(check(self.state)['LB-0'])
        self.state.update(k=10, m=5, extrapolation=False)
        self.assertFalse(check(self.state)['LB-0'])

    def test_extrapolation_requires_prior_and_selection(self):
        for field in ('type', 'prior_family', 'component_selection', 'naive_y_over_m_transform_only'):
            state = copy.deepcopy(self.state)
            del state['estimator'][field]
            self.assertFalse(check(state)['LB-1'])
        for estimator in ('naive', 'y/m', 'direct', 'combinatorial'):
            self.state['estimator']['type'] = estimator
            self.assertFalse(check(self.state)['LB-1'])
        self.state['estimator'].update(type='hierarchical', prior_family='Beta-Binomial',
                                      component_selection='fixed single component')
        self.assertTrue(check(self.state)['LB-1'])

    def test_interval_containment_is_recorded_not_required(self):
        interval = self.state['interval']
        for reference, contains in [(0.6,True),(0.8,True),(0.9,False)]:
            interval.update(full_data_reference=reference, contains_reference=contains)
            self.assertTrue(check(self.state)['LB-2'])
            interval['contains_reference'] = not contains
            self.assertFalse(check(self.state)['LB-2'])
        for bounds in ([0.8,0.6], [0.6], [False,0.8], [0.6,float('inf')]):
            interval['bounds'] = bounds
            self.assertFalse(check(self.state)['LB-2'])

    def test_unused_diagnostic_and_single_metric_exemptions(self):
        self.state['improvability'] = {'used':False}
        self.state['metrics_fit'] = {'reports_pass_power_and_auc':False}
        self.assertTrue(all(check(self.state).values()))

    def test_absolute_only_does_not_require_rank_or_differential_evidence(self):
        c = self.state['contamination']
        c.update(claim_types=['absolute_inflation'], discusses_ranking=False)
        del c['paraphrase_rank_correlation']
        del c['decomposition']['differential_evidence']
        del c['decomposition']['evidence_description']
        self.assertTrue(all(check(self.state).values()))
        c['discusses_ranking'] = True
        self.assertFalse(check(self.state)['CT-1'])

    def test_ranking_claim_cannot_hide_behind_discussion_flag(self):
        self.state['contamination']['discusses_ranking'] = False
        self.assertFalse(check(self.state)['CT-1'])

    def test_rank_correlation_has_no_acceptance_threshold(self):
        for value in (-1,0,1):
            self.state['contamination']['paraphrase_rank_correlation'] = value
            self.assertTrue(check(self.state)['CT-1'])
        for value in (-1.1,1.1,True,float('nan'),'0.99'):
            self.state['contamination']['paraphrase_rank_correlation'] = value
            self.assertFalse(check(self.state)['CT-1'])

    def test_each_contamination_evidence_field_is_required(self):
        for section, fields, gate in [
            ('decomposition', ('uniform','differential','differential_evidence','evidence_description'), 'CT-2'),
            ('calibration', ('known_dose','known_dose_result','negative_control_result'), 'CT-3'),
            ('clean_baseline', ('reference','gap','used_as_reference'), 'CT-4')]:
            for field in fields:
                state = copy.deepcopy(self.state)
                del state['contamination'][section][field]
                self.assertFalse(check(state)[gate])

    def test_mixed_or_unknown_claim_types_rejected(self):
        for kinds in ([], ['mixed'], ['ranking_reorder','ranking_reorder'], [True], [{}]):
            self.state['contamination']['claim_types'] = kinds
            self.assertFalse(check(self.state)['CT-0'])

    def test_separate_fits_fail_even_if_same_fit_flag_is_true(self):
        self.state['metrics_fit']['auc_fit_id'] = 'fit-2'
        self.assertFalse(check(self.state)['LB-5'])


if __name__ == '__main__':
    unittest.main()
