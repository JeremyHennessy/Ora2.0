import unittest
from experiments import transfer_gate as p,transfer_audit as a
class TransferTest(unittest.TestCase):
    def test_paid_partial_and_full_scope(self):
        r=p.enumerate_case((0,0,0,0,0,0),0,1,'candidate')
        self.assertIn('partial',r['witnesses']);self.assertNotIn('whole',r['witnesses'])
        v=r['witnesses']['partial'];self.assertEqual(len(v['final_bonds']),2);self.assertEqual(v['startup_paid'],9)
        a.witness(r,'partial',v)
        r=p.enumerate_case((0,0,0,0,0,0),0,4,'candidate')
        self.assertIn('transfer-whole',r['witnesses']);a.witness(r,'transfer-whole',r['witnesses']['transfer-whole'])
    def test_all_primary_nulls_can_restore_whole(self):
        for arm in p.ARMS:
            r=p.enumerate_case((0,1,0,1,0,1),0,3,arm);self.assertIn('whole',r['witnesses'])
            a.witness(r,'whole',r['witnesses']['whole'])
    def test_independent_state_enumeration(self):
        for arm in p.ARMS:
            for budget in range(7):
                types=(1,0,1,1,0,0);r=p.enumerate_case(types,2,budget,arm)
                n,e,h,_=a.enumerate_states(types,2,budget,arm);self.assertEqual((r['states'],r['edges'],r['state_sha256']),(n,e,h))
                for label,value in r['witnesses'].items():a.witness(r,label,value)
    def test_no_unpriced_work(self):
        r=p.enumerate_case((0,0,0,0,0,0),0,0,'candidate');self.assertFalse(r['witnesses'])
        r=p.enumerate_case((0,0,0,0,0,0),0,1,'candidate');r['witnesses']['partial']['heat']-=1;r['witnesses']['partial']['photons']+=1
        with self.assertRaises(ValueError):a.witness(r,'partial',r['witnesses']['partial'])
    def test_ancestry_and_false_scope_reject(self):
        import copy
        r=p.enumerate_case((0,0,0,0,0,0),0,1,'candidate');v=copy.deepcopy(r['witnesses']['partial']);v['objects'][-1]['energy_parent']=999
        with self.assertRaises(ValueError):a.witness(r,'partial',v)
        with self.assertRaises(ValueError):a.witness(r,'whole',r['witnesses']['partial'])
if __name__=='__main__':unittest.main()
