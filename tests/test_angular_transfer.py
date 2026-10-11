import math
import unittest
from experiments import angular_transfer as model
from experiments import angular_transfer_audit as audit

class AngularTests(unittest.TestCase):
    def test_raw_capital_no_prebuilt_bond(self):
        for arm in model.ARMS:
            z=model.initial(arm)
            self.assertEqual(model.field(z,arm=='function_disabled')[1],0.)
            self.assertEqual(model.accounts(z)[:2],(.375,0.))
            self.assertEqual(model.groups(z,model.field(z)[2])[0],[])

    def test_independent_polar_gradient(self):
        z=model.initial('candidate');z[0]=[.2,.3,.7,.1,.2,.3];z[1]=[-.1,-.2,-.4,0.,0.,0.]
        contacts=model.field(z)[2]
        row=next(c for c in contacts if c[:2]==(0,1))
        for a,b in zip(row[2:],audit.polar_pair(z[0],z[1])):self.assertAlmostEqual(a,b,places=14)

    def test_numerical_potential_derivative(self):
        z=model.initial('bare');z[0]=[.2,.3,.7,0.,0.,0.];z[1]=[-.1,-.2,-.4,0.,0.,0.]
        f,p,_=model.field(z)
        for i,k in ((0,0),(0,1),(0,2),(1,2)):
            h=1e-6;z[i][k]+=h;plus=model.field(z)[1];z[i][k]-=2*h;minus=model.field(z)[1];z[i][k]+=h
            self.assertAlmostEqual(f[i][k],-(plus-minus)/(2*h),places=8)

    def test_combined_angular_momentum_identity(self):
        a=[.2,.3,.7,0.,0.,0.];b=[-.1,-.2,-.4,0.,0.,0.]
        fx,fy,ti,tj,_=audit.polar_pair(a,b)
        self.assertAlmostEqual((a[0]-b[0])*fy-(a[1]-b[1])*fx+ti+tj,0.,places=14)

    def test_cutoff_and_coincident_finite(self):
        for a,b in (([0.,0.,0.,0.,0.,0.],[1.,0.,.4,0.,0.,0.]),([0.,0.,0.,0.,0.,0.],[0.,0.,.4,0.,0.,0.])):
            self.assertEqual(audit.polar_pair(a,b),(0.,0.,0.,0.,0.))

    def test_input_is_identical_not_resource_shuffle(self):
        expected=model.initial('candidate')[2:]
        for arm in model.ARMS:self.assertEqual(model.initial(arm)[2:],expected)

    def test_strict_json(self):
        with self.assertRaises(ValueError):audit.unique([('x',1),('x',2)])

    def test_reject_unregistered_resolution(self):
        with self.assertRaises(ValueError):model.simulate('candidate',64)

if __name__=='__main__':unittest.main()
