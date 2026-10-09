import copy
import unittest
from experiments import precursor_reactivation as worker
from experiments import precursor_reactivation_audit as audit


class ReactivationTests(unittest.TestCase):
    def test_complete_cross_and_every_independent_transition(self):
        configs=list(worker.configs())
        self.assertEqual(configs,list(audit.panel()))
        self.assertEqual(len(configs),1792)
        for c in configs:
            r=worker.simulate(c)
            audit.inspect_record(r,c)

    def test_empty_partial_food_work_and_captured_funding_controls(self):
        outcomes=[]
        for c in worker.configs():
            if c['bits']=='0000' and c['source']=='producer' and c['founder_present']:
                r=worker.simulate(c)
                activated=r['events'][-1]['result']['outcome']=='activated'
                self.assertEqual(activated,c['mismatches']==3 and c['fresh_donor'])
                self.assertEqual(r['second_producer_funded'],activated and c['refill'])
                outcomes.append(activated)
        self.assertEqual(sum(outcomes),2)
        for c in worker.configs():
            if len(c['bits'])<4 and c['source']=='producer':
                self.assertNotEqual(worker.simulate(c)['events'][-1]['result']['outcome'],'activated')

    def test_founder_removed_external_activation_is_not_startup(self):
        for c in worker.configs():
            if not c['founder_present']:
                r=worker.simulate(c)
                self.assertNotIn('C',r['terminal']['objects'])
                self.assertEqual(set(r['terminal']['history']),{'C'})
                self.assertEqual(r['events'][0]['result']['outcome']=='activated',c['source']=='external')
                self.assertFalse(r['second_producer_funded'])
                audit.inspect_record(r,c)

    def test_forged_funding_and_semantic_event_rejected(self):
        c=next(c for c in worker.configs() if c['source']=='external' and
               c['founder_present'] and c['mismatches']==3 and c['fresh_donor'])
        r=worker.simulate(c)
        forged=copy.deepcopy(r)
        forged['second_producer_funded']=True
        with self.assertRaisesRegex(ValueError,'funding/subsidy'):
            audit.inspect_record(forged,c)
        forged=copy.deepcopy(r)
        forged['events'][-1]['result']['heat']+=1
        forged['events'][-1]['sha256']=audit.law.sha({k:v for k,v in forged['events'][-1].items() if k!='sha256'})
        with self.assertRaisesRegex(ValueError,'Semantic'):
            audit.inspect_record(forged,c)


if __name__=='__main__':
    unittest.main()
