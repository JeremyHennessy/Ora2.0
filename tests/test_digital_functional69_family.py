"""Synthetic binding checks only; no World, seed query, or paid-life claim."""
import ast
import copy
import inspect
import unittest
from experiments import digital_functional69_family as family
from experiments.digital_functional69_contract import ANCESTOR


def fixture(edges):
    events = []; audited = []; serial = 0
    for actor, target, generation in edges:
        tick = len(events) + 1; words = []
        for index, value in enumerate(ANCESTOR):
            words.append(dict(write_id=serial, index=index, unit=100+index,
                source_unit=index, source_value=value, effective_source_value=value,
                effective_source='parent_copy', mutation_draw=99, value=value,
                mutated=False, tick=tick))
            serial += 1
        events.append(dict(tick=tick, actor=actor, writes=words))
        tick += 1; ids = [w['write_id'] for w in words]
        newborn = dict(id=target, parent=actor, generation=generation,
                       code=[[w['value'], w['unit']] for w in words])
        events.append(dict(tick=tick, actor=actor, state_hash='a'*64,
                           birth=dict(child=newborn, write_ids=ids)))
        audited.append(dict(parent=actor, child=target, generation=generation,
                            tick=tick, write_ids=ids, parent_personal_food=0))
    row = dict(seed=1, mode='mutating', inheritance_mode='parent_copy',
               fuel_mode='renewed', route='ancestor', final=dict(events=events))
    row['hash'] = family.digest(row['final'])
    summary = dict(verified=True, seed=1, mode='mutating', inheritance_mode='parent_copy',
                   fuel_mode='renewed', route='ancestor', ticks=len(events), birth_edges=audited)
    return row, summary


def rehash(row):
    row['hash'] = family.digest(row['final'])


class FamilyBindingTests(unittest.TestCase):
    def test_same_parent_child_not_first_unrelated_generation_two(self):
        row, audit = fixture([(0,1,1),(0,2,1),(2,3,2),(1,4,2),(1,5,2)])
        result = family.family_from_audited(row,audit)
        self.assertEqual(result['parent']['target'],1)
        self.assertEqual(result['child']['target'],4)
        self.assertFalse(result['stage_credit'])
        self.assertTrue(result['requires_authenticated_full_history'])

    def test_null_child_no_replacement_parent(self):
        row, audit = fixture([(0,1,1),(0,2,1),(2,3,2)])
        result = family.family_from_audited(row,audit)
        self.assertEqual(result['parent']['target'],1)
        self.assertIsNone(result['child'])

    def test_empty_history_retains_two_null_slots(self):
        row, audit = fixture([])
        result = family.family_from_audited(row,audit)
        self.assertIsNone(result['parent']); self.assertIsNone(result['child'])

    def test_source_control_preserves_actual_child_draw_and_unit(self):
        row, audit = fixture([(0,1,1),(1,2,2)])
        words = row['final']['events'][2]['writes']
        w = words[0]; w.update(source_value=9,effective_source_value=9,
                              mutation_draw=0,value=10,mutated=True)
        row['final']['events'][3]['birth']['child']['code'][0][0] = 10
        rehash(row); original = copy.deepcopy(row)
        slot = family.family_from_audited(row,audit)['child']
        self.assertEqual(slot['inherited_source_code'][0],[5,100])
        self.assertEqual(slot['born_code'][0],[10,100])
        self.assertEqual(row,original)

    def test_summary_flag_does_not_override_all_edge_binding(self):
        row, audit = fixture([(0,1,1),(0,2,1),(2,3,2)])
        audit['birth_edges'][2]['parent'] = 1
        with self.assertRaises(AssertionError): family.family_from_audited(row,audit)

    def test_bad_parent_generation_and_boolean_identity_refused(self):
        for field,value in [('parent',True),('generation',2),('id',True)]:
            row, audit = fixture([(0,1,1)])
            row['final']['events'][1]['birth']['child'][field] = value; rehash(row)
            with self.assertRaises(AssertionError): family.family_from_audited(row,audit)

    def test_stale_hash_and_event_order_refused(self):
        row,audit = fixture([(0,1,1)])
        row['final']['events'][0]['tick'] = 2
        with self.assertRaises(AssertionError): family.family_from_audited(row,audit)
        rehash(row)
        with self.assertRaises(AssertionError): family.family_from_audited(row,audit)

    def test_wrong_temporal_certificate_or_newborn_value_refused(self):
        for defect in ('tick','value','actor'):
            row,audit = fixture([(0,1,1),(1,2,2)])
            if defect=='tick': row['final']['events'][2]['writes'][0]['tick']=4
            elif defect=='value': row['final']['events'][3]['birth']['child']['code'][0][0]=31
            else: row['final']['events'][2]['actor']=0
            rehash(row)
            with self.assertRaises(AssertionError): family.family_from_audited(row,audit)

    def test_missing_duplicate_or_reused_certificate_refused(self):
        for defect in ('missing','duplicate','reuse'):
            row,audit = fixture([(0,1,1),(0,2,1)])
            ids=row['final']['events'][3]['birth']['write_ids']
            if defect=='missing': ids[0]=999
            elif defect=='duplicate': ids[0]=ids[1]
            else: row['final']['events'][3]['birth']['write_ids']=list(range(27))
            rehash(row)
            with self.assertRaises((AssertionError,KeyError)): family.family_from_audited(row,audit)

    def test_data_only_imports_no_world_or_sampler(self):
        tree=ast.parse(inspect.getsource(family))
        imports=[]
        for node in ast.walk(tree):
            if isinstance(node,ast.Import): imports.extend(a.name for a in node.names)
            elif isinstance(node,ast.ImportFrom): imports.append(node.module)
        self.assertEqual(imports,['hashlib','json','experiments.digital_functional69_contract'])
        self.assertFalse(any(isinstance(n,ast.Name) and n.id=='World' for n in ast.walk(tree)))


if __name__=='__main__': unittest.main()
