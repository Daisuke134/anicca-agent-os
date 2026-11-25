"""Offline regression checks; run with python3 -m unittest discover -s this_dir."""
import copy
import importlib.util
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent

def load(name, path):
    spec = importlib.util.spec_from_file_location(name,path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

EV=load('ev',ROOT/'eval_report_check.py')
HL=load('hl',ROOT.parent/'repetition-schedule-check/repetition_schedule_check.py')

class Gates(unittest.TestCase):
    def setUp(self):
        self.ev=json.loads((ROOT/'fixtures/good.json').read_text())
        self.hl=json.loads((ROOT.parent/'repetition-schedule-check/fixtures/good.json').read_text())

    def statuses(self,d):
        return {g:s for g,s,_ in EV.evaluate(d)[0]}

    def test_beta_closed_form(self):
        p=EV.posterior([[0,0]],[0,1],[1,1])
        self.assertAlmostEqual(p['mean'],.5)
        self.assertAlmostEqual(p['variance'],1/12)
        p=EV.posterior([[3,7]],[0,1],[1,1])
        self.assertAlmostEqual(p['mean'],2/3)
        self.assertAlmostEqual(p['variance'],4*8/(12**2*13))

    def test_multicategory_and_case_averaging(self):
        p=EV.posterior([[1,2,3],[1,2,3]],[0,.5,1],[1,1,1])
        self.assertAlmostEqual(p['mean'],11/18)
        self.assertAlmostEqual(p['variance'],((3/4+4)/9-(11/18)**2)/10/2)

    def test_counts_change_mean_and_width(self):
        a=EV.posterior([[5,5]],[0,1],[1,1])
        b=EV.posterior([[50,50]],[0,1],[1,1])
        c=EV.posterior([[1,9]],[0,1],[1,1])
        self.assertLess(b['interval'][1]-b['interval'][0],a['interval'][1]-a['interval'][0])
        self.assertGreater(c['mean'],a['mean'])

    def test_warn_does_not_fail(self):
        del self.ev['allocation_rule']
        self.assertEqual(self.statuses(self.ev)['EV-3'],'WARN')
        self.assertEqual(EV.check(self.ev),[])

    def test_narrow_does_not_need_allocation(self):
        del self.ev['allocation_rule']; self.ev['max_interval_width']=1
        self.assertEqual(self.statuses(self.ev)['EV-3'],'PASS')

    def test_forged_report(self):
        self.ev['models'][0]['posterior_mean']=1
        self.assertEqual(self.statuses(self.ev)['EV-1'],'FAIL')

    def test_overlap_computed_even_when_reports_forged(self):
        self.ev['models'][1]['counts']=copy.deepcopy(self.ev['models'][0]['counts'])
        self.assertEqual(self.statuses(self.ev)['EV-2'],'FAIL')
        self.ev['comparison']={'status':'unresolved'}
        self.assertEqual(self.statuses(self.ev)['EV-2'],'PASS')

    def test_loser_cannot_win(self):
        self.ev['comparison']['winner']='baseline'
        self.assertEqual(self.statuses(self.ev)['EV-2'],'FAIL')

    def test_counts_validation(self):
        for value in [-1,True,.5,float('nan')]:
            d=copy.deepcopy(self.ev); d['models'][0]['counts'][0][0]=value
            self.assertEqual(self.statuses(d)['EV-0'],'FAIL')
        self.ev['N']=21
        self.assertEqual(self.statuses(self.ev)['EV-0'],'FAIL')

    def test_final_artifact_requires_explicit_opacity(self):
        self.ev['evidence']=[{'kind':'final_artifact','path':'synthetic://artifact'}]
        self.assertEqual(self.statuses(self.ev)['EV-4'],'FAIL')
        self.ev['trajectory_opaque']=True
        self.assertEqual(self.statuses(self.ev)['EV-4'],'PASS')

    def test_masking_and_legitimate_rejection(self):
        self.ev['dimensions'][1]['score']=.1
        self.assertEqual(self.statuses(self.ev)['EV-5'],'FAIL')
        self.ev['overall_pass']=False
        self.assertEqual(self.statuses(self.ev)['EV-5'],'PASS')

    def test_every_schedule_decision_checked(self):
        self.hl['decisions'].append({'calendar_interval_hours':24})
        self.assertEqual(len(HL.check(self.hl)),4)

    def test_probability_or_half_life(self):
        del self.hl['decisions'][0]['recall_probability']
        self.assertEqual(HL.check(self.hl),[])
        self.hl['decisions'][0]['half_life']=0
        self.assertTrue(any(s.startswith('HL-2') for s in HL.check(self.hl)))

    def test_non_objects_fail(self):
        for d in [None,[],True,42]:
            self.assertTrue(EV.check(d))
            self.assertTrue(HL.check(d))

    def test_cli_invalid_json(self):
        with tempfile.NamedTemporaryFile(mode='w',suffix='.json') as f:
            f.write('{'); f.flush()
            for script in [ROOT/'eval_report_check.py',ROOT.parent/'repetition-schedule-check/repetition_schedule_check.py']:
                p=subprocess.run([sys.executable,str(script),f.name],capture_output=True,text=True)
                self.assertEqual(p.returncode,1)
                self.assertTrue(p.stdout.startswith('FAIL (1)'))
                self.assertEqual(p.stderr,'')

if __name__=='__main__':
    unittest.main()
