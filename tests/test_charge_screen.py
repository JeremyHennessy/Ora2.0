import json
import unittest
from experiments import charge_screen as model
from experiments import charge_screen_audit as audit

class ChargeScreenTests(unittest.TestCase):
    def test_all_raw_layouts_have_equal_energy_and_materials(self):
        for layout in model.LAYOUTS:
            x,v=model.initial(layout)
            self.assertEqual(model.field(x)[1],0.)
            self.assertEqual(model.kinetic(v),1.5)
            self.assertEqual(sum(m*u for m,u in zip(model.MASS,v)),3.)
            self.assertEqual(model.components(x,v)[0],tuple((i,) for i in range(6)))

    def test_reciprocal_signed_potential_gradient(self):
        for x in ([-.7,0.,3.,5.,7.,9.],[0.,3.,.7,5.,7.,9.]):
            force,_,_=model.field(x)
            self.assertAlmostEqual(sum(force),0.)
            for i in range(6):
                left=x.copy();right=x.copy();left[i]-=1e-6;right[i]+=1e-6
                derivative=(model.field(right)[1]-model.field(left)[1])/2e-6
                self.assertAlmostEqual(force[i],-derivative,places=8)

    def test_like_charges_repel_unlike_attract(self):
        self.assertGreater(model.field([0.,3.,.2,5.,7.,9.])[0][2],0.)
        self.assertLess(model.field([0.,.2,3.,5.,7.,9.])[0][1],0.)

    def test_bound_edges_require_attractive_negative_relative_energy(self):
        self.assertIn((0,1),model.components([0.,.2,3.,5.,7.,9.],[0.]*6)[1])
        self.assertNotIn((0,2),model.components([0.,3.,.2,5.,7.,9.],[0.]*6)[1])
        self.assertNotIn((0,1),model.components([0.,.2,3.,5.,7.,9.],[-2.,2.,0.,0.,0.,0.])[1])

    def test_two_body_reference_conserves_energy_and_momentum(self):
        relative=.5*(1*4/(1+4))*1**2
        self.assertLess(relative,1.)
        self.assertAlmostEqual(-.6+4*.4,1.)
        self.assertAlmostEqual(.5*.6**2+2*.4**2,.5)
        self.assertAlmostEqual(2*.4**2,.32)

    def test_independent_force_contact_and_ledger(self):
        x=[-.71317832938944,0.,.4170521124421,5.,7.,9.];v=[.1,-.4,.2,0.,0.,.3]
        force,u,_=model.field(x);a,iu,k=audit._physics(x,v)
        summed=[0.]*6
        for (i,j),f in audit._contact_forces(x).items():summed[i]+=f;summed[j]-=f
        self.assertEqual(summed,force)
        self.assertEqual(a,[f/m for f,m in zip(force,model.MASS)])
        self.assertEqual(u,iu);self.assertEqual(k,model.kinetic(v))

    def test_function_ablation_is_disclosed(self):
        self.assertEqual(model.field([0.]*6,'force_disabled'),([0.]*6,0.,[]))
        self.assertEqual(audit._contact_forces([0.]*6,True),{})

    def test_unregistered_values_and_forged_types_fail(self):
        with self.assertRaises(ValueError):json.loads('{"a":1,"a":2}',object_pairs_hook=audit.unique)
        for value in (False,float('nan'),float('inf')):
            with self.assertRaises(ValueError):audit._finite({'x':value})
        with self.assertRaises(ValueError):model.initial((0,4))
        with self.assertRaises(ValueError):model.simulate((0,1),128)
        with self.assertRaises(ValueError):model.simulate((1,0),256,'force_disabled')

if __name__=='__main__':unittest.main()
