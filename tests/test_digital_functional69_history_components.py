"""Prepared69 boundary/independence checks; complete histories still unqualified."""
import ast
import copy
import inspect
import unittest
from unittest.mock import patch
from experiments import digital_sharedlineage68_population as kernel
from experiments import digital_sharedlineage68_fork_interpret as old_referee
from experiments import digital_functional69_family as family
from experiments import digital_functional69_transition as producer
from experiments import digital_functional69_referee as referee
from experiments import digital_functional69_world as wrapper
from test_digital_sharedlineage68_transition_components import prepared, PROVENANCE
from test_digital_functional69_family import fixture


def witness(generation=1):
    state,slot=prepared()
    if generation==2:
        slot.update(target=2,parent=1,generation=2)
        for w in slot['certificates']:w['actor']=1
        state['entities']={2:referee.body(2,1,2,copy.deepcopy(slot['born_code']),list(range(127,143)),2)}
        state['turns']={0:256,1:256,2:0}
        slot['post_step_hash']=referee.h({k:v for k,v in state.items() if k!='events'})
    return state,slot


class FunctionalHistoryComponents(unittest.TestCase):
    def setUp(self):
        trap=patch.object(kernel.World,'__init__',side_effect=AssertionError('No World in prepared checks'))
        self.spy=trap.start();self.addCleanup(trap.stop)
        self.addCleanup(lambda:self.assertEqual(self.spy.call_count,0))

    def test_parent_child_all_role_parity_and_sham(self):
        for generation,role in [(1,'sham'),(1,'ancestor_value_control'),(2,'sham'),(2,'inherited_source_control')]:
            state,slot=witness(generation)
            a=producer.transition(state,slot,'c'*64,role,PROVENANCE)
            with patch.object(producer,'transition',side_effect=AssertionError('Producer unavailable')):
                self.assertEqual(referee.transition(state,slot,'c'*64,role,PROVENANCE),a)
            if role=='sham':self.assertEqual(a[0],referee.clone(state))

    def test_child_control_preserves_mutation_and_units(self):
        state,slot=witness(2)
        after,record=referee.transition(state,slot,'c'*64,'inherited_source_control',PROVENANCE)
        code=referee.actor_record(after['entities'],2)['code']
        for i,w in enumerate(slot['certificates']):
            value=referee.ANCESTOR_WORDS[i]
            if w['mutation_draw']%100<8:value=(value+1+(w['mutation_draw']//100)%31)%32
            self.assertEqual(code[i],[value,w['unit']])
        self.assertTrue(any(w['mutated'] for w in slot['certificates']))
        self.assertNotEqual([v for v,u in code],referee.ANCESTOR_WORDS)
        self.assertEqual(record['certificates'],slot['certificates'])

    def test_corrupted_child_sampler_cannot_mislead_referee(self):
        state,slot=witness(2)
        planted=[[v,slot['born_code'][i][1]] for i,v in enumerate(referee.ANCESTOR_WORDS)]
        with patch.object(producer,'child_source_values',return_value=planted):
            bad=producer.transition(state,slot,'c'*64,'inherited_source_control',PROVENANCE)
            good=referee.transition(state,slot,'c'*64,'inherited_source_control',PROVENANCE)
            self.assertNotEqual(bad,good)

    def test_roster_does_not_use_corrupted_producer_family(self):
        row,audit=fixture([(0,1,1),(0,2,1),(2,3,2),(1,4,2),(1,5,2)])
        with patch.object(family,'family_from_audited',return_value={'parent':None,'child':None}):
            result=referee.family_from_replayed(row,audit)
        self.assertEqual(result['parent']['target'],1);self.assertEqual(result['child']['target'],4)
        row,audit=fixture([(0,1,1),(0,2,1),(2,3,2)])
        self.assertIsNone(referee.family_from_replayed(row,audit)['child'])

    def test_only_code_values_change_after_expiry_boundary(self):
        state,slot=witness(2);before=copy.deepcopy(state)
        after,record=referee.transition(state,slot,'c'*64,'inherited_source_control',PROVENANCE)
        restored=referee.clone(after);referee.actor_record(restored['entities'],2)['code']=copy.deepcopy(slot['born_code'])
        self.assertEqual(restored,referee.clone(before));self.assertEqual(state,before)
        self.assertEqual(record['before_hash'],referee.h(state))
        self.assertEqual(record['after_hash'],referee.h(after))

    def test_cold_channels_refused_even_rehashed(self):
        for key,value in [('energy',13),('pc',1),('registers',[1,0]),('memory',[1]*8),('feedback',1),('cue',1),('inbox',0),('nursery',[{}])]:
            state,slot=witness(2);state['entities'][2][key]=value
            slot['post_step_hash']=referee.h({k:v for k,v in state.items() if k!='events'})
            with self.assertRaises(AssertionError):referee.transition(state,slot,'c'*64,'sham',PROVENANCE)

    def test_role_domains_reject_before_any_world(self):
        for generation,role in [(1,'inherited_source_control'),(2,'ancestor_value_control')]:
            state,slot=witness(generation)
            for helper in (producer.transition,referee.transition):
                with self.assertRaises(AssertionError):helper(state,slot,'c'*64,role,PROVENANCE)
        for kind,role in [('parent','inherited_source_control'),('child','ancestor_value_control')]:
            with self.assertRaises(AssertionError):wrapper.history({},kind,role,PROVENANCE)

    def test_temporal_draw_unit_and_identity_refusals(self):
        for key,value in [('tick',40),('mutation_draw',True),('mutation_draw',0),('source_value',32),('unit',512),('unit',True)]:
            state,slot=witness(2);slot['certificates'][0][key]=value
            with self.assertRaises(AssertionError):referee.transition(state,slot,'c'*64,'sham',PROVENANCE)
        state,slot=witness(2);state['turns'][2]=1
        with self.assertRaises(AssertionError):referee.transition(state,slot,'c'*64,'sham',PROVENANCE)

    def test_referee_imports_only_standard_library(self):
        tree=ast.parse(inspect.getsource(referee));imports=[]
        for node in ast.walk(tree):
            if isinstance(node,ast.Import):imports.extend(a.name for a in node.names)
            elif isinstance(node,ast.ImportFrom):imports.append(node.module)
        self.assertEqual(imports,['hashlib','json'])

    def test_literal_vm_replay_ast_unchanged(self):
        old=ast.parse(inspect.getsource(old_referee.audit_history))
        new=ast.parse(inspect.getsource(referee.audit_history))
        self.assertEqual(ast.dump(old,include_attributes=False),ast.dump(new,include_attributes=False))

    def test_ancestral_sources_are_true_noop_despite_child_variation(self):
        state,slot=witness(2)
        for i,w in enumerate(slot['certificates']):
            value=referee.ANCESTOR_WORDS[i];draw=w['mutation_draw']
            out=(value+1+(draw//100)%31)%32 if draw%100<8 else value
            w.update(source_value=value,effective_source_value=value,value=out,mutated=out!=value)
            state['entities'][2]['code'][i][0]=out
        slot['born_code']=copy.deepcopy(state['entities'][2]['code'])
        slot['post_step_hash']=referee.h({k:v for k,v in state.items() if k!='events'})
        after,record=referee.transition(state,slot,'c'*64,'inherited_source_control',PROVENANCE)
        self.assertEqual(after,referee.clone(state));self.assertEqual(record['code_value_mask'],[])

    def test_literal_full_audit_precedes_any_family_derivation(self):
        row=dict(version=referee.VERSION,natural=dict(inheritance_mode='parent_copy',mode='mutating',fuel_mode='renewed',route='ancestor',genesis_program=[referee.ANCESTOR_WORDS[i:i+3] for i in range(0,27,3)]),branch=None,slot_kind='child',role='sham',transition=None,provenance=PROVENANCE)
        with patch.object(referee,'audit_history',side_effect=AssertionError('Unpaid natural history')) as audit:
            with patch.object(referee,'family_from_replayed') as roster:
                with self.assertRaises(AssertionError):referee.audit(row,PROVENANCE)
                self.assertEqual(audit.call_count,1);self.assertEqual(roster.call_count,0)


if __name__=='__main__':unittest.main()
