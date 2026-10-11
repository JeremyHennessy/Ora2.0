"""Bounded software fixtures: typed evidence, never scientific populations."""
import copy
import unittest
from experiments.digital_memory_task import Task
from experiments.digital_memory_task_audit import audit, h
from experiments.digital_memory_binding import measure
from experiments.digital_memory_binding_audit import audit as binding_audit
from experiments.digital_ecosystem02 import World
from experiments.digital_route02 import World as RouteWorld


class ReceiptTypesTests(unittest.TestCase):
    def task_record(self):
        task = Task(0)
        task.step('sense')
        return task.record()

    def test_genuine_boolean_alive_and_integer_receipts_pass(self):
        self.assertTrue(audit(self.task_record())['verified'])
        self.assertTrue(binding_audit(measure([[4,0,0],[6,0,0],[7,0,0]],0))['verified'])

    def test_numeric_task_fields_reject_boolean_and_float_lookalikes(self):
        for field in ('tick','out'):
            for replacement in (False,0.0):
                with self.subTest(field=field,replacement=replacement):
                    row=self.task_record();row['events'][0][field]=replacement
                    with self.assertRaises(AssertionError):audit(row)

    def test_alive_rejects_numeric_even_with_rehashed_final(self):
        for section in ('event','final'):
            row=self.task_record()
            if section=='event':row['events'][0]['alive']=1
            else:
                row['final']['alive']=1;row['state_hash']=h(row['final'])
            with self.subTest(section=section),self.assertRaises(AssertionError):audit(row)

    def test_binding_formation_and_events_reject_numeric_lookalikes(self):
        genuine=measure([[4,0,0],[6,0,0],[7,0,0]],0)
        for section,field,replacements in (('formation','energy',(True,1.0)),('events','tick',(False,0.0))):
            for replacement in replacements:
                row=copy.deepcopy(genuine);row[section][0][field]=replacement
                with self.subTest(section=section,replacement=replacement),self.assertRaises(AssertionError):binding_audit(row)

    def test_restore_preserves_valid_checkpoint_and_rejects_numeric_lookalikes(self):
        for cls in (World,RouteWorld):
            world=cls(0,'faithful');world.step();state=world.snapshot()
            self.assertEqual(cls.restore(state).snapshot(),state)
            for replacement in (True,1.0):
                bad=copy.deepcopy(state);bad['formation'][0]['energy']=replacement
                with self.subTest(cls=cls.__name__,replacement=replacement),self.assertRaises(AssertionError):cls.restore(bad)


if __name__=='__main__':unittest.main()
