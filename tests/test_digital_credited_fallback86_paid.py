"""Finite scope/precharge checks only; no World or target is constructed."""
import copy
import json
import unittest
import ast
from pathlib import Path
from experiments.digital_credited_fallback86_paid_child import CONFIG, scope
from experiments.digital_credited_fallback86_paid_plan import ROLES, capacity, layout, registration_capacity, recording_bound, admit_ci, M


class PaidCustody(unittest.TestCase):
    def test_exact_ci_also_binds_clean_worktree(self):
        good=dict(passed=True,conclusion='success',source_head='a'*40)
        admit_ci(good,'a'*40,'')
        for receipt,head,status in ((good,'a'*40,' M worker.py'),(good,'b'*40,''),
            (dict(good,conclusion=None),'a'*40,''),(dict(good,passed=1),'a'*40,'')):
            with self.assertRaises(AssertionError):admit_ci(receipt,head,status)

    def base(self):
        return dict(configuration=copy.deepcopy(CONFIG), source_files={}, source_sha='',
                    config_sha='', role='original:2100080:generate', kind='generate', input=None,
                    grant={}, seal='')

    def test_exact_scopes_and_no_foreign_case(self):
        self.assertEqual(scope(self.base()), 'generate')
        for field, value in [('role', 'original:1009400:generate'), ('kind', 'audit')]:
            request = self.base(); request[field] = value
            with self.assertRaises(AssertionError): scope(request)
        for field, value in [('horizon', 64), ('seeds', [1009300]), ('software_only', 1),
                             ('cases', [[8, 'model']])]:
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
        self.assertEqual(len([n for n in raw if n.startswith('native/')]), 16)
        for role in ROLES:
            self.assertEqual(raw['data/'+role.replace(':', '-')+'.json'], capacity(role))
        with self.assertRaises(AssertionError): layout({'huge.py': M+1}, {}, 100)
        with self.assertRaises(AssertionError): layout({'a.py': 10}, {'huge': M+1}, 100)
        with self.assertRaises(AssertionError): layout({'a.py': 10}, {}, 65537)

    def test_nine_history_input_allowance_and_role_dependencies(self):
        self.assertEqual(recording_bound(),7512064)
        self.assertLess(recording_bound(),8*M)
        self.assertEqual(len(ROLES),12)
        for i,seed in enumerate(CONFIG['seeds']):
            self.assertEqual(ROLES[3*i:3*i+3],(f'original:{seed}:generate',f'original:{seed}:audit',f'restored:{seed}:generate'))
            for role in ROLES[3*i:3*i+3]:
                req=self.base();req['role']=role;req['kind']=role.split(':')[-1];req['input']={} if req['kind']=='audit' else None
                self.assertEqual(scope(req),req['kind'])

    def test_controller_pins_per_seed_parity_and_fail_stop(self):
        text=(Path(__file__).parents[1]/'lab/run_credited_fallback86_paid_v1.py').read_text()
        tree=ast.parse(text)
        self.assertFalse(any(isinstance(n,ast.ImportFrom) and n.module in
            ('experiments.digital_memory80','experiments.digital_memory80_referee') for n in ast.walk(tree)))
        # Guard against silently pairing the fourth source export with the first
        # fixture, or counting one nine-source bundle as two old diagnostic cases.
        self.assertIn("inputs=original[seed] if kind=='audit' else None",text)
        self.assertIn("oralab.sha(path)==original[seed]['sha256']",text)
        self.assertIn("completed_software_geneses=9*sum",text)
        self.assertIn("assert calls==16 and negatives==4 and len(summary)==4",text)
        worker=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='worker')
        self.assertTrue(any(isinstance(n,ast.Try) and n.handlers and n.finalbody for n in ast.walk(worker)))

    def test_pretty_registration_is_not_reserved_as_compact_json(self):
        value = {'pins': {'source/'+str(i): 'a'*64 for i in range(20)}}
        compact = len(json.dumps(value, separators=(',', ':')).encode())
        pretty = len((json.dumps(value, indent=2)+'\n').replace('\n', '\r\n').encode())
        self.assertGreater(pretty, compact)
        self.assertLessEqual(pretty, registration_capacity(compact))
        with self.assertRaises(AssertionError): registration_capacity(32769)


if __name__ == '__main__':
    unittest.main()
