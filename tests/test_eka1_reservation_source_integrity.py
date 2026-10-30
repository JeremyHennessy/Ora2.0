"""Current owner/ledger source-origin checks; historical nine-check receipts retained.

The execution tests now live in test_eka1_native_owner_candidate, because both
entrypoints require the physical owner introduced after accepted head06c5659.
"""
import ast
import hashlib
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
from test_eka1_native_owner_candidate import wrapper_scope,ROOT,native,budget

class ReservationSourceChecks(unittest.TestCase):
    def test_both_ledger_and_owner_pins_are_exact(self):
        for derived in (False,True):
            scope,target=wrapper_scope(derived)
            pins=scope['SOURCE_PINS' if derived else 'INPUT_PINS']
            for name in ('tools/eka1_cumulative_reservations.py','tools/eka1_native_owner_candidate.py'):
                self.assertEqual(pins[name],hashlib.sha256((ROOT/name).read_bytes()).hexdigest())
            self.assertIs(scope['reservation_class'](),budget.Reservations)
            self.assertIs(scope['owner_class'](),native.NativeOwnerCandidate)
    def test_changed_ledger_bytes_refused(self):
        for d in (False,True):
            scope,target=wrapper_scope(d)
            with patch.object(Path,'read_bytes',return_value=b'changed'):
                with self.assertRaisesRegex(ValueError,'reservation source changed'):scope['reservation_class']()
    def test_symlink_ledger_refused_without_read(self):
        for d in (False,True):
            scope,target=wrapper_scope(d)
            with patch.object(Path,'is_symlink',return_value=True),patch.object(Path,'read_bytes',side_effect=AssertionError('must reject before read')):
                with self.assertRaisesRegex(ValueError,'reservation source changed'):scope['reservation_class']()
    def test_wrong_ledger_origin_refused(self):
        for d in (False,True):
            scope,target=wrapper_scope(d)
            with patch.object(budget,'__file__',str(ROOT/'wrong.py')):
                with self.assertRaisesRegex(ValueError,'origin differs'):scope['reservation_class']()
    def test_changed_owner_bytes_refused(self):
        for d in (False,True):
            scope,target=wrapper_scope(d)
            with patch.object(Path,'read_bytes',return_value=b'changed'):
                with self.assertRaisesRegex(ValueError,'owner source changed'):scope['owner_class']()
    def test_wrong_owner_origin_refused(self):
        for d in (False,True):
            scope,target=wrapper_scope(d)
            with patch.object(native,'__file__',str(ROOT/'wrong.py')):
                with self.assertRaisesRegex(ValueError,'origin differs'):scope['owner_class']()
    def test_owner_is_required_no_default(self):
        for d in (False,True):
            scope,target=wrapper_scope(d)
            with self.assertRaisesRegex(TypeError,'owner'):scope[target](*([b'',b'',{}] if d else [b'',{}]),reservations=object(),genesis_index=0)
    def test_owner_gate_precedes_runtime_and_rejects_wrong_type(self):
        for d in (False,True):
            scope,target=wrapper_scope(d)
            with self.assertRaisesRegex(TypeError,'canonical owner'):
                scope[target](*([b'',b'',{'configuration':{}}] if d else [b'',{'configuration':{}}]),reservations=budget.Reservations.__new__(budget.Reservations),genesis_index=0,owner=object())
    def test_no_native_modules_imported(self):
        self.assertFalse(any(n.startswith('experiments.digital_') for n in sys.modules))

if __name__=='__main__':unittest.main(verbosity=2)
