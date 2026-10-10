import copy, unittest
from experiments import assemble_world as producer, assemble_audit as auditor

class AssembleTests(unittest.TestCase):
    def test_full_paid_certificates_all_controls(self):
        for arm in producer.ARMS:
            r=producer.trajectory(0,arm,True);self.assertEqual(r['score']['functional_surplus'],3)
            self.assertEqual(r['score']['post_functional_surplus'],3);self.assertTrue(auditor.audit_world(r)['endpoint'])

    def test_all_primitive_reverse_prices_and_interpreters(self):
        for arm in producer.ARMS:
            for f in range(11):
                for q in range(4):
                    for pos in range(4):
                        if q and pos not in (0,3):continue
                        for work in (0,1,2,8):
                            s=(f,q,pos,work)
                            if producer.heat(s)<0:continue
                            for a in producer.ALPHABET:
                                r=producer.transition(s,a,arm);self.assertEqual(r,auditor.interpret(s,a,arm))
                                if r:
                                    k,j,d=a;t,rate=r;back=producer.transition(t,(k,j,1 if k=='hop' else -d),arm)
                                    self.assertEqual(back[0],s)

    def test_tampered_ancestry_is_rejected(self):
        r=copy.deepcopy(producer.trajectory(0,'candidate',True));r['objects'][-1]['parent']=None
        with self.assertRaises(AssertionError):auditor.audit_world(r)

    def test_unpriced_damage_is_rejected(self):
        r=copy.deepcopy(producer.trajectory(0,'candidate',True));e=next(e for e in r['events'] if e['action'][0]=='damage');e['after'][3]+=1
        with self.assertRaises(AssertionError):auditor.audit_world(r)
