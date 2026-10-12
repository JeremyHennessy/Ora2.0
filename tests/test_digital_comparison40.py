"""Prepared summaries only, never organism evidence."""
import unittest
from experiments.digital_comparison40_diagnose import diagnose
from experiments.digital_comparison40_independent import diagnose as referee, IDS,SEEDS,MODES,REFS

def metric(t=200,personal=False,formation=55):
    return dict(formation=formation,food=32,fresh=16,own_origins=16 if personal else 0,terminal_tick=t,
        completed=True,survived64=True,delivered_own=personal,both_own_outcomes=personal,completion_tick=t,paid_work=formation+t)

def bank():
    return dict(rows=[dict(role=r,seed=s,control=c,metric=metric(100 if r.startswith('candidate') and c=='intact' else 200,r.startswith('candidate') and c=='intact'))
        for r in ['candidate'+str(i) for i in IDS]+list(REFS) for s in SEEDS for c in MODES])

class DiagnosisTests(unittest.TestCase):
    def check(self,b):
        x=diagnose(b);self.assertEqual(x,referee(b));self.assertFalse(x['learning']);return x
    def test_prepared_positive_is_only_bill_description(self):
        x=self.check(bank());self.assertEqual(x['summary']['personal_control_benefit'],896);self.assertFalse(x['stage_credit'])
    def test_fixed_baseline_can_bind_despite_control_benefit(self):
        b=bank()
        for r in b['rows']:
            if r['role']=='affine7' and r['control']=='intact':r['metric']=metric(90)
        x=self.check(b);self.assertEqual(x['summary']['personal_control_benefit_without_fixed'],896)
    def test_completion_without_personal_information_is_separate(self):
        b=bank();b['rows'][0]['metric']['own_origins']=15;x=self.check(b)
        self.assertEqual(x['summary']['strict_control_benefit'],896);self.assertEqual(x['summary']['personal_control_benefit'],895)
    def test_null_control_not_cheap_winner(self):
        b=bank();b['rows'][1]['metric'].update(completed=False,food=2,fresh=0,terminal_tick=90,completion_tick=None,paid_work=None)
        x=self.check(b);self.assertIsNone(x['cells'][0]['control_gaps']['retained_disabled']);self.assertFalse(x['cells'][0]['complete_all']);self.assertFalse(x['cells'][0]['strict_control_benefit'])
    def test_work_and_latency_different_binding_references(self):
        b=bank()
        for r in b['rows']:
            if r['role']=='affine7' and r['control']=='intact':r['metric']=metric(101,formation=19)
        x=self.check(b);self.assertEqual(x['cells'][0]['fixed_gaps'],[-1,35]);self.assertFalse(x['cells'][0]['strict_fixed_benefit'])
    def test_missing_or_duplicate_identity_refused(self):
        b=bank();b['rows'].pop()
        for f in (diagnose,referee):
            with self.assertRaises(ValueError):f(b)
        b=bank();b['rows'].append(b['rows'][0])
        for f in (diagnose,referee):
            with self.assertRaises(ValueError):f(b)
    def test_boolean_bill_and_unrelated_own_label_refused(self):
        b=bank();b['rows'][0]['metric']['paid_work']=True
        for f in (diagnose,referee):
            with self.assertRaises(ValueError):f(b)
        b=bank();b['rows'][2]['metric']['delivered_own']=True
        for f in (diagnose,referee):
            with self.assertRaises(ValueError):f(b)
    def test_all_contexts_retain_failed_control_and_reference(self):
        b=bank()
        for r in b['rows']:
            if r['control']=='intact' and r['role']=='fixed0':r['metric'].update(completed=False,food=0,fresh=0,terminal_tick=12,survived64=False,completion_tick=None,paid_work=None)
        self.assertEqual(self.check(b)['summary']['personal_complete_fixed_benefit'],896)

if __name__=='__main__':unittest.main()
