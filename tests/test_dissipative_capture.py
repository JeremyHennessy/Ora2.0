import json
import unittest
from experiments import dissipative_capture as model
from experiments import dissipative_capture_audit as audit

class CaptureTests(unittest.TestCase):
    def test_all_raw_controls_have_identical_capital(self):
        for layout in model.LAYOUTS:
            x,v=model.initial(layout)
            self.assertEqual(model.field(x)[1],0.)
            self.assertEqual(model.kinetic(v),1.5)
            self.assertEqual(model.components(x,v)[0],tuple((i,) for i in range(6)))
        self.assertEqual(sum(model.MASS),9.)

    def test_capture_conserves_energy_and_momentum(self):
        x=[0.,.2,3.,5.,7.,9.];v=[1.,-1.,0.,0.,0.,0.];heat=[0.]*6
        old=model.kinetic(v);momentum=sum(m*u for m,u in zip(model.MASS,v))
        work,pairs=model.capture(x,v,heat,1.)
        self.assertGreater(sum(heat),0.)
        self.assertAlmostEqual(model.kinetic(v)+sum(heat),old,places=14)
        self.assertAlmostEqual(sum(m*u for m,u in zip(model.MASS,v)),momentum,places=14)
        self.assertAlmostEqual(sum(heat),sum(sum(r) for r in pairs),places=14)
        self.assertAlmostEqual(sum(sum(r) for r in work),-sum(heat),places=14)

    def test_heat_capacity_is_finite_and_never_reset(self):
        x=[0.,.2,3.,5.,7.,9.];v=[3.,-3.,0.,0.,0.,0.];h=[.999,0.,0.,0.,0.,0.]
        model.capture(x,v,h,100.)
        self.assertAlmostEqual(h[0],1.,places=12)
        oldv=v.copy();oldh=h.copy();model.capture(x,v,h,100.)
        for before,after in zip(oldv+oldh,v+h):self.assertAlmostEqual(before,after,places=13)
        model.components(x,v)
        for before,after in zip(oldh,h):self.assertAlmostEqual(before,after,places=13)

    def test_binding_is_a_paid_possibility_not_a_world_witness(self):
        x=[0.,.2,3.,5.,7.,9.];v=[1.,-1.,0.,0.,0.,0.];h=[0.]*6
        self.assertNotIn((0,1),model.components(x,v)[1])
        model.capture(x,v,h,1.)
        self.assertIn((0,1),model.components(x,v)[1])
        self.assertGreater(h[0],0.)

    def test_like_charge_and_disabled_encounters_have_no_heat_channel(self):
        for x,off in [([0.,3.,.2,5.,7.,9.],False),([0.,.2,3.,5.,7.,9.],True)]:
            v=[1.,-1.,-1.,0.,0.,0.];old=v.copy();h=[0.]*6
            model.capture(x,v,h,1.,disabled=off)
            self.assertEqual(v,old);self.assertEqual(h,[0.]*6)

    def test_independent_thermal_derivation_and_boundary_arithmetic(self):
        x=[0.,.2,.6,5.,7.,9.];v=[.2,-.7,.3,0.,0.,0.];h=[0.]*6
        v2=v.copy();h2=h.copy();v3=v.copy();h3=h.copy()
        w,p=model.capture(x,v,h,.125)
        iw,ip=audit._thermal(x,v2,h2,.125)
        audit._thermal(x,v3,h3,.125,reference=True)
        self.assertEqual((v,h,w,p),(v2,h2,iw,ip))
        for expected,actual in zip(v+h,v3+h3):self.assertAlmostEqual(expected,actual,places=14)

    def test_reverse_order_retains_heat_and_common_force(self):
        x=[0.,.2,.6,5.,7.,9.];v=[.2,-.7,.3,0.,0.,0.];h=[0.]*6
        model.capture(x,v,h,.1,tuple(reversed(model.PAIRS)))
        self.assertGreater(sum(h),0.)
        f,u,_=model.field(x);a,iu,k=audit._physics(x,v)
        self.assertEqual(a,[s/m for s,m in zip(f,model.MASS)])
        self.assertEqual(u,iu);self.assertEqual(model.kinetic(v),k)

    def test_unregistered_data_refuses(self):
        with self.assertRaises(ValueError):json.loads('{"heat":0,"heat":1}',object_pairs_hook=audit.unique)
        with self.assertRaises(ValueError):audit._finite({'heat':[False]})
        with self.assertRaises(ValueError):model.simulate((1,0),256,'capture_disabled')
        with self.assertRaises(ValueError):model.simulate((0,1),64)

if __name__=='__main__':unittest.main()
