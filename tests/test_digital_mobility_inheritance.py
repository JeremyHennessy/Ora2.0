import copy,unittest
from experiments.digital_inheritance import history,MOBILE
from experiments.digital_inheritance_audit import h
from experiments.digital_mobility_inheritance import cases
from experiments.digital_mobility_inheritance_audit import metrics

class MobilityInheritanceTests(unittest.TestCase):
    def test_generic_endpoint_paid_descendant_witness_and_forgery_refusal(self):
        row=history(24599,'faithful',MOBILE,'fixture')
        self.assertGreaterEqual(metrics(row)['descendant_remote_food'],4)
        bad=copy.deepcopy(row)
        next(e for e in bad['events'] if 'birth' in e)['birth']['write_events']=[]
        bad['final']['events']=bad['events'];bad['state_hash']=h(bad['final'])
        with self.assertRaises(AssertionError):metrics(bad)

    def test_claim_specific_null_and_disjoint_prospective_seeds(self):
        row=history(24598,'copy_disabled',MOBILE,'fixture')
        x=metrics(row);self.assertEqual((x['births'],x['descendant_remote_food']),(0,0))
        self.assertEqual(len(cases('primary')),48)
        self.assertEqual(len(cases('replication')),48)
        self.assertFalse({x['seed'] for x in cases('primary')} & {x['seed'] for x in cases('replication')})
