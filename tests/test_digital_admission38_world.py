import unittest
from unittest.mock import patch
from experiments import digital_admission38_world as new
from experiments import digital_history35_world as old
from experiments.digital_source37_coverage import manifest as source

class PaidAdmissionScopeTests(unittest.TestCase):
    def test_only_admission_seeds_and_closed_old_scope(self):
        self.assertEqual(new.SEEDS,(38100,38101));self.assertEqual(old.SEEDS,tuple(range(33100,33108)))
        self.assertFalse(set(new.SEEDS)&set(new.FUTURE_FRESH+new.RESERVED+old.SEEDS))

    def test_complete_frozen_source_and_references(self):
        m=new.manifest();self.assertEqual(m['candidates'],source()['candidates']);self.assertEqual(m['total_histories'],738);self.assertFalse(m['primary'])
        self.assertEqual(m['references'],old.manifest()['references']);self.assertEqual(len(new.programmes()),123)

    def test_every_identity_once_in_chunks(self):
        chunks=new.chunks();self.assertEqual(len(chunks),16);self.assertEqual(sum(chunks,[]),list(new.programmes()));self.assertEqual(len(set(sum(chunks,[]))),123)

    def test_refuses_other_seeds_modes_chunks_before_construction(self):
        with patch.object(new.law.World,'__init__',side_effect=AssertionError('fixture must not instantiate World')):
            for seed,mode,chunk in [(True,'intact',0),(33100,'intact',0),(33200,'intact',0),(38200,'intact',0),(38300,'intact',0),(38100,'bad',0),(38100,'intact',True),(38100,'intact',16)]:
                with self.assertRaises(ValueError):new.batch(seed,mode,chunk)

    def test_old_namespace_still_refuses_new_admission(self):
        with self.assertRaises(ValueError):old.batch(38100,'intact',0)

if __name__=='__main__':unittest.main()
