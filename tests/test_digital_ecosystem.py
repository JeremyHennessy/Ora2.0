import copy
import unittest
from experiments.digital_ecosystem import World, digest
from experiments.digital_ecosystem_audit import audit_world

def record(world,limit=64):
    r=world.run(limit);r['checkpoint_replay']=True;return r

class DigitalEcosystemTests(unittest.TestCase):
    def test_birth_endpoint_and_forged_parent_refusal(self):
        r=record(World(0,'faithful'))
        self.assertGreater(audit_world(r)['births'],0)
        bad=copy.deepcopy(r);b=next(e for e in bad['events'] if 'birth' in e)
        b['birth']['write_events']=[]
        with self.assertRaises(AssertionError):audit_world(bad)

    def test_disabled_copy_and_resource_denial(self):
        self.assertEqual(audit_world(record(World(1,'copy_disabled')))['births'],0)
        x=World(1);x.heat=20*len(x.food);x.food={};x.check()
        self.assertEqual(x.run(64)['births'],0)

    def test_checkpoint_and_no_opcode_escape(self):
        x=World(2);x.run(32);y=World.restore(x.snapshot())
        self.assertEqual(x.run(128),y.run(128))
        x=World(3);x.entities[0]['code'][0][0]='__import__("os")'
        with self.assertRaises(AssertionError):x.check()

    def test_instruction_fixtures_are_not_discovery(self):
        # Software reachability/accounting only, not emergent behavior.
        for op in range(16):
            x=World(4,'faithful');x.entities[0]['pc']=4
            # Primitive unit assertions use direct software setup only.
            e=x.entities[0];e['code'][4][0]=op;e['r0']=0;e['r1']=1
            x.step();x.check()
            self.assertEqual(x.tick,1)
