"""Source-only qualification: no World construction and no target queries."""
import types,unittest
from unittest.mock import patch
from experiments import digital_memory80 as old
from experiments import digital_learning81_source as s
from experiments import digital_learning81_world as w

class Source(unittest.TestCase):
    def test_manifest_and_costs_never_query_targets_or_worlds(self):
        with patch.object(w,'target_mask',side_effect=AssertionError('target forbidden')),patch.object(w.World,'__init__',side_effect=AssertionError('World forbidden')):
            m=s.manifest()
            self.assertEqual(len(m['roster']),15)
            self.assertEqual(m['roles']['learner8']['formation'],49)
            self.assertEqual(m['roles']['fixed0']['formation'],28)
            self.assertEqual(len(m['roles']['learner8']['programme']),11)
            self.assertFalse(m['stage_credit'])

    def test_all_families_share_compact_header_translation(self):
        for role in s.ROLES:
            p=s.programme(role);self.assertEqual(p[0],[7,s.descriptor(role),1])
            self.assertTrue(all(t[0] in s.OPS and t[0] not in (10,12) for t in p))
            self.assertTrue(all(0<=t[2]<len(p) for t in p if t[0] in (7,8)))
        self.assertEqual(s.programme('learner8')[5],[8,0,7])
        self.assertEqual(s.finish_pc('fixed_alternation'),2)

    def test_instance_namespaces_reuse_exact_byte_code_without_mutation(self):
        self.assertIs(w._genesis.__code__,old.World.__init__.__code__)
        self.assertIs(w._transition.__code__,old.World.step.__code__)
        self.assertIsNot(w._transition.__globals__,old.World.step.__globals__)
        first=w.bind(w._transition);second=w.bind(w._transition)
        self.assertIs(first.__code__,old.World.step.__code__)
        self.assertIsNot(first.__globals__,second.__globals__)
        self.assertIsNot(first.__globals__['MASKS'],second.__globals__['MASKS'])
        self.assertEqual(old.SOFTWARE,(2100080,2100081,2100082,2100083))
        self.assertEqual(old.MASKS,(0,255,90,165))
        self.assertFalse(set(s.RESERVED)&set(w.SEEDS))

    def test_read_lens_preserves_actual_cells_and_current_state(self):
        owner=types.SimpleNamespace(decisions=31,control_mode='model_erased')
        cells=w.ModelView([0,15],owner)
        self.assertEqual(cells[1],15)
        owner.decisions=32;self.assertEqual(cells[1],0)
        cells[0]=15;self.assertEqual(list(cells),[15,15])
        owner.control_mode='history_misbound';cells[1]=0
        self.assertEqual(cells[0],0);self.assertEqual(cells[1],15)
        self.assertEqual(list(cells),[15,0])

    def test_genesis_and_horizon_refuse_reserves_or_unregistered_modes(self):
        with patch.object(w,'_genesis',side_effect=AssertionError('unexpected genesis')) as genesis:
            for seed in s.RESERVED:
                with self.assertRaises(AssertionError):w.World(seed)
            genesis.assert_not_called()

if __name__=='__main__':unittest.main()
