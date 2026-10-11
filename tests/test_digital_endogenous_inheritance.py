import copy,unittest
from experiments.digital_inheritance import history,MOBILE,ANCESTOR
from experiments.digital_inheritance_audit import h
from experiments.digital_endogenous_inheritance import cases
from experiments.digital_endogenous_inheritance_audit import metrics

class EndogenousInheritanceTests(unittest.TestCase):
    def test_paid_birth_positive_witness_and_unpaid_forgery_refusal(self):
        # Software reachability fixture, explicitly installed MOVE genotype.
        row=history(24799,'faithful',MOBILE,'fixture')
        self.assertGreater(metrics(row)['descendant_remote_food'],0)
        # No novelty credited to unchanged descendants of the supplied founder.
        self.assertEqual(metrics(row)['qualifying_lineages'],0)
        bad=copy.deepcopy(row)
        next(e for e in bad['events'] if 'birth' in e)['birth']['write_events']=[]
        bad['final']['events']=bad['events'];bad['state_hash']=h(bad['final'])
        with self.assertRaises(AssertionError):metrics(bad)

    def test_natural_novel_lineage_fixture_and_null(self):
        # Historical seed disclosed; fixture never belongs to a new panel.
        row=history(24114,'mutating',ANCESTOR,'fixture')
        self.assertGreater(metrics(row)['qualifying_lineages'],0)
        self.assertEqual(metrics(history(24798,'copy_disabled',ANCESTOR,'fixture'))['qualifying_lineages'],0)
        self.assertEqual(len(cases('primary')),256)
        self.assertFalse({x['seed'] for x in cases('primary')} & {x['seed'] for x in cases('replication')})
