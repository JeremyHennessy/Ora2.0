"""Prepared69 data fixtures only; no World,paid route or scientific seed query."""
import copy,unittest
from experiments import digital_functional69_contract as c

def certificates():
    words=[]
    for i,value in enumerate(c.ANCESTOR):
        src=3 if i==0 else value;draw=105 if i==0 else 99
        words.append(dict(actor=1,index=i,write_id=1000+i,unit=200+i,source_unit=100+i,
            source_value=src,effective_source='parent_copy',effective_source_value=src,
            mutation_draw=draw,value=(src+2)%32 if i==0 else src,mutated=i==0,tick=10+i//3))
    return words

def e(births=2,food=12,port=1,censored=False):
    return dict(births=births,food=food,censored=censored,signatures=[['ACT',0,port],['MOVE',1]])

class PreparedContract(unittest.TestCase):
    def test_control_retains_child_variation_and_allocated_units(self):
        words=certificates();prior=copy.deepcopy(words);code=c.child_source_values(words)
        self.assertEqual(code[0],[6,200]);self.assertNotEqual(code[0][0],c.ANCESTOR[0])
        self.assertEqual([x[1] for x in code],list(range(200,227)));self.assertEqual(words,prior)
    def test_ancestral_source_is_noop_even_with_new_mutation(self):
        words=certificates();words[0].update(source_value=4,effective_source_value=4,value=6)
        self.assertEqual(c.child_source_values(words),[[w['value'],w['unit']] for w in words])
    def test_corrupt_certificate_or_control_role_refused(self):
        for key,value in [('mutation_draw',True),('value',4),('mutated',False),('effective_source','ancestor_copy'),('effective_source_value',4),('actor',False),('index',True)]:
            words=certificates();words[0][key]=value
            with self.subTest(key=key),self.assertRaises(AssertionError):c.child_source_values(words)
    def test_duplicate_ids_units_and_unpaid_source_alias_refused(self):
        for key in ('write_id','unit','source_unit'):
            words=certificates();words[1][key]=words[0][key]
            with self.subTest(key=key),self.assertRaises(AssertionError):c.child_source_values(words)
        words=certificates();words[0]['unit']=words[0]['source_unit']
        with self.assertRaises(AssertionError):c.child_source_values(words)
    def test_trace_length_only_and_incomplete_lifetime_give_no_strategy(self):
        sham=e();control=e(births=1);sham['signatures']+= [['MOVE',2]]
        self.assertFalse(c.contrast(sham,control,True)['new_strategy'])
        self.assertFalse(c.contrast(e(censored=True),e(births=1,port=0),True)['useful'])
    def test_inherited_source_noop_does_not_pass_despite_endpoint_advantage(self):
        r=c.functional_contribution(e(),e(births=1,port=0),e(),e(births=1,port=0),True,False,True)
        self.assertFalse(r['conditional_functional_contribution'])
    def test_prepared_functional_reachability_still_requires_full_history(self):
        r=c.functional_contribution(e(),e(births=1,port=0),e(),e(births=1,port=0),True,True,True)
        self.assertTrue(r['conditional_functional_contribution']);self.assertFalse(r['stage_credit']);self.assertTrue(r['requires_authenticated_full_history'])
        for paid,child in [(False,e()),(True,e(births=0)),(True,e(food=0))]:
            self.assertFalse(c.functional_contribution(e(),e(births=1,port=0),child,e(births=0,food=0,port=0),True,True,paid)['conditional_functional_contribution'])
    def test_conditional_bill_is_not_ordinary_viability_or_sampler_minimum(self):
        b=c.lifecycle_bill();self.assertEqual(b['min_parent_birth_debit'],67);self.assertEqual(b['min_birth_heat']+b['child_startup'],67)
        self.assertEqual(b['founder_assembly']+b['constructor_after_assembly'],128);self.assertFalse(b['viability_demonstrated'])
        with self.assertRaises(AssertionError):c.contrast(e(births=True),e(),True)

if __name__=='__main__':unittest.main()
