"""Prepared literal-boundary comparisons; no organism continuation is run."""
import ast
import copy
import inspect
import unittest
from experiments import digital_pressure71_referee as referee
from experiments import digital_pressure71_family as family
from experiments import digital_pressure71_transition as producer
from tests.test_digital_pressure71_newborn_data import fixture,cold,PROVENANCE


class LiteralBoundaryTests(unittest.TestCase):
    def test_literal_has_only_standard_library_imports(self):
        tree=ast.parse(inspect.getsource(referee))
        imports=[node for node in ast.walk(tree) if isinstance(node,(ast.Import,ast.ImportFrom))]
        self.assertEqual(len(imports),1)
        self.assertIsInstance(imports[0],ast.Import)
        self.assertEqual([a.name for a in imports[0].names],['hashlib','json'])

    def test_independent_neutral_roster_and_null(self):
        for edges in ([(0,1,1),(1,2,2),(1,3,2),(3,4,3)],
                      [(0,1,1),(1,2,2),(1,3,2),(3,4,3),(2,5,3)]):
            for dose in (1,8):
                row,audit=fixture(edges,dose)
                actual=referee.family_from_replayed(row,audit)
                expected=family.family_from_audited(row,audit)
                self.assertEqual(actual,{k:expected[k] for k in ('parent','child')})

    def test_literal_cold_controls_match_declared_boundary(self):
        for dose in (1,8):
            row,audit=fixture([(0,1,1),(1,2,2),(2,3,3)],dose)
            slots=family.family_from_audited(row,audit)
            for slot_kind,role in [('parent','sham'),('parent','ancestor_value_control'),
                                   ('child','sham'),('child','inherited_source_control')]:
                slot=slots[slot_kind];before=cold(slot,dose)
                self.assertEqual(referee.transition(before,slot,row['hash'],role,PROVENANCE),
                                 producer.transition(before,slot,row['hash'],role,PROVENANCE))

    def test_wrong_dose_role_or_warm_newborn_refused(self):
        for defect in ('dose','role','turns'):
            row,audit=fixture([(0,1,1),(1,2,2)])
            slot=family.family_from_audited(row,audit)['parent'];before=cold(slot,1);role='sham'
            if defect=='dose':before['_dose']=True
            if defect=='role':role='inherited_source_control'
            if defect=='turns':before['turns']['2']=1
            slot['post_step_hash']=referee.h({k:v for k,v in before.items() if k!='events'})
            with self.assertRaises(AssertionError):referee.transition(before,slot,row['hash'],role,PROVENANCE)

    def test_forged_certificate_is_not_repaired_by_hash(self):
        row,audit=fixture([(0,1,1),(1,2,2)])
        slot=family.family_from_audited(row,audit)['parent']
        word=slot['certificates'][0];word['mutation_draw']^=1
        before=cold(slot,1)
        with self.assertRaises(AssertionError):referee.transition(before,slot,row['hash'],'sham',PROVENANCE)

    def test_rehashed_empty_history_not_authenticated(self):
        # Supplying plausible metadata and self-consistent final hash is insufficient.
        for dose in (1,8):
            row=dict(version='DIGITAL-PRESSURE-SELECTION-71-POPULATION-v2',seed=1,
                dose=dose,horizon=64,software_only=True,mode='mutating',route='ancestor',
                inheritance_mode='parent_copy',fuel_mode='renewed',
                genesis_program=[family.ANCESTOR[i:i+3] for i in range(0,27,3)],
                ancestor_supplied=True,checkpoint_replay=True,learning_demonstrated=False,
                checkpoint={},final=dict(events=[],tick=0))
            row['hash']=referee.h(row['final'])
            with self.assertRaises(AssertionError):referee.audit_history(row)

    def test_unsupported_scientific_scope_refused_before_sampler(self):
        from unittest.mock import patch
        row=dict(version='DIGITAL-PRESSURE-SELECTION-71-POPULATION-v2',seed=74000,
            dose=1,horizon=512,software_only=True,mode='mutating',route='ancestor',
            inheritance_mode='parent_copy',fuel_mode='renewed',genesis_program=[],
            ancestor_supplied=True,checkpoint_replay=True,learning_demonstrated=False,
            checkpoint={},final={},hash='a'*64)
        for software in (True,False):
            row['software_only']=software
            with patch.object(referee,'h',side_effect=RuntimeError('sampler reached')):
                with self.assertRaises(AssertionError):referee.audit_history(row)


if __name__=='__main__':unittest.main()
