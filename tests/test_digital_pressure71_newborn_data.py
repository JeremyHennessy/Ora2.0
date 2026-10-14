"""Synthetic ancestry/code-edit boundaries only; no population or outcome search."""
import ast
import copy
import inspect
import unittest
from experiments import digital_pressure71_family as family
from experiments import digital_pressure71_transition as transition


def fixture(edges, dose=1):
    events = []; audited = []; serial = 0
    for actor, target, generation in edges:
        tick = len(events)+1; words = []
        for index, value in enumerate(family.ANCESTOR):
            draw = int(family.digest([1, 'mutation', serial])[:16], 16)
            changed = draw % 100 < dose
            output = (value+1+(draw//100)%31)%32 if changed else value
            words.append(dict(write_id=serial,index=index,unit=100+index,
                source_unit=index,source_value=value,effective_source_value=value,
                effective_source='parent_copy',mutation_draw=draw,value=output,
                mutated=changed,tick=tick))
            serial += 1
        events.append(dict(tick=tick,actor=actor,writes=words))
        tick += 1; identities = [w['write_id'] for w in words]
        newborn = dict(id=target,parent=actor,generation=generation,
                       code=[[w['value'],w['unit']] for w in words])
        events.append(dict(tick=tick,actor=actor,state_hash='a'*64,
                           birth=dict(child=newborn,write_ids=identities)))
        audited.append(dict(parent=actor,child=target,generation=generation,
                            tick=tick,write_ids=identities))
    row = dict(seed=1,dose=dose,mode='mutating',inheritance_mode='parent_copy',
               fuel_mode='renewed',route='ancestor',final=dict(events=events))
    row['hash'] = family.digest(row['final'])
    summary = dict(verified=True,seed=1,dose=dose,mode='mutating',
                   inheritance_mode='parent_copy',fuel_mode='renewed',route='ancestor',
                   ticks=len(events),birth_edges=audited)
    return row, summary


def cold(slot, dose):
    state = dict(_dose=dose,seed=1,mode='mutating',fuel_mode='renewed',
        inheritance_mode='parent_copy',tick=slot['tick'],events=[],
        entities={str(slot['target']):transition.body(slot['target'],slot['parent'],
            slot['generation'],copy.deepcopy(slot['born_code']),list(range(200,216)),2)},
        turns={str(slot['target']):0},heat=123,food={'9':[0,1]},constructor_remaining=69)
    slot['post_step_hash'] = transition.h({k:v for k,v in state.items() if k!='events'})
    return state


PROVENANCE = dict(source_sha256='b'*64,configuration_sha256='c'*64)


class NewbornDataTests(unittest.TestCase):
    def test_first_g2_and_its_actual_child(self):
        row,audit=fixture([(0,1,1),(0,2,1),(2,3,2),(1,4,2),(4,5,3),(3,6,3),(3,7,3)])
        result=family.family_from_audited(row,audit)
        self.assertEqual(result['parent']['target'],3)
        self.assertEqual(result['child']['target'],6)
        self.assertFalse(result['stage_credit'])

    def test_null_child_not_unrelated_g3(self):
        row,audit=fixture([(0,1,1),(1,2,2),(1,3,2),(3,4,3)])
        result=family.family_from_audited(row,audit)
        self.assertEqual(result['parent']['target'],2)
        self.assertIsNone(result['child'])

    def test_two_null_slots(self):
        row,audit=fixture([(0,1,1)])
        result=family.family_from_audited(row,audit)
        self.assertIsNone(result['parent']);self.assertIsNone(result['child'])

    def test_dose_specific_original_draw_control(self):
        row,audit=fixture([(0,1,1),(1,2,2),(2,3,3)])
        words=family.family_from_audited(row,audit)['child']['certificates']
        for word in words:
            word.update(mutation_draw=99,value=word['source_value'],mutated=False)
        for dose, expected in [(1,4),(8,5)]:
            w=copy.deepcopy(words);w[0].update(source_value=9,effective_source_value=9,
                mutation_draw=5,value=10 if dose==8 else 9,mutated=dose==8)
            before=copy.deepcopy(w)
            code=family.child_source_values(w,dose)
            self.assertEqual(code[0],[expected,100]);self.assertEqual(w,before)

    def test_bad_dose_or_summary_binding(self):
        for dose in (True,0,2,9,1.0,'1'):
            row,audit=fixture([]);row['dose']=dose
            with self.assertRaises(AssertionError):family.family_from_audited(row,audit)
        row,audit=fixture([]);audit['dose']=8
        with self.assertRaises(AssertionError):family.family_from_audited(row,audit)

    def test_every_edge_bound_and_temporal_certificate(self):
        for defect in ('edge','time','duplicate'):
            row,audit=fixture([(0,1,1),(1,2,2)])
            if defect=='edge':audit['birth_edges'][0]['parent']=1
            elif defect=='time':row['final']['events'][2]['writes'][0]['tick']=4
            else:row['final']['events'][3]['birth']['write_ids'][1]=27
            row['hash']=family.digest(row['final'])
            with self.assertRaises(AssertionError):family.family_from_audited(row,audit)

    def test_root_edit_preserves_all_except_code_values(self):
        for dose in (1,8):
            row,audit=fixture([(0,1,1),(1,2,2)],dose)
            slot=family.family_from_audited(row,audit)['parent'];state=cold(slot,dose)
            before=copy.deepcopy(state)
            after,record=transition.transition(state,slot,row['hash'],'ancestor_value_control',PROVENANCE)
            self.assertEqual(state,before);self.assertEqual(record['dose'],dose)
            expected=copy.deepcopy(state)
            expected['entities']['2']['code']=[[v,100+i] for i,v in enumerate(family.ANCESTOR)]
            self.assertEqual(after,expected)
            self.assertTrue(transition.validate_transition(state,after,record,slot,row['hash'],'ancestor_value_control',PROVENANCE))

    def test_sham_exact_identity(self):
        row,audit=fixture([(0,1,1),(1,2,2)])
        slot=family.family_from_audited(row,audit)['parent'];state=cold(slot,1)
        after,record=transition.transition(state,slot,row['hash'],'sham',PROVENANCE)
        self.assertEqual(after,state);self.assertEqual(record['before_hash'],record['after_hash'])

    def test_child_control_retains_original_mutations(self):
        row,audit=fixture([(0,1,1),(1,2,2),(2,3,3)],8)
        slot=family.family_from_audited(row,audit)['child'];state=cold(slot,8)
        after,_=transition.transition(state,slot,row['hash'],'inherited_source_control',PROVENANCE)
        self.assertEqual(after['entities']['3']['code'],slot['inherited_source_code'])

    def test_wrong_role_or_non_cold_state_refused(self):
        row,audit=fixture([(0,1,1),(1,2,2)])
        slot=family.family_from_audited(row,audit)['parent'];state=cold(slot,1)
        with self.assertRaises(AssertionError):transition.transition(state,slot,row['hash'],'inherited_source_control',PROVENANCE)
        state['turns']['2']=1;slot['post_step_hash']=transition.h({k:v for k,v in state.items() if k!='events'})
        with self.assertRaises(AssertionError):transition.transition(state,slot,row['hash'],'sham',PROVENANCE)

    def test_forged_draw_refused_even_with_consistent_values(self):
        row,audit=fixture([(0,1,1),(1,2,2)])
        slot=family.family_from_audited(row,audit)['parent']
        w=slot['certificates'][0];w.update(mutation_draw=99,value=w['source_value'],mutated=False)
        slot['born_code'][0][0]=w['source_value'];state=cold(slot,1)
        with self.assertRaises(AssertionError):transition.transition(state,slot,row['hash'],'sham',PROVENANCE)

    def test_no_population_execution_import(self):
        for module in (family,transition):
            tree=ast.parse(inspect.getsource(module))
            imports=[n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)]
            self.assertFalse(any('population' in name or 'world' in name for name in imports))
            self.assertFalse(any(isinstance(n,ast.Name) and n.id=='World' for n in ast.walk(tree)))


if __name__=='__main__':unittest.main()
