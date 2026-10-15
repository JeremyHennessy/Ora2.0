"""Source/data-only checks: no World or fresh label is evaluated."""
import json
import ast
import inspect
import types
import unittest
from unittest.mock import patch
from experiments import digital_learning81_source as old
from experiments import digital_revision84_source as source
from experiments import digital_revision84_world as world

class Revision84SourceTests(unittest.TestCase):
    def test_complete_neutral_inventory_without_targets(self):
        with patch.object(source,'target_mask',side_effect=AssertionError('target query')):
            manifest=source.manifest()
        self.assertEqual(len(manifest['roster']),18)
        self.assertEqual([manifest['roles'][f'learner{q}']['formation'] for q in (2,4,8)],[43,45,49])
        self.assertEqual([manifest['roles'][r]['formation'] for r in source.FIXED],[22,22,22,25,25,31])
        self.assertEqual(manifest['worlds'],0)
        self.assertEqual(manifest['targets_queried'],0)

    def test_source_body_reuse_and_minimum_reference_state(self):
        for role in source.ROLES:
            before=old.programme(role);after=source.programme(role)
            self.assertEqual(before[1:],after[1:])
            self.assertEqual(after[0],[7,source.descriptor(role),1])
            if role in source.FIXED:
                self.assertEqual(after[0][1],2)
                self.assertFalse({t[0] for t in after}&{2,3,19,20})
        # The bounded source qualifier intentionally instruments _genesis to
        # refuse construction. Check the namespace binder without that hook.
        self.assertEqual(world.bind(world.engine.World.__init__).__code__,world.engine.World.__init__.__code__)
        self.assertEqual(world.bind(world.engine.World.step).__code__,world.engine.World.step.__code__)

    def test_reserve_software_scope_and_foreign_refused_before_genesis(self):
        seeds=list(source.RESERVED)+(list(source.PRIMARY)+list(source.UNSEEN))+[True,2100080,-1]
        with patch.object(world,'_genesis',side_effect=AssertionError('GENESIS')) as genesis:
            for seed in seeds:
                with self.assertRaisesRegex(AssertionError,'Unregistered context'):
                    world.World(seed)
            for seed in source.RESERVED:
                with self.assertRaisesRegex(AssertionError,'Unregistered context'):
                    world.World(seed,admission=source.ADMISSION)
        genesis.assert_not_called()
        with patch.object(source,'digest',side_effect=AssertionError('label generation')) as hash_fn:
            for seed in source.RESERVED+source.PRIMARY+source.UNSEEN:
                with self.assertRaisesRegex(AssertionError,'Unregistered context'):
                    source.target_mask(seed,48)
        hash_fn.assert_not_called()

    def test_actual_read_channels_preserve_real_data(self):
        owner=types.SimpleNamespace(control_active=0,control_mode='model_erased')
        memory=world.ModelView([0,15,3,7],owner)
        self.assertEqual(memory[1],15)
        owner.control_active=1
        self.assertEqual(memory[1],0)
        owner.control_mode='history_misbound'
        self.assertEqual(memory[1],3)
        self.assertEqual(memory[3],0)
        memory[1]=9
        self.assertEqual(list(memory),[0,9,3,7])
        self.assertEqual(json.loads(json.dumps(memory)),[0,9,3,7])
        self.assertEqual(world.channel(memory,1,owner)['truthful_cell'],9)

    def test_frozen_store_only_after_cut(self):
        owner=types.SimpleNamespace(control_active=0,control_mode='update_frozen')
        memory=world.ModelView([0,0],owner)
        memory[1]=15
        owner.control_active=1
        memory[1]=0
        self.assertEqual(memory[1],15)
        owner.control_mode='intact'
        memory[1]=0
        self.assertEqual(memory[1],0)

    def test_transient_packet_scope_requires_actual_packet(self):
        scratch={'packet':None}
        labels=world.Labels(source.SOFTWARE[0],None,scratch)
        with patch.object(world,'target_mask',return_value=123) as target:
            with self.assertRaisesRegex(AssertionError,'Actual ACT packet required'):
                labels[0]
            target.assert_not_called()
            scratch['packet']=48
            self.assertEqual(labels[0],123)
            target.assert_called_once_with(source.SOFTWARE[0],48,None)

    def test_literal_scope_is_producer_free_and_reserved_input_refused(self):
        from experiments import digital_revision84_referee as referee
        tree=ast.parse(inspect.getsource(referee))
        imports={alias.name for node in tree.body if isinstance(node,ast.Import) for alias in node.names}
        self.assertEqual(imports,{'hashlib','json'})
        self.assertFalse(any(isinstance(n,ast.ImportFrom) for n in ast.walk(tree)))
        with patch.object(referee,'mask_for',side_effect=AssertionError('target query')) as target:
            for seed in source.RESERVED:
                with self.assertRaises(AssertionError):
                    referee.audit({},seed=seed,role='learner8',control='intact',program=[])
        target.assert_not_called()

if __name__=='__main__':unittest.main()
