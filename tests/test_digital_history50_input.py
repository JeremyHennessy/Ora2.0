"""Synthetic custody refusals; no original traces, World or new organisms."""
import copy
import unittest
from experiments import digital_history50_input as guard


def fixture(chunk=0):
    identities=[]; histories=[]
    for role in guard.roles(chunk):
        ancestry={'sample_id': int(role[9:]), 'parent': {'complete': [1, 2]}} if role.startswith('candidate') else None
        row=dict(seed=44200, control_mode='intact', experiment=guard.CONTRACT,
                 genesis_program=[[18, 0, 0]], synthetic_payload=role)
        histories.append(dict(role=role, ancestry=ancestry, row=row, source_descriptor_is_static=True))
        identities.append(dict(role=role, ancestry=copy.deepcopy(ancestry), program=row['genesis_program'], input_sha256=guard.digest(row)))
    return (dict(contract=guard.CONTRACT, chunk=chunk, seed=44200, control='intact', histories=histories),
            dict(chunk=chunk, seed=44200, control='intact', histories=identities))


class ClosedInputTests(unittest.TestCase):
    def test_complete_membership_and_both_slices(self):
        batch, expected=fixture()
        self.assertEqual([x['role'] for x in guard.authenticate(batch, expected, 0)], guard.roles(0)[:4])
        self.assertEqual([x['role'] for x in guard.authenticate(batch, expected, 4)], guard.roles(0)[4:])

    def test_changed_unselected_row_refused(self):
        batch, expected=fixture(); batch['histories'][7]['row']['synthetic_payload']='changed'
        with self.assertRaisesRegex(ValueError, 'row hash'): guard.authenticate(batch, expected, 0)

    def test_missing_member_refused(self):
        batch, expected=fixture(); batch['histories'].pop()
        with self.assertRaisesRegex(ValueError, 'membership'): guard.authenticate(batch, expected, 0)

    def test_permuted_member_refused(self):
        batch, expected=fixture(); batch['histories'].reverse()
        with self.assertRaisesRegex(ValueError, 'membership'): guard.authenticate(batch, expected, 0)

    def test_nested_ancestry_change_refused(self):
        batch, expected=fixture(); batch['histories'][3]['ancestry']['parent']['complete'].pop()
        with self.assertRaisesRegex(ValueError, 'ancestry'): guard.authenticate(batch, expected, 0)

    def test_boolean_ancestry_alias_refused(self):
        batch, expected=fixture(); batch['histories'][1]['ancestry']['sample_id']=True
        with self.assertRaisesRegex(ValueError, 'ancestry'): guard.authenticate(batch, expected, 0)

    def test_metadata_and_boolean_refused(self):
        for key, value in [('seed', True), ('chunk', False), ('control', 'retained_disabled'), ('contract', 'other')]:
            batch, expected=fixture(); batch[key]=value
            with self.assertRaisesRegex(ValueError, 'metadata'): guard.authenticate(batch, expected, 0)

    def test_source_program_join_refused_even_with_matching_row_hash(self):
        batch, expected=fixture(); batch['histories'][0]['row']['genesis_program']=[[18, 1, 0]]
        expected['histories'][0]['input_sha256']=guard.digest(batch['histories'][0]['row'])
        with self.assertRaisesRegex(ValueError, 'Row source'): guard.authenticate(batch, expected, 0)

    def test_static_disclosure_required(self):
        batch, expected=fixture(); batch['histories'][0]['source_descriptor_is_static']=False
        with self.assertRaisesRegex(ValueError, 'disclosure'): guard.authenticate(batch, expected, 0)

    def test_short_reference_chunk_and_invalid_slice(self):
        batch, expected=fixture(33)
        self.assertEqual(len(guard.authenticate(batch, expected, 0)), 3)
        for offset in (4, True, -1, 1):
            with self.assertRaisesRegex(ValueError, 'slice'): guard.authenticate(batch, expected, offset)


if __name__ == '__main__':
    unittest.main()
