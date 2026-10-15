"""Finite scope/precharge checks only; no World or target is constructed."""
import copy
import json
import unittest
from experiments.digital_arbitration85_cold_child import CONFIG, scope
from experiments.digital_arbitration85_cold_plan import ROLES, capacity, layout, registration_capacity, M


class ColdCustody(unittest.TestCase):
    def base(self):
        return dict(configuration=copy.deepcopy(CONFIG), source_files={}, source_sha='',
                    config_sha='', role='original:generate', kind='generate', input=None,
                    grant={}, seal='')

    def test_exact_scopes_and_no_foreign_case(self):
        self.assertEqual(scope(self.base()), 'generate')
        for field, value in [('role', 'original:1009400:generate'), ('kind', 'audit')]:
            request = self.base(); request[field] = value
            with self.assertRaises(AssertionError): scope(request)
        for field, value in [('horizon', 64), ('seed', 1009300), ('software_only', 1),
                             ('cases', [[8, 0, 'model'], [8, 0, 'constant']])]:
            request = self.base(); request['configuration'][field] = value
            with self.assertRaises(AssertionError): scope(request)
        request = self.base(); request['input'] = {'copied_state': 1}
        with self.assertRaises(AssertionError): scope(request)

    def test_all_output_and_archive_slots_precharged(self):
        raw, failure, limits = layout({'a.py': 100}, {'owner.py': 50}, 1000)
        self.assertEqual(sum(raw.values()), limits['raw'])
        self.assertEqual(sum(failure.values()), limits['failure'])
        self.assertEqual(limits['restore'], limits['raw']+limits['failure'])
        self.assertGreaterEqual(limits['archive'], limits['restore']+4*M)
        self.assertEqual(len([n for n in raw if n.startswith('native/')]), 7)
        for role in ROLES:
            self.assertEqual(raw['data/'+role.replace(':', '-')+'.json'], capacity(role))
        with self.assertRaises(AssertionError): layout({'huge.py': M+1}, {}, 100)
        with self.assertRaises(AssertionError): layout({'a.py': 10}, {'huge': M+1}, 100)
        with self.assertRaises(AssertionError): layout({'a.py': 10}, {}, 65537)

    def test_pretty_registration_is_not_reserved_as_compact_json(self):
        value = {'pins': {'source/'+str(i): 'a'*64 for i in range(20)}}
        compact = len(json.dumps(value, separators=(',', ':')).encode())
        pretty = len((json.dumps(value, indent=2)+'\n').replace('\n', '\r\n').encode())
        self.assertGreater(pretty, compact)
        self.assertLessEqual(pretty, registration_capacity(compact))
        with self.assertRaises(AssertionError): registration_capacity(32769)


if __name__ == '__main__':
    unittest.main()
