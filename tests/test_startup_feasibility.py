import copy
import itertools
import unittest
from unittest.mock import patch
from experiments import startup_feasibility as law
from experiments import startup_feasibility_audit as audit

def config(bits='0000',mode='generic',budget=None,food='1',renewal='withdrawn'):
    return dict(bits=bits,mode=mode,budget=2*len(bits)+2 if budget is None else budget,food_bit=food,renewal=renewal)

class StartupFeasibilityTests(unittest.TestCase):
    def checked(self,c):
        record=law.simulate(c)
        self.assertEqual(audit.inspect(record,c),law.counts(record))
        return record

    def test_registered_panel_is_complete_and_independently_enumerated(self):
        a=list(law.configs()); b=list(audit.panel())
        self.assertEqual(a,b); self.assertEqual(len(a),3024)
        self.assertEqual(len({law.encode(c) for c in a}),3024)
        self.assertEqual(sum(len(list(law.requests(c))) for c in a),133920)

    def test_all_generic_words_and_food_types_have_finite_paid_endpoints(self):
        for n in (2,3,4):
            for word in itertools.product('01',repeat=n):
                bits=''.join(word)
                for food in '01':
                    with self.subTest(bits=bits,food=food):
                        c=config(bits,food=food); record=self.checked(c)
                        self.assertNotIn('C',record['initial']['objects'])
                        birth=record['terminal']['history']['D0']
                        self.assertEqual(len(birth['debits']),3*n+1)
                        self.assertIsNone(birth['parent']); self.assertIsNone(birth['template'])
                        self.assertEqual(law.counts(record)['first_function'],int(bits[-1]!=food))

    def test_budget_and_individual_reaction_knockouts(self):
        for c in [config(budget=0),config(budget=8),*(config(mode=m) for m in ('association_off','topup_off','parent_release'))]:
            with self.subTest(c=c):
                r=self.checked(c)
                self.assertNotIn('D0',r['terminal']['history'])
        c=config(mode='topup_off'); s=law.initial(c)
        for tick,q in enumerate(law.requests(c)):
            if q[0]=='release' and q[1]==0:
                self.assertEqual(sum(len(s['potential'][a]) for a in s['channels']['0']['atoms']),2)
                break
            s,_=law.step(s,c,tick,q)

    def test_template_specificity_with_equal_material_and_energy(self):
        generic=law.initial(config()); template=law.initial(config(mode='template'))
        self.assertEqual(generic['atoms'],template['atoms'])
        self.assertEqual(audit.accounting(generic,config()),audit.accounting(template,config(mode='template')))
        self.assertEqual(law.counts(self.checked(config(mode='template')))['first_function'],1)
        self.assertEqual(law.counts(self.checked(config(bits='0010',mode='template')))['first_function'],0)

    def test_ghost_has_same_formation_debit_structure_and_no_endowment(self):
        states=[]
        for mode in ('generic','ghost'):
            c=config(mode=mode); s=law.initial(c)
            for tick,q in enumerate(law.requests(c)):
                s,r=law.step(s,c,tick,q); audit.accounting(s,c)
                if q[0]=='release' and q[1]==0: break
            states.append(s)
        normal,ghost=states
        self.assertEqual(normal['history']['D0']['debits'],ghost['history']['D0']['debits'])
        self.assertEqual(normal['objects']['D0']['atoms'],ghost['objects']['D0']['atoms'])
        self.assertEqual(normal['objects']['D0']['bonds'],ghost['objects']['D0']['bonds'])
        self.assertEqual(ghost['heat']-normal['heat'],2)
        self.assertEqual(len(normal['objects']['D0']['work']),2)
        self.assertEqual(ghost['objects']['D0']['work'],[])
        self.assertEqual(law.counts(self.checked(config(mode='ghost')))['first_function'],0)

    def test_withdrawal_and_funding_provenance_are_separate(self):
        for n in (2,3,4):
            c=config('0'*n); r=self.checked(c)
            self.assertEqual(law.counts(r)['captured_resource_second'],int(n==4))
            self.assertEqual(r['terminal']['environment']['1'],r['initial']['environment']['1'])
        self.assertEqual(law.counts(self.checked(config(renewal='food_withdrawn')))['second_function'],0)
        self.assertEqual(law.counts(self.checked(config(renewal='external')))['captured_resource_second'],0)

    def test_zero_and_full_local_capacity_rejections_do_not_change_resources(self):
        c=config(budget=0); s=law.initial(c)
        after,_=law.step(s,c,0,['activate',0,'C','M0.0','A0.0'])
        self.assertEqual(after,s)
        c=config(); s=law.initial(c)
        s,_=law.step(s,c,0,['activate',0,'C','M0.0','A0.0'])
        after,_=law.step(s,c,1,['topup',0,'C','M0.0','Q0'])
        self.assertEqual(after,s)

    def test_coherent_conserving_cheaper_recharge_forgery_is_rejected(self):
        c=config(); original=law.step
        def counterfeit(s,c,t,q):
            result,r=original(s,c,t,q)
            if q[0]=='topup' and q[1]==0 and r['outcome']=='recharged':
                refunded=r['spent'].pop(); result['environment']['0'].append(refunded)
                result['heat']-=1; r['heat']-=1
            audit.accounting(result,c)
            return result,r
        with patch.object(law,'step',counterfeit): r=law.simulate(c)
        with self.assertRaisesRegex(ValueError,'divergence'): audit.inspect(r,c)

    def test_false_funding_ancestry_and_boolean_config_are_rejected(self):
        c=config(renewal='external'); valid=self.checked(c)
        for field,value in [('captured_resource_funded',True),('parent','invented')]:
            forged=copy.deepcopy(valid); forged['terminal']['history']['D1'][field]=value
            with self.assertRaises(ValueError): audit.inspect(forged,c)
        c=config(budget=0); forged=law.simulate(c); forged['config']['budget']=False
        with self.assertRaisesRegex(ValueError,'configuration'): audit.inspect(forged,c)

if __name__=='__main__': unittest.main()
