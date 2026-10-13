"""Synthetic data only: no natural ancestry, VM construction or resume proof."""
import ast
import copy
import hashlib
import unittest
from pathlib import Path
from unittest.mock import patch
from experiments import digital_capsule01_data as data


def prepared():
    # Structurally consistent invented values; deliberately NOT a natural genome
    # or a resource-hash query. The missing semantic referee must reject its claim
    # to executed ancestry before any loader could accept it as resume authority.
    body = dict(id=0, parent=None, generation=0, code=[[0, i] for i in range(27)],
                state_units=list(range(27, 43)), memory=[0]*8, registers=[0, 0],
                pc=0, cue=0, feedback=0, inbox=None, pos=0, energy=12, nursery=[])
    return dict(inheritance_mode='parent_copy', fuel_mode='renewed', turns={'0': 0},
                offered=0, admitted=0, rejected=0, next_packet=64, seed=1,
                mode='faithful', tick=0, last=-1, next_id=1, writes=0,
                constructor_remaining=85, heat=43,
                formation=[dict(unit=i, value=0, energy=1, assistance='supplied ancestor assembly') for i in range(43)],
                food={str(i): [0 if i < 32 else 1+(i-32)//16, 0] for i in range(64)},
                free=list(range(43, 512)), entities={'0': body}, events=[],
                births=0, deaths=0, maximum=1)


IDENTITY = dict(revision='a'*40, source_sha256='b'*64, config_sha256='c'*64,
                law='DIGITAL-SHARED-LINEAGE-68-v1')


def packet(state=None):
    state = prepared() if state is None else state
    raw = data.canonical(dict(version=data.VERSION, identity=IDENTITY, state=state,
                              state_sha256=data.digest(state)))
    return raw, hashlib.sha256(raw).hexdigest()


class PreparedBoundary(unittest.TestCase):
    def reject_state(self, edit):
        state = prepared(); edit(state)
        raw, sha = packet(state)
        with self.assertRaises(ValueError):
            data.decode_prepared(raw, IDENTITY, sha, 100000)

    def test_normalizes_three_maps_without_mutating_source(self):
        state = prepared(); before = copy.deepcopy(state)
        raw, sha = packet(state)
        result = data.decode_prepared(raw, IDENTITY, sha, 100000)
        self.assertEqual(state, before)
        for name in ('turns', 'entities', 'food'):
            self.assertTrue(all(type(key) is int for key in result[name]))
        self.assertEqual(result['entities'][0]['code'], state['entities']['0']['code'])

    def test_bad_custody_refused_before_json_decode(self):
        raw, sha = packet()
        with patch.object(data.json, 'loads', side_effect=AssertionError('decode reached')):
            for bad, cap in [(raw+b'x', 100000), (raw[:-1], 100000), (raw, len(raw)-1)]:
                with self.assertRaises(ValueError):
                    data.decode_prepared(bad, IDENTITY, sha, cap)

    def test_duplicate_and_noncanonical_json(self):
        raw, _ = packet()
        for bad in [raw.replace(b'"tick":0', b'"tick":0,"tick":0'), raw+b'\n']:
            with self.assertRaises(ValueError):
                data.decode_prepared(bad, IDENTITY, hashlib.sha256(bad).hexdigest(), 100000)

    def test_source_configuration_version_and_state_hash(self):
        raw, sha = packet()
        for key in ('revision', 'source_sha256', 'config_sha256'):
            wrong = dict(IDENTITY); wrong[key] = 'd'*len(wrong[key])
            with self.assertRaises(ValueError):
                data.decode_prepared(raw, wrong, sha, 100000)
        for old, new in [(data.VERSION.encode(), b'wrong'), (data.digest(prepared()).encode(), b'f'*64)]:
            bad = raw.replace(old, new)
            with self.assertRaises(ValueError):
                data.decode_prepared(bad, IDENTITY, hashlib.sha256(bad).hexdigest(), 100000)

    def test_missing_extra_and_ambiguous_map_ids(self):
        self.reject_state(lambda s: s.pop('last'))
        self.reject_state(lambda s: s.update(host_command='anything'))
        for bad in ('00', '+0', '\u0660', '-0', '1.0'):
            self.reject_state(lambda s, bad=bad: s['turns'].update({bad: s['turns'].pop('0')}))
        with self.assertRaises(ValueError):
            data.validate_state(dict(prepared(), turns={0: 0}))

    def test_boolean_numeric_fields(self):
        for key in ('tick', 'last', 'seed', 'writes', 'heat', 'births', 'maximum'):
            self.reject_state(lambda s, key=key: s.update({key: False}))
        for key in ('id', 'generation', 'pc', 'cue', 'feedback', 'pos', 'energy'):
            self.reject_state(lambda s, key=key: s['entities']['0'].update({key: False}))
        self.reject_state(lambda s: s['entities']['0']['registers'].__setitem__(0, False))

    def test_material_and_energy_resource_ledger(self):
        self.reject_state(lambda s: s['free'].__setitem__(0, 42))
        self.reject_state(lambda s: s['entities']['0']['code'][0].__setitem__(1, 1))
        self.reject_state(lambda s: s.update(heat=44))
        self.reject_state(lambda s: s.update(offered=1, rejected=1, next_packet=65))
        self.reject_state(lambda s: s['food'].update({'64': [0, 0]}))
        self.reject_state(lambda s: s['food']['32'].__setitem__(0, 0))

    def test_turn_scheduler_and_history_extent(self):
        self.reject_state(lambda s: s.update(last=0))
        self.reject_state(lambda s: s['turns'].update({'0': 1}))
        self.reject_state(lambda s: s.update(events=[dict(tick=1, actor=0)]))
        # A dead scheduler ID is structurally legal; requiring a live last actor
        # would incorrectly reject a real post-expiry checkpoint.
        state = prepared(); state.update(tick=1, last=0, heat=55, deaths=1,
                                          entities={}, free=list(range(512)), turns={'0': 1})
        state['events'] = [dict(tick=1, actor=0, state_hash=data.digest({k: v for k, v in state.items() if k != 'events'}))]
        self.assertEqual(data.validate_state(state)['last'], 0)

    def test_program_channel_and_nursery_shapes(self):
        self.reject_state(lambda s: s['entities']['0']['code'][0].__setitem__(0, 'print(1)'))
        self.reject_state(lambda s: s['entities']['0'].update(inbox=True))
        self.reject_state(lambda s: s['entities']['0'].update(nursery=[{}]))
        self.reject_state(lambda s: s['entities']['0'].update(memory=[0]*7))

    def test_boundary_has_no_world_hydration_or_execution(self):
        tree = ast.parse(Path(data.__file__).read_text())
        imports = [node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]
        self.assertEqual([node.names[0].name for node in imports], ['hashlib', 'json'])
        self.assertFalse(any(isinstance(node, ast.Attribute) and node.attr in ('step', 'restore', '__dict__') for node in ast.walk(tree)))
        self.assertFalse(hasattr(data, 'load_world'))


if __name__ == '__main__':
    unittest.main()
