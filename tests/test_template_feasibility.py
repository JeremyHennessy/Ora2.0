import copy
import tempfile
from pathlib import Path
import unittest

from experiments import template_feasibility as worker
from experiments import template_feasibility_audit as audit


class TemplateFeasibilityTests(unittest.TestCase):
    def test_complete_all_sequence_case_panel_and_independent_audit(self):
        cases = list(worker.cases())
        specs = list(audit.expected_specs())
        self.assertEqual(len(cases), 392)
        for record, spec in zip(cases, specs):
            with self.subTest(bits=record['bits'], mode=record['mode'], case=record['label']):
                audit.verify(record, spec)

    def test_paid_parent_child_coupling_exposes_full_cost(self):
        r = next(r for r in worker.cases() if r['bits'] == '010' and r['mode'] == 'active' and r['label'] == 'generations')
        copies = [e['result'] for e in r['events'] if e['result']['outcome'] == 'copied']
        self.assertEqual([e['charged'] for e in copies], [10, 10])
        self.assertEqual([e['heat'] for e in copies], [6, 6])
        self.assertEqual([e['endowment'] for e in copies], [2, 2])
        self.assertEqual([r['terminal']['objects'][p]['work'] for p in ('p0', 'p1', 'p2')], [0, 0, 2])
        self.assertTrue(set(r['terminal']['objects']['p0']['atoms']).isdisjoint(r['terminal']['objects']['p1']['atoms']))

    def test_starvation_missing_material_and_recycling(self):
        for r in worker.cases():
            if r['label'] in ('wrong-feed', 'missing-feed', 'insufficient-feed', 'contact-budget-0', 'contact-budget-1', 'nonmatching-food'):
                self.assertFalse(any(e['result']['outcome'] in ('copied', 'converted') for e in r['events']))
            if r['label'] == 'regeneration':
                self.assertEqual(r['terminal']['history']['p1']['atoms'], r['terminal']['history']['p2']['atoms'])
                self.assertNotIn('p1', r['terminal']['objects'])

    def test_rehashed_cost_parent_and_bit_forgeries_fail(self):
        record = next(worker.cases())
        spec = next(audit.expected_specs())
        for field in ('cost', 'parent', 'bit', 'duplicate'):
            r = copy.deepcopy(record)
            if field == 'cost':
                r['events'][0]['result']['charged'] += 1
            elif field == 'parent':
                r['terminal']['history']['p1']['template_parent'] = 'fake'
            elif field == 'bit':
                r['initial']['atoms']['a000']['bit'] = '1'
            else:
                r['terminal']['ready'].append('a000')
            with self.subTest(field=field), self.assertRaises(ValueError):
                audit.verify(r, spec)

    def test_source_bound_read_only_audit(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp)/'authored'
            worker.run(output, 'a'*40)
            before = {p.name: p.read_bytes() for p in output.iterdir()}
            report = audit.audit(output, 'a'*40)
            self.assertTrue(report['feasibility_passed'])
            self.assertEqual(report['independent_natural_initializations'], 0)
            self.assertEqual(before, {p.name: p.read_bytes() for p in output.iterdir()})
            with self.assertRaises(ValueError):
                audit.audit(output, 'b'*40)


if __name__ == '__main__':
    unittest.main()
