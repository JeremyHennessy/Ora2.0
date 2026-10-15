"""Literal replay coverage on prospectively enumerated software fixtures only."""
import unittest
from unittest.mock import patch
from experiments.digital_memory80 import World,programme
from experiments.digital_memory80_referee import audit,duplicate


class Referee(unittest.TestCase):
    def replay(self,seed=2100080,capacity=8,mode='no_variation',max_population=1,
               expansion_tick=1536,code=None,horizon=1024):
        program=programme(capacity) if code is None else code
        state=World(seed,capacity,mode,max_population,expansion_tick,code=program).run(horizon)
        result=audit(state,seed=seed,mode=mode,max_population=max_population,
                     expansion_tick=expansion_tick,program=program,horizon=horizon)
        self.assertTrue(result['verified'])
        return state

    def test_complete_declared_seed_and_mode_denominators(self):
        for seed in range(2100080,2100084):
            for mode in ('variation','no_variation','inheritance_disabled'):
                with self.subTest(seed=seed,mode=mode):
                    self.replay(seed=seed,mode=mode,max_population=8,expansion_tick=0)

    def test_context_expansion_and_cap_losses(self):
        self.replay(seed=2100082,code=[[7,8,1],[4,0,0],[6,0,0],[7,0,1]],horizon=1664)

    def test_age_death_energy_and_full_material_reclamation(self):
        state=self.replay(code=[[7,8,1],[6,0,0],[1,1,0],[7,0,1]],horizon=2050)
        self.assertEqual(state['events'][-1]['death']['cause'],'installed_age_law')

    def test_unconsumed_lease_return_on_energy_death(self):
        state=self.replay(code=[[7,8,1],[0,0,0],[7,0,1]],horizon=150)
        self.assertEqual(state['leases'],{})
        self.assertIn('0',state['food'])

    def test_absence_read_and_less_used_ordinary_opcodes(self):
        self.replay(code=[[7,2,1],[6,0,0],[1,1,0],[7,0,1]],horizon=1024)
        self.replay(code=[[7,4,1],[4,0,15],[3,3,0],[2,1,3],[5,0,1],
                          [18,0,0],[19,0,1],[20,1,0],[21,0,0],[8,0,1],[7,0,1]],horizon=150)

    def test_forced_sampler_assistance_is_not_a_natural_receipt(self):
        # This intentionally disclosed host patch is a software witness only.
        # The natural-law referee must reject it rather than trusting the draw.
        with patch('experiments.digital_memory80.draw_value',return_value=0):
            state=World(2100080,8,'variation',8,0).run(120)
        with self.assertRaises(AssertionError):
            audit(state,seed=2100080,mode='variation',max_population=8,
                  expansion_tick=0,program=programme(8),horizon=120)


if __name__=='__main__': unittest.main()
