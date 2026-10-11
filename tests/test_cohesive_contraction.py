import json
import math
import unittest
from experiments import cohesive_contraction as model
from experiments import cohesive_contraction_audit as audit

class CohesionTests(unittest.TestCase):
    def test_every_raw_layout_has_identical_paid_capital(self):
        for layout in model.LAYOUTS:
            x,v = model.initial(layout)
            self.assertEqual(model.field(x)[1],0)
            self.assertEqual(model.kinetic(v),.09375)
            self.assertEqual(sum(m*u for m,u in zip(model.MASS,v)),.75)
            self.assertEqual(model.components(x,v)[0],tuple((i,) for i in range(6)))

    def test_common_force_is_potential_gradient_and_reciprocal(self):
        x = [-.7,0.,3.,5.,7.,9.]
        force,_,_ = model.field(x)
        self.assertAlmostEqual(sum(force),0)
        delta = 1e-6
        for i in range(6):
            left=x.copy();right=x.copy();left[i]-=delta;right[i]+=delta
            gradient=(model.field(right)[1]-model.field(left)[1])/(2*delta)
            self.assertAlmostEqual(force[i],-gradient,places=8)

    def test_cohesive_floor_is_finite(self):
        force,u,_=model.field([0.]*6)
        self.assertEqual(u,-15)
        self.assertEqual(force,[0.]*6)

    def test_binding_classifier_rejects_fast_unbound_crossing(self):
        x=[0.,.2,3.,5.,7.,9.]
        self.assertIn((0,1),model.components(x,[0.]*6)[1])
        self.assertNotIn((0,1),model.components(x,[-2.,2.,0.,0.,0.,0.])[1])

    def test_ablation_discloses_removed_conversion_channel(self):
        self.assertEqual(model.field([0.]*6,'cohesion_disabled'),([0.]*6,0.,[]))
        self.assertEqual(model.components([0.]*6,[0.]*6,'cohesion_disabled')[1],())

    def test_independent_equations_agree_on_force_and_energy(self):
        x=[-.7,0.,.4,5.,7.,9.];v=[.1,-.4,.2,0.,0.,.3]
        f,u,_=model.field(x)
        a,independent_u,k=audit._physics(x,v)
        self.assertEqual([f[i]/model.MASS[i] for i in range(6)],a)
        self.assertEqual(u,independent_u)
        self.assertEqual(model.kinetic(v),k)

    def test_forgeries_and_unregistered_input_fail_closed(self):
        with self.assertRaises(ValueError): json.loads('{"a":0,"a":1}',object_pairs_hook=audit.unique)
        for value in (float('nan'),float('inf'),False):
            with self.assertRaises(ValueError): audit._finite({'x':value})
        with self.assertRaises(ValueError):model.initial((0,4))
        with self.assertRaises(ValueError):model.simulate((0,1),128)
        with self.assertRaises(ValueError):model.simulate((1,2),256,'cohesion_disabled')

    def test_pair_work_and_independent_ode_use_consistent_derivative(self):
        x=[-.71317832938944,0.,.4170521124421,5.,7.,9.]
        summed=[0.]*6
        for (a,b),f in audit._contact_forces(x).items():
            summed[a]+=f;summed[b]-=f
        acceleration=audit._physics(x,[0.]*6)[0]
        self.assertEqual([summed[i]/model.MASS[i] for i in range(6)],acceleration)
        self.assertEqual(audit._contact_forces(x,True),{})

if __name__ == '__main__': unittest.main()
