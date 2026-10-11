import unittest
from experiments import finite_heat_transport as m
from experiments import finite_heat_transport_audit as a
class HeatTransportTests(unittest.TestCase):
    def test_finite_pair_heat_conservation(self):
        x=[0.,.2,3.,5.,7.,9.,11.,13.];h=[1.,0.,0.,0.,0.,0.,0.,0.]
        flows=m.conduct(x,h,10.)
        self.assertGreater(h[1],0.);self.assertLess(h[0],1.)
        self.assertAlmostEqual(sum(h),1.,places=14)
        self.assertTrue(all(0<=v<=mass for v,mass in zip(h,m.M)))
        self.assertAlmostEqual(h[0],1+sum(v for i,j,v in flows if i==0),places=14)
    def test_independent_common_temperature(self):
        x=[0.,.2,3.,5.,7.,9.,11.,13.];h=[1.,0.,0.,0.,0.,0.,0.,0.];v=[0.]*8;q=[0]*8
        expected=h.copy();m.conduct(x,h,.5)
        a.thermal(x,v,expected,q,.5,a.PAIRS,False,True)
        for i,j in zip(h,expected):self.assertAlmostEqual(i,j,places=14)
    def test_no_nonlocal_heat_or_capacity_reset(self):
        x=[0.,2.,4.,6.,8.,10.,12.,14.];h=[1.,1.,1.,1.,1.,4.,1.,1.];old=h.copy()
        self.assertEqual(m.conduct(x,h,100),[]);self.assertEqual(h,old)
    def test_disabled_transport_retains_every_heat_store(self):
        x=[0.,.2,3.,5.,7.,9.,11.,13.];h=[1.,0.,0.,0.,0.,0.,0.,0.];old=h.copy()
        self.assertEqual(m.conduct(x,h,10.,disabled=True),[]);self.assertEqual(h,old)
    def test_raw_common_capital_and_identical_input(self):
        expected=m.initial('candidate')
        for arm in m.ARMS:
            x,v,q=m.initial(arm)
            self.assertEqual(m.kinetic(v),1.5625);self.assertEqual(m.field(x,q)[1],0.)
            self.assertEqual((x[2:],v[2:],q[2:]),(expected[0][2:],expected[1][2:],expected[2][2:]))
            self.assertEqual(m.groups(x,v,q)[0],[])
    def test_capture_conserves_actual_translation_and_heat(self):
        x=[0.,.2,3.,5.,7.,9.,11.,13.];v=[1.,-1.,0.,0.,0.,0.,0.,0.];h=[0.]*8
        old=m.kinetic(v);w,p=m.capture(x,v,h,list(m.Q),.5)
        self.assertGreater(sum(h),0.);self.assertAlmostEqual(m.kinetic(v)+sum(h),old,places=14)
        self.assertAlmostEqual(sum(sum(row) for row in p),sum(h),places=14)
    def test_duplicate_fields_refused(self):
        with self.assertRaises(ValueError):a.unique([('x',1),('x',2)])
    def test_unregistered_run_refused(self):
        with self.assertRaises(ValueError):m.simulate('candidate',64)
if __name__=='__main__':unittest.main()
