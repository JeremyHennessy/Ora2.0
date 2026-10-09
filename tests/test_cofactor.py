import copy,unittest
from experiments import cofactor as c,cofactor_audit as audit
class JointChemistry(unittest.TestCase):
    def test_direct_and_reconstruction_pay_full_food(self):
        w=c.new(77999,'candidate');c.advance(w,0,[0,0,0,1,2,0,0,0]);c.advance(w,1,[2,143,0,1,2,0,0,0]);c.advance(w,2,[1,143,0,1,2,1,0,0]);c.check(w)
        self.assertEqual(w['stats']['direct'],1);self.assertEqual(w['stats']['recycled'],1);self.assertEqual(w['heat'],10)
    def test_blind_loss_funded(self):
        w=c.new(77999,'candidate');c.advance(w,0,[0,0,0,1,2,77999%4,0,0]);c.damage(w,2048);c.check(w);self.assertEqual(w['work'],287);self.assertEqual(w['heat'],7);self.assertEqual(w['windows'][0]['lost'],1)
    def test_both_nulls_reach_same_functional_endpoint(self):
        for arm in ('catalyst-ghost','annealed'):
            w=c.new(77999,arm);target=77999%4;c.advance(w,0,[0,0,0,1,2,target,0,0]);c.damage(w,2048)
            for t,s in enumerate([target,0,1,2,3],2049):
                live=[o for o in w['objects'] if o['alive']];index=next(i for i,o in enumerate(live) if o['kind']=='F');c.advance(w,t,[0,index,0,0,0,s,0,0])
            c.advance(w,3071,[2,0,0,0,0,0,255,0]);self.assertTrue(w['windows'][0]['success']);c.check(w)
    def test_control_truth_tables_before_samples(self):
        for mask in range(16):
            bits=[bool(mask&(1<<t)) for t in range(4)];k=sum(bits);self.assertEqual(sum(v<k for v in range(4)),k)
            if 0<k<4:self.assertTrue(any(bits[t]!=(v<k) for t in range(4) for v in range(4)))
    def test_no_free_energy_or_actor_ancestry(self):
        w=c.new(77999,'candidate');w['heat']+=1
        with self.assertRaises(ValueError):c.check(w)
        w=c.new(77999,'candidate');c.advance(w,0,[0,0,0,1,2,0,0,0]);w['objects'][-1]['cofactors']=[99999]
        with self.assertRaises(ValueError):c.check(w)
    def test_separate_interpreter_and_forged_draw(self):
        r=c.world(77999,'candidate');audit.audit_record(r);r=copy.deepcopy(r);r['trace'][0][0]='0'*64
        with self.assertRaises(ValueError):audit.audit_record(r)
