import copy
import unittest
from experiments.digital_inheritance import history,MOBILE,select
from experiments.digital_inheritance_audit import audit_world,h

class DigitalInheritanceTests(unittest.TestCase):
    def test_viable_ordinary_route_and_same_endpoint_forgery_refusal(self):
        r=history(24399,'faithful',MOBILE,'software_fixture')
        x=audit_world(r)
        self.assertGreaterEqual(x['remote_food'],4)
        self.assertGreaterEqual(x['descendant_births'],1)
        self.assertFalse(r['final']['entities'])
        for kind in ('genesis','ancestry'):
            bad=copy.deepcopy(r)
            if kind=='genesis':bad['genesis_program']=[0]*6
            else:next(e for e in bad['events'] if 'birth' in e)['birth']['write_events']=[]
            bad['state_hash']=h(bad['final'])
            with self.assertRaises(AssertionError):audit_world(bad)

    def test_disabled_copy_and_static_unscreened_selector(self):
        r=history(24398,'copy_disabled',MOBILE,'software_fixture')
        self.assertEqual(audit_world(r)['births'],0)
        rows=[dict(mode='mutating',events=[dict(birth=dict(child=dict(code=[[v,i] for i,v in enumerate(p)]))) for p in ([1,2,4,5,6,12],[3,2,4,5,6,12],[1,2,4,5,6,3])])]
        self.assertEqual(select(rows)['candidate'],[1,2,4,5,6,3])
