"""Inventory arithmetic/refusals only; no World, child or disk output."""
import copy,unittest
from experiments import digital_pilot74_inventory as inventory

class Inventory(unittest.TestCase):
    def test_complete_cost_and_role_denominators(self):
        p=inventory.plan();r=inventory.validate(p)
        self.assertEqual((r['native_children'],r['genesis'],r['hydrates'],r['steps']),(26,2,15,34816))
        self.assertGreater(r['raw_margin_bytes'],0);self.assertFalse(r['execution_admitted'])
    def test_partial_and_orphan_recover_paid_suffix_committed_zero(self):
        roles={r['name']:r for r in inventory.plan()['roles']}
        for fault in ('partial','orphan','committed','normal'):
            self.assertEqual(roles['crash/'+fault]['steps'],1024)
            self.assertEqual(roles['recover/'+fault]['steps'],1024 if fault in ('partial','orphan') else 0)
    def test_missing_or_duplicate_roles_refused(self):
        for mutation in (lambda p:p['roles'].pop(),lambda p:p['roles'].__setitem__(0,p['roles'][1])):
            p=inventory.plan();mutation(p)
            with self.assertRaises(AssertionError):inventory.validate(p)
    def test_unpaid_instruction_and_hydration_changes_refused(self):
        for key in ('genesis','hydrates','steps'):
            p=inventory.plan();p['roles'][0][key]+=1
            with self.assertRaises(AssertionError):inventory.validate(p)
    def test_duplicate_and_escaping_output_refused(self):
        for name in ('../escape','/absolute','D:/absolute','unsafe\\file'):
            p=inventory.plan();p['files'][0]['name']=name
            with self.assertRaises(AssertionError):inventory.validate(p)
        p=inventory.plan();p['files'].append(copy.deepcopy(p['files'][0]))
        with self.assertRaises(AssertionError):inventory.validate(p)
    def test_boolean_and_overlarge_cap_refused(self):
        for cap in (True,0,40*inventory.MIB+1):
            p=inventory.plan();p['files'][0]['limit']=cap
            with self.assertRaises(AssertionError):inventory.validate(p)
    def test_total_raw_overcommit_refused(self):
        p=inventory.plan()
        for i in range(40):p['files'].append(dict(name=f'extra{i}',limit=40*inventory.MIB))
        with self.assertRaises(AssertionError):inventory.validate(p)

if __name__=='__main__':unittest.main()
