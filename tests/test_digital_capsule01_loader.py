"""Prepared negative boundaries only; no World construction or resource query."""
import ast
import hashlib
import json
import unittest
from pathlib import Path
from unittest.mock import patch
from experiments import digital_capsule01_data as data
from experiments import digital_capsule01_loader as loader
from experiments import digital_capsule01_referee as referee
from test_digital_capsule01_data import IDENTITY, packet, prepared


class LoaderPrepared(unittest.TestCase):
    def test_numeric_map_wire_hash_regression(self):
        original=prepared()
        normalized=data.validate_state(original)
        self.assertNotEqual(data.digest(normalized),data.digest(original))
        wire=json.loads(json.dumps(normalized))
        self.assertEqual(data.digest(wire),data.digest(original))

    def test_independent_checker_never_uses_boundary_or_world(self):
        tree=ast.parse(Path(referee.__file__).read_text())
        imports=[alias.name for n in ast.walk(tree) if isinstance(n,ast.Import) for alias in n.names]
        self.assertEqual(imports,['hashlib','json'])
        self.assertFalse(any(isinstance(n,ast.ImportFrom) for n in ast.walk(tree)))
        self.assertFalse(any(isinstance(n,ast.Attribute) and n.attr in ('hydrate','decode_prepared','step','restore') for n in ast.walk(tree)))

    def test_custody_refusal_before_any_literal_history(self):
        raw,sha=packet()
        with patch.object(referee,'audit_state',side_effect=AssertionError('history reached')):
            for bad,extent in [(raw[:-1],len(raw)),(raw+b'x',len(raw))]:
                with self.assertRaises(AssertionError):
                    referee.verify_capsule(bad,IDENTITY,sha,extent)

    def test_independent_duplicate_refusal(self):
        raw,_=packet();bad=raw.replace(b'"tick":0',b'"tick":0,"tick":0')
        with patch.object(referee,'audit_state',side_effect=RuntimeError('history reached')):
            with self.assertRaises(AssertionError):
                referee.verify_capsule(bad,IDENTITY,hashlib.sha256(bad).hexdigest(),len(bad))

    def test_wrong_source_refused_even_when_data_boundary_is_corrupt(self):
        raw,sha=packet();wrong=dict(IDENTITY,revision='d'*40)
        with patch.object(data,'decode_prepared',return_value=prepared()), patch.object(referee,'audit_state',side_effect=RuntimeError('history reached')):
            with self.assertRaises(AssertionError):
                referee.verify_capsule(raw,wrong,sha,len(raw))

    def test_loader_requires_externally_pinned_receipt_before_boundary(self):
        raw,sha=packet()
        with patch.object(data,'decode_prepared',side_effect=AssertionError('decode reached')):
            with self.assertRaises(ValueError):
                loader.hydrate(raw,IDENTITY,sha,{'verified':True},'0'*64)

    def test_loader_refuses_self_claimed_verified_flag(self):
        raw,sha=packet();audit={'verified':True}
        with patch.object(loader.kernel.World,'__new__',side_effect=AssertionError('World reached')):
            with self.assertRaises(ValueError):
                loader.hydrate(raw,IDENTITY,sha,audit,data.digest(audit))

    def test_frozen_cuts_scope_and_byte_binding(self):
        raw,sha=packet()
        audit=dict(version='DIGITAL-CAPSULE01-AUDIT-v1',verified=True,identity=IDENTITY,
                   capsule_sha256=sha,extent=len(raw),state_sha256=data.digest(prepared()),tick=0,
                   audit_prefix_instructions=0,summary={},engineering_only=True,stage_credit=False)
        with patch.object(data,'decode_prepared',side_effect=AssertionError('decode reached')):
            with self.assertRaises(ValueError):
                loader.hydrate(raw,IDENTITY,sha,audit,data.digest(audit))
            for changed in [dict(audit,tick=True),dict(audit,tick=64,audit_prefix_instructions=True),dict(audit,tick=64,audit_prefix_instructions=64,extent=len(raw)+1)]:
                with self.assertRaises(ValueError):
                    loader.hydrate(raw,IDENTITY,sha,changed,data.digest(changed))

    def test_floats_and_boolean_seed_refused_without_resource_hash(self):
        for changed in [dict(prepared(),seed=True),dict(prepared(),tick=0.0),dict(prepared(),seed=2)]:
            with patch.object(referee,'h',side_effect=RuntimeError('hash query reached')):
                with self.assertRaises(AssertionError):
                    referee.audit_state(changed)

    def test_candidate_loader_has_no_prefix_replay_calls(self):
        tree=ast.parse(Path(loader.__file__).read_text())
        self.assertFalse(any(isinstance(n,ast.Attribute) and n.attr in ('step','restore','run','audit_state','verify_capsule','__init__') for n in ast.walk(tree)))


if __name__=='__main__':unittest.main()
