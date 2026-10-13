"""Prepared guard regression only; no paid evidence or scientific seed queries."""
import ast,inspect,unittest
from pathlib import Path
from unittest.mock import patch
from experiments import digital_sharedlineage68_population as kernel
from experiments import digital_sharedlineage68_admission as previous
from experiments import digital_functional69_admission as admission
from experiments.digital_functional69_scientific_child import admit
from experiments import digital_functional69_scientific_child as adapter


class AdmissionGuards(unittest.TestCase):
    def setUp(self):
        self.trap=patch.object(kernel.World,'__init__',side_effect=AssertionError('World forbidden')).start()
        self.addCleanup(patch.stopall)
        self.provenance=dict(source_sha256='a'*64,configuration_sha256='b'*64)
        self.receipt=dict(self.provenance,references=16,treatment_worlds=0,original_restored_equal=True,all_paid_gates=True)
        self.reference=dict(seed=70000,kind='population',mode='faithful',inheritance_mode='parent_copy')
    def tearDown(self):self.assertEqual(self.trap.call_count,0)
    def summary(self,seed):
        return dict(verified=True,seed=seed,mode='faithful',inheritance_mode='parent_copy',route='ancestor',formation_cost=43,
          genesis_program_hash=admission.h(admission.ANCESTOR_WORDS),fuel_mode='renewed',births=12,
          turnover=dict(founder_expiry_tick=100,post_founder_instructions=128,maximum_generation=3,
                        post_founder_paid_personal_births=1,post_founder_renewed_food=1,living_descendants=1,
                        paid_personal_chains=[{'prepared':True}]))
    def test_new_membership_and_old_reserved_software_banks_refused(self):
        for seed in admission.SEEDS:self.assertFalse(admit(dict(self.reference,seed=seed),self.provenance))
        for seed in (1,2,69000,69200,70100,70300,True,70000.0):
            with self.assertRaises(AssertionError):admit(dict(self.reference,seed=seed),self.provenance)
    def test_mutation_requires_exact_all16_zero_source_configuration(self):
        request=dict(self.reference,mode='mutating')
        with self.assertRaises(AssertionError):admit(request,self.provenance)
        for field,value in (('references',15),('references',True),('treatment_worlds',1),('treatment_worlds',False),('all_paid_gates',False),('original_restored_equal',False),('source_sha256','c'*64),('configuration_sha256','c'*64)):
            with self.assertRaises(AssertionError):admit(request,self.provenance,dict(self.receipt,**{field:value}))
        self.assertTrue(admit(request,self.provenance,self.receipt))
        self.assertTrue(admit(dict(request,inheritance_mode='ancestor_copy'),self.provenance,self.receipt))
    def test_parent_child_control_domains_and_every_referee_channel(self):
        for kind in ('fork','fork_ref'):
            for slot,control in [('parent','ancestor_value_control'),('child','inherited_source_control')]:
                for role in ('sham',control):
                    request=dict(seed=70203,kind=kind,slot_kind=slot,fork_role=role)
                    with self.assertRaises(AssertionError):admit(request,self.provenance)
                    self.assertTrue(admit(request,self.provenance,self.receipt))
                wrong='inherited_source_control' if slot=='parent' else 'ancestor_value_control'
                with self.assertRaises(AssertionError):admit(dict(seed=70000,kind=kind,slot_kind=slot,fork_role=wrong),self.provenance,self.receipt)
        self.assertFalse(admit(dict(self.reference,kind='population_ref'),self.provenance))
        self.assertTrue(admit(dict(self.reference,kind='population_ref',mode='mutating'),self.provenance,self.receipt))
    def test_unregistered_roles_and_provenance_refused(self):
        with self.assertRaises(AssertionError):admit(self.reference,dict(self.provenance,configuration_sha256='UNPINNED'))
        for request in (dict(self.reference,kind='selected'),dict(self.reference,mode='selected'),dict(self.reference,inheritance_mode='ancestor_copy'),dict(seed=70000,kind='fork',slot_kind='unrelated_child',fork_role='sham'),dict(seed=70000,kind='fork',slot_kind='parent',fork_role='repair')):
            with self.assertRaises(AssertionError):admit(request,self.provenance,self.receipt)
    def test_paid_gate_body_is_unchanged_and_membership_is_explicit(self):
        a=ast.parse(inspect.getsource(admission.ordinary_gate));b=ast.parse(inspect.getsource(previous.ordinary_gate))
        self.assertEqual(ast.dump(a,include_attributes=False),ast.dump(b,include_attributes=False))
        self.assertEqual(admission.SEEDS,(70000,70001,70002,70003,70200,70201,70202,70203))
        for seed in admission.SEEDS:self.assertTrue(admission.ordinary_gate(self.summary(seed)))
        for seed in (69000,69200,70100,70300):
            with self.assertRaises(AssertionError):admission.ordinary_gate(self.summary(seed))
    def test_all16_evaluated_despite_first_gate_failure(self):
        original=[self.summary(s) for s in admission.SEEDS];restored=[self.summary(s) for s in admission.SEEDS]
        original[0]['births']=restored[0]['births']=0
        with patch.object(admission,'ordinary_gate',wraps=admission.ordinary_gate) as gate:
            self.assertFalse(admission.ordinary_admission(original,restored));self.assertEqual(gate.call_count,16)
    def test_duplicate_missing_and_unequal_export_references_refused(self):
        original=[self.summary(s) for s in admission.SEEDS];restored=[self.summary(s) for s in admission.SEEDS]
        self.assertTrue(admission.ordinary_admission(original,list(reversed(restored))))
        for wrong in (restored[:-1],restored[:-1]+[restored[0]]):
            with self.assertRaises(AssertionError):admission.ordinary_admission(original,wrong)
        restored[0]['births']=13
        with self.assertRaises(AssertionError):admission.ordinary_admission(original,restored)
    def test_each_paid_lifecycle_condition_has_an_actual_failure_boundary(self):
        for field,value in [('founder_expiry_tick',None),('post_founder_instructions',127),('maximum_generation',2),('post_founder_paid_personal_births',0),('post_founder_renewed_food',0),('living_descendants',0),('paid_personal_chains',[])]:
            summary=self.summary(70000);summary['turnover'][field]=value;self.assertFalse(admission.ordinary_gate(summary))
        summary=self.summary(70000);summary['births']=11;self.assertFalse(admission.ordinary_gate(summary))
    def test_incomplete_source_footprint_refused_before_file_or_world_access(self):
        with patch.object(adapter,'sha',side_effect=AssertionError('File hash forbidden')) as hashes:
            for pins in ({},{'experiments/digital_functional69_scientific_child.py':'a'*64}):
                with self.assertRaises(AssertionError):adapter.verify_source(Path.cwd(),pins)
            self.assertEqual(hashes.call_count,0)
    def test_wrong_module_origin_refused_without_world(self):
        with patch.object(kernel,'__file__',str(Path.cwd()/'foreign.py')):
            with self.assertRaises(AssertionError):adapter.module_origins(Path.cwd())


if __name__=='__main__':unittest.main()
