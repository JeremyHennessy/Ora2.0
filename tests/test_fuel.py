import copy,unittest
from experiments import fuel,fuel_audit

class FuelAccounting(unittest.TestCase):
    def test_paid_activation(self):
        w=fuel.initial(76999,'candidate');self.assertEqual(fuel.advance(w,0,[0,0,1,2,0,0]),['activate',0,0,None]);self.assertEqual(w['heat'],2);self.assertEqual(w['food'][0],1)
    def test_bond_and_recycled_atoms(self):
        w=fuel.initial(76999,'candidate');fuel.advance(w,0,[0,0,1,2,0,0]);fuel.advance(w,1,[1,0,1,2,0,0])
        self.assertEqual(w['objects'][-1]['parents'],[0,1]);self.assertEqual(w['objects'][-1]['fuel'],0)
        fuel.advance(w,2,[2,22,0,0,0,0]);self.assertEqual(w['stats']['cleavage'],1);self.assertEqual(w['heat'],4);fuel.check(w)
    def test_no_free_charge_or_fuel_reuse(self):
        w=fuel.initial(76999,'candidate');fuel.advance(w,0,[0,0,1,2,0,0]);self.assertIsNone(fuel.advance(w,1,[0,1,2,3,0,0]));w['heat']-=1
        with self.assertRaises(ValueError):fuel.check(w)
    def test_all_nulls_can_form(self):
        for arm in fuel.ARMS:
            w=fuel.initial(76999,arm);fuel.advance(w,0,[0,0,1,2,0,0]);self.assertIsNotNone(fuel.advance(w,1,[1,0,1,2,0,0]));fuel.check(w)
    def test_starvation_retains_energy_and_mass(self):
        w=fuel.initial(76999,'fuel-withdrawn');fuel.advance(w,2048,[0,0,1,2,0,0]);self.assertEqual(w['food'],[2]*96);self.assertEqual(w['heat'],0)
    def test_independent_authored_world_and_forgery(self):
        r=fuel.world(76999,'candidate');fuel_audit.audit_record(r)
        for field in ('energy','draw','ancestry'):
            forged=copy.deepcopy(r)
            if field=='energy':forged['final']['heat']+=1
            elif field=='draw':forged['trace'][0][0][0]^=1
            else:forged['final']['objects'][-1]['parents']=[99999]
            with self.assertRaises(ValueError):fuel_audit.audit_record(forged)
