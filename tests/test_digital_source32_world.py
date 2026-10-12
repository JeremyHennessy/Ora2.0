import unittest
from experiments.digital_source32_world import programmes,chunks,install,batch,World
from experiments.digital_source32_admission import manifest
from experiments import digital_pc31_world as frozen

class PaidScopeTests(unittest.TestCase):
    def test_structural_chunks_cover_every_role_once(self):
        parts=chunks();self.assertEqual([len(x) for x in parts],[8]*8+[3]);self.assertEqual(sum(parts,[]),list(programmes()))
        self.assertEqual(len(set(sum(parts,[]))),67)
    def test_candidate_codes_and_static_ancestry_unchanged(self):
        codes=programmes();self.assertTrue(all(codes[f"candidate{x['candidate_id']}"]==x['program'] for x in manifest()['candidates']))
        self.assertTrue(all(op[0] in (1,2,3,4,5,6,7,8,18) for code in codes.values() for op in code))
    def test_canonical_registry_deduplicates_only_identical_genotypes(self):
        codes,routes=install();self.assertEqual(set(routes),set(codes))
        for role,code in codes.items():self.assertEqual(routes[role],'genome-'+frozen.law.h(code))
    def test_invalid_input_rejected_before_world_construction(self):
        for seed,mode,chunk in [(True,'intact',0),(31100,'intact',0),(32100,'other',0),(32100,'intact',True),(32100,'intact',9)]:
            with self.assertRaises(ValueError):batch(seed,mode,chunk)
        with self.assertRaises(AssertionError):World(32100,'mutating','missing')
    def test_frozen31_registration_not_broadened(self):
        self.assertEqual(frozen.SEEDS,(31100,31101));self.assertEqual(frozen.VERSION,'DIGITAL-PC-CONTROLS-31-PHASE2-v1')
        with self.assertRaises(ValueError):frozen.batch(32100,'intact')
