"""Disclosed in-memory controller IO; no native scientific endpoint or World."""
import copy
import unittest
from experiments import digital_pressure71_controller as controller
from experiments.digital_pressure71_admission import digest, SEEDS
from experiments.digital_pressure71_runplan import schedule
from tests.test_digital_pressure71_measure import fixture, PROVENANCE
from tests.test_digital_pressure71_runner_boundaries import summary


class PreparedIO:
    def __init__(self, defect=None):
        self.defect = defect; self.calls = []; self.records = {}; self.failure = None
        self.admission = None; self.read_calls = []; self.checked = 0; self.raw = {}

    def source_check(self):
        self.checked += 1
        if self.defect == 'source' and len(self.calls) == 34: raise AssertionError('prepared changed source')

    def precharge(self, plan, amount):
        assert not self.calls and plan == schedule() and amount == 14976 * 1024**2
        self.precharged = True

    def prepared(self, export):
        assert self.precharged; self.calls.append(dict(export=export, role='prepared', endpoint='prepared', treatment=False))

    def endpoint(self, export, role, endpoint, input_spec, admission_spec):
        treatment = role['kind'] == 'fork' or role.get('mode') == 'mutating'
        assert self.precharged
        if treatment:
            assert self.admission is not None and admission_spec is not None
            assert len(self.calls) >= 34
        self.calls.append(dict(export=export, role=role['name'], endpoint=endpoint, treatment=treatment))
        if self.defect == 'native' and treatment: raise AssertionError('prepared endpoint failure')
        if endpoint == 'raw':
            if role['kind'] == 'fork': assert input_spec == self.raw[(export, role['natural_role'])]
            artifact = dict(path=f'/prepared/{export}/{role["name"]}/raw', sha256=digest(role), extent=100)
            if self.defect == 'copy' and export == 'restored': artifact['sha256'] = 'f' * 64
            self.raw[(export, role['name'])] = artifact
            return artifact, None
        assert input_spec == self.raw[(export, role['name'])]
        if role['kind'] == 'population' and role['mode'] == 'faithful':
            s = summary(role['seed'])
            if self.defect == 'gate': s['turnover']['living_descendants'] = 0
            value = dict(verified=True, stage_credit=False, provenance=PROVENANCE, summary=s,
                         natural_history_hash='c' * 64)
        else:
            proofs, context = fixture()
            for p in proofs:
                p['seed'] = role['seed']; p['summary'].update(seed=role['seed'], dose=role['dose'])
            if role['kind'] == 'population':
                s = proofs[0]['summary']
                s.update(mode=role['mode'], inheritance_mode=role['inheritance_mode'], renewed_food=10)
                value = dict(verified=True, stage_credit=False, provenance=PROVENANCE,
                             summary=s, natural_history_hash=context['natural_history_hash'])
            else:
                value = next(p for p in proofs if p['slot_kind'] == role['slot_kind'] and p['role'] == role['fork_role'])
                if self.defect == 'censor': value['target']['censored'] = True
                if self.defect == 'dose': value['summary']['dose'] = 8 if role['dose'] == 1 else 1
        artifact = dict(path=f'/prepared/{export}/{role["name"]}/proof', sha256=digest(value), extent=1000)
        if self.defect == 'hash' and treatment: artifact['sha256'] = 'f' * 64
        return artifact, value

    def persist_admission(self, value):
        assert len(self.calls) == 34 and not any(c['treatment'] for c in self.calls)
        self.admission = copy.deepcopy(value)
        return dict(path='/prepared/admission', sha256=digest(value), extent=1000)

    def read_admission(self, spec):
        self.read_calls.append(len(self.calls)); value = copy.deepcopy(self.admission)
        if self.defect == 'durable' and len(self.read_calls) > 1: value['treatment_worlds'] = 1
        return value

    def record(self, name, value): self.records[name] = copy.deepcopy(value)
    def failed(self, value): self.failure = value


class ControllerTests(unittest.TestCase):
    def test_full418_order_reference_receipts_and_unscreened_panel(self):
        io = PreparedIO(); result = controller.drive(io, PROVENANCE)
        self.assertEqual(io.calls, schedule())
        self.assertEqual(result['native_calls'], 418); self.assertEqual(result['treatment_calls'], 384)
        self.assertEqual(len(result['admission']['reference_receipts']), 16)
        self.assertEqual(len(io.read_calls), 385); self.assertEqual(io.read_calls[:2], [34, 34])
        self.assertEqual(len(io.records['comparison']['families']), 16)
        self.assertEqual(result['comparison']['replicated_selection'], {1: True, 8: True})
        self.assertFalse(result['scientific_acceptance']); self.assertFalse(result['stage_credit'])
        self.assertIsNone(io.failure)

    def test_all16_failed_gates_saved_before_zero_treatment_stop(self):
        io = PreparedIO('gate')
        with self.assertRaises(AssertionError): controller.drive(io, PROVENANCE)
        self.assertEqual(len(io.calls), 34)
        self.assertFalse(io.admission['all_paid_gates'])
        self.assertEqual(io.failure['attempted_treatment_calls'], 0)
        self.assertEqual(len(io.records['ordinary-gates']['references']['original']), 8)
        self.assertEqual(len(io.records['ordinary-gates']['references']['restored']), 8)

    def test_unequal_raw_copy_refuses_before_treatment(self):
        io = PreparedIO('copy')
        with self.assertRaises(AssertionError): controller.drive(io, PROVENANCE)
        self.assertFalse(io.admission['original_restored_equal']); self.assertEqual(len(io.calls), 34)

    def test_durable_changed_receipt_refuses_before_first_treatment(self):
        io = PreparedIO('durable')
        with self.assertRaises(AssertionError): controller.drive(io, PROVENANCE)
        self.assertEqual(len(io.calls), 34); self.assertEqual(io.failure['attempted_treatment_calls'], 0)

    def test_failed_native_not_retried_attempt_and_partials_preserved(self):
        io = PreparedIO('native')
        with self.assertRaises(AssertionError): controller.drive(io, PROVENANCE)
        self.assertEqual(len(io.calls), 35); self.assertEqual(io.failure['attempted_native_calls'], 35)
        self.assertEqual(io.failure['attempted_treatment_calls'], 1)
        self.assertEqual(io.failure['recorded_raw'], 16)

    def test_proof_file_hash_mismatch_stops_after_single_pair(self):
        io = PreparedIO('hash')
        with self.assertRaises(AssertionError): controller.drive(io, PROVENANCE)
        self.assertEqual(len(io.calls), 36); self.assertEqual(io.failure['recorded_proofs'], 16)

    def test_source_change_stops_at34_without_durable_authority(self):
        io = PreparedIO('source')
        with self.assertRaises(AssertionError): controller.drive(io, PROVENANCE)
        self.assertEqual(len(io.calls), 34); self.assertIsNone(io.admission)

    def test_wrong_fork_dose_cannot_pass_family_measurement(self):
        io = PreparedIO('dose')
        with self.assertRaises(AssertionError): controller.drive(io, PROVENANCE)
        self.assertEqual(len(io.calls), 164)
        self.assertNotIn('comparison', io.records)

    def test_censored_all_families_retained_as_negative(self):
        io = PreparedIO('censor'); result = controller.drive(io, PROVENANCE)
        self.assertEqual(len(io.records['comparison']['families']), 16)
        self.assertEqual(result['comparison']['replicated_selection'], {1: False, 8: False})
        self.assertFalse(result['comparison']['pressure_alleviation'])


if __name__ == '__main__': unittest.main()
