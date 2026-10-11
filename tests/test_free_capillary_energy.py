import math
import unittest
from experiments.free_capillary_energy import evaluate


class EnergyGradientTests(unittest.TestCase):
    def setUp(self):
        self.s=[-2.,0.,2.];self.c=[.2,.6,.3];self.x=[-.7,.9]

    def difference(self,group,index):
        args=[self.s.copy(),self.c.copy(),self.x.copy()];h=1e-6
        args[group][index]+=h;plus=evaluate(*args)['free_energy']
        args[group][index]-=2*h;minus=evaluate(*args)['free_energy']
        return (plus-minus)/(2*h)

    def test_solid_force_is_negative_energy_gradient(self):
        row=evaluate(self.s,self.c,self.x)
        for i,f in enumerate(row['solid_force']):self.assertAlmostEqual(f,-self.difference(2,i),places=8)

    def test_material_recoil_includes_gradient_and_wetting(self):
        row=evaluate(self.s,self.c,self.x)
        for i,f in enumerate(row['material_force']):self.assertAlmostEqual(f,-self.difference(0,i),places=8)

    def test_chemical_derivative(self):
        row=evaluate(self.s,self.c,self.x)
        for i,mu in enumerate(row['chemical_derivative']):self.assertAlmostEqual(mu,self.difference(1,i),places=8)

    def test_common_translation_preserves_energy_and_forces(self):
        before=evaluate(self.s,self.c,self.x)
        after=evaluate([s+17 for s in self.s],self.c,[x+17 for x in self.x])
        for field in ('material_force','solid_force'):
            for a,b in zip(before[field],after[field]):self.assertAlmostEqual(a,b,places=13)
        self.assertAlmostEqual(before['free_energy'],after['free_energy'],places=13)

    def test_total_reaction_and_unknown_work(self):
        row=evaluate(self.s,self.c,self.x)
        self.assertAlmostEqual(sum(row['material_force'])+sum(row['solid_force']),0,places=14)
        for key in ('internal_energy','net_work','physical_cost'):self.assertIsNone(row[key])
        self.assertFalse(row['dynamics_executed']);self.assertFalse(row['admitted'])

    def test_invalid_geometry_and_material_not_repaired_silently(self):
        for args in (([0,0],[.2,.6],self.x),(self.s,[.2,1.1,.3],self.x),([0,math.inf],[.2,.6],self.x)):
            with self.assertRaises(ValueError):evaluate(*args)


if __name__=='__main__':unittest.main()
