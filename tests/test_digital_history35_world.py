import unittest
from experiments import digital_history35_world as fresh
from experiments import digital_source32_world as frozen
from experiments.digital_history33_endpoint import FRESH_SEEDS, RESERVED_SEEDS

class FreshScopeTests(unittest.TestCase):
    def test_exact_fresh_scope_reserves_unopened(self):
        self.assertEqual(fresh.SEEDS,FRESH_SEEDS)
        self.assertFalse(set(fresh.SEEDS)&set(RESERVED_SEEDS))
        self.assertEqual(frozen.SEEDS,(32100,32101))
    def test_whole_source_and_programmes_unchanged(self):
        self.assertEqual(fresh.programmes(),frozen.programmes())
        self.assertEqual(fresh.manifest()['candidates'],frozen.manifest()['candidates'])
        self.assertEqual(fresh.manifest()['total_histories'],1608)
    def test_chunks_cover_all67(self):
        self.assertEqual(fresh.chunks(),frozen.chunks())
        self.assertEqual(len(set(sum(fresh.chunks(),[]))),67)
    def test_invalid_seed_control_chunk_before_world(self):
        for seed,mode,chunk in [(True,'intact',0),(32100,'intact',0),(33200,'intact',0),(33100,'bad',0),(33100,'intact',True),(33100,'intact',9)]:
            with self.assertRaises(ValueError):fresh.batch(seed,mode,chunk)
        with self.assertRaises(AssertionError):fresh.World(33200,'faithful','missing')
    def test_old_scope_still_rejects_fresh(self):
        with self.assertRaises(ValueError):frozen.batch(33100,'intact',0)

if __name__=='__main__':unittest.main()
