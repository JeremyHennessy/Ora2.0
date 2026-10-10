import copy, unittest
from experiments import local_world as law, local_audit as audit

class LocalAccounting(unittest.TestCase):
    def test_paid_renewal_possible_in_every_control(self):
        for arm in law.ARMS:
            r=law.trajectory(0,arm,True)
            self.assertTrue(r['score']['endpoint']);self.assertEqual(r['score']['functional_surplus'],2)
            audit.audit_world(r)
    def test_heat_cannot_become_fresh_fuel(self):
        self.assertEqual(law.transition((0,0,0,0,0,0),('decay',0,-1),'candidate')[0],(0,1,0,0,0,0))
        r=law.trajectory(0,'candidate',True);r['events'][-1]['origin']='thermal-reactivation'
        with self.assertRaises(AssertionError):audit.audit_world(r)
    def test_free_activation_forbidden(self):
        self.assertIsNone(law.transition((10,0,0,0,0,0),('activate',0,1),'candidate'))
    def test_renewal_payment_and_identity_refused(self):
        original=law.trajectory(0,'candidate',True)
        for field in ('after','parent'):
            r=copy.deepcopy(original);e=next(e for e in r['events'] if e['action']==['activate',0,1] and e['step']>2048)
            if field=='after':e['after'][5]+=1
            else:e['parent']=0
            with self.assertRaises(AssertionError):audit.audit_world(r)
    def test_all_reverse_channels_preserved(self):
        s=(5,2,3,1,0,8)
        for a in law.ALPHABET:
            r=law.transition(s,a,'candidate')
            if r is not None:
                t,p=r;back,q=law.transition(t,(a[0],a[1],1 if a[0]=='hop' else -a[2]),'candidate')
                self.assertEqual(back,s);self.assertEqual(2**law.heat(s)*p,2**law.heat(t)*q)
if __name__=='__main__':unittest.main()
