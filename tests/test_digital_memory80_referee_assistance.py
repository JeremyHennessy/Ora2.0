"""Explicitly supplied draw witnesses; default physics must refuse them."""
import unittest
from unittest.mock import patch
from experiments.digital_memory80 import World,programme
from experiments.digital_memory80_referee import audit
from experiments.digital_memory80_endpoint import paid_viable_children
RECORDINGS=[]


class Assistance(unittest.TestCase):
    def witness(self,kind,q=8,mode='variation',seed=2100080,max_population=8,horizon=256,program=None):
        program=programme(q) if program is None else program
        def draw(key,stage):
            if kind=='gate7': return 7 if stage=='gate' else 3
            if stage=='gate': return 0
            return 3 if kind=='gate0-reject8' or key[-1]==2 else 2
        with patch('experiments.digital_memory80.draw_value',side_effect=draw):
            state=World(seed,q,mode,max_population,0,code=program).run(horizon)
        args=dict(seed=seed,mode=mode,max_population=max_population,expansion_tick=0,program=program,horizon=horizon)
        RECORDINGS.append(dict(assistance=kind,configuration=args,state=state))
        proof=audit(state,software_assistance=kind,**args)
        self.assertEqual(proof['software_assistance'],kind)
        with self.assertRaises(AssertionError): audit(state,**args)
        return state,args

    def test_eight_rejections_abort_and_return_reserved_units(self):
        state,args=self.witness('gate0-reject8')
        ends=[e for e in state['events'] if e.get('sampler_finished',{}).get('abort')]
        self.assertTrue(ends)
        self.assertTrue(all(e['sampler_finished']['draws']==9 and 'writes' not in e for e in ends))
        with self.assertRaises(AssertionError): audit(state,software_assistance='gate7',**args)

    def test_rejected_allele_then_true_capacity_inheritance(self):
        state,_=self.witness('gate0-reject1-then8',q=2,horizon=512)
        children=paid_viable_children(state)
        self.assertTrue(children)
        self.assertTrue(all(c['capacity']==8 and c['paid'] and c['blank'] for c in children))
        self.assertTrue(any(e.get('sampler_finished',{}).get('draws')==3 for e in state['events']))

    def test_no_variation_keeps_parent_capacity_and_paid_draws(self):
        state,_=self.witness('gate0-reject1-then8',q=2,mode='no_variation',horizon=512)
        children=paid_viable_children(state)
        self.assertTrue(children)
        self.assertTrue(all(c['capacity']==2 for c in children))

    def test_inheritance_disabled_keeps_physical_capacity_paid(self):
        state,_=self.witness('gate0-reject1-then8',q=2,mode='inheritance_disabled',horizon=512)
        children=paid_viable_children(state)
        self.assertTrue(children)
        self.assertTrue(all(c['capacity']==8 and c['paid'] and c['blank'] for c in children))

    def test_word_energy_failure_does_not_mint_copied_words(self):
        program=[[7,8,1]]+[[6,0,0]]*21+[[18,0,0]]*2+[[10,0,0],[7,0,24]]
        state,args=self.witness('gate7',mode='no_variation',seed=2100081,max_population=1,horizon=28,program=program)
        failed=[e for e in state['events'] if e.get('copy_refused')=='word_energy']
        self.assertTrue(failed)
        self.assertEqual(failed[0]['energy_before'],3)
        self.assertNotIn('writes',failed[0])
        self.assertEqual(state['writes'],0)
        with self.assertRaises(AssertionError): audit(state,software_assistance=True,**args)


if __name__=='__main__': unittest.main()
