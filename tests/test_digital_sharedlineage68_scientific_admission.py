"""Constructor-trapped adapter guards, using disclosed prepared receipts only."""
import unittest
from unittest.mock import patch
from experiments import digital_sharedlineage68_population as kernel
from experiments.digital_sharedlineage68_scientific_child import admit


class AdmissionGuards(unittest.TestCase):
    def setUp(self):
        self.trap=patch.object(kernel.World,'__init__',side_effect=AssertionError('World forbidden'))
        self.trap.start();self.addCleanup(self.trap.stop)
        self.provenance=dict(source_sha256='a'*64,configuration_sha256='b'*64)
        self.receipt=dict(self.provenance,references=16,treatment_worlds=0,original_restored_equal=True,all_paid_gates=True)
        self.reference=dict(seed=69000,kind='population',mode='faithful',inheritance_mode='parent_copy')
    def test_all_science_references_and_reserved_rejection(self):
        for seed in (69000,69001,69002,69003,69200,69201,69202,69203):
            self.assertFalse(admit(dict(self.reference,seed=seed),self.provenance))
        for seed in (1,2,69100,69300,True,69000.0):
            with self.assertRaises(AssertionError):admit(dict(self.reference,seed=seed),self.provenance)
    def test_mutation_requires_all16_and_exact_zero(self):
        request=dict(self.reference,mode='mutating')
        with self.assertRaises(AssertionError):admit(request,self.provenance)
        for field,value in (('references',15),('references',True),('treatment_worlds',1),('treatment_worlds',False),('all_paid_gates',False),('original_restored_equal',False)):
            with self.assertRaises(AssertionError):admit(request,self.provenance,dict(self.receipt,**{field:value}))
        self.assertTrue(admit(request,self.provenance,self.receipt))
        self.assertTrue(admit(dict(request,inheritance_mode='ancestor_copy'),self.provenance,self.receipt))
    def test_both_generations_and_both_counterfactual_roles(self):
        for generation in (1,2):
            for role in ('sham','ancestor_value_control'):
                request=dict(seed=69203,kind='fork',generation=generation,fork_role=role)
                with self.assertRaises(AssertionError):admit(request,self.provenance)
                self.assertTrue(admit(request,self.provenance,self.receipt))
        for generation in (0,3,True,1.0):
            with self.assertRaises(AssertionError):admit(dict(seed=69000,kind='fork',generation=generation,fork_role='sham'),self.provenance,self.receipt)
    def test_provenance_and_unregistered_roles_refused(self):
        request=dict(self.reference,mode='mutating')
        with self.assertRaises(AssertionError):admit(self.reference,dict(self.provenance,configuration_sha256='UNPINNED'))
        for field in ('source_sha256','configuration_sha256'):
            with self.assertRaises(AssertionError):admit(request,self.provenance,dict(self.receipt,**{field:'c'*64}))
        for altered in (dict(self.reference,inheritance_mode='ancestor_copy'),dict(self.reference,mode='selected'),dict(self.reference,kind='selected'),dict(seed=69000,kind='fork',generation=1,fork_role='repair')):
            with self.assertRaises(AssertionError):admit(altered,self.provenance,self.receipt)
    def test_referee_channels_obey_same_admission(self):
        self.assertFalse(admit(dict(self.reference,kind='population_ref'),self.provenance))
        self.assertTrue(admit(dict(self.reference,kind='population_ref',mode='mutating'),self.provenance,self.receipt))
        self.assertTrue(admit(dict(seed=69000,kind='fork_ref',generation=2,fork_role='sham'),self.provenance,self.receipt))


if __name__=='__main__':unittest.main()
