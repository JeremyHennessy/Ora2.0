import copy
import unittest
from experiments.thermal_dynamics import world
from experiments.thermal_dynamics_audit import audit_record

class ThermalDynamics(unittest.TestCase):
    def test_independent_all_layouts_and_prices(self):
        for c in (3,4,5):
            for seed in (83000,83001):
                for arm in ('candidate','independent','shuffled'):audit_record(world(c,seed,arm))
    def test_working_null_is_exact(self):
        a=world(3,83000,'candidate');b=world(3,83000,'shuffled');a.pop('arm');b.pop('arm');self.assertEqual(a,b)
    def test_forged_payment_refused(self):
        r=world(3,83000,'candidate');r['states'][-1][2]+=1
        with self.assertRaises(ValueError):audit_record(r)
    def test_identity_and_noise_refused(self):
        original=world(3,83000,'candidate')
        for field in ('objects','draw_sha256'):
            r=copy.deepcopy(original)
            if field=='objects':r[field][0]['parent']=999
            else:r[field]='0'*64
            with self.assertRaises(ValueError):audit_record(r)
