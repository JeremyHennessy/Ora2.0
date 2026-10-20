"""Full host protocol transcript with synthetic peer; NOT a native G/W/C run.

AST-extract production Client to avoid importing or starting any Ora worlds.
Exercise all 26 exchanges, framing refusal and failure progression.
"""
import ast
import io
import json
from pathlib import Path
import struct
from types import SimpleNamespace
import unittest

SOURCE = Path(__file__).resolve().parents[1] / 'experiments/digital_pilot74_guardian_v1.py'
node = next(n for n in ast.parse(SOURCE.read_bytes()).body if isinstance(n, ast.ClassDef) and n.name == 'Client')
encode = lambda v: json.dumps(v, separators=(',', ':'), sort_keys=True).encode()
ns = dict(struct=struct, enc=encode, FRAME=65536, MIB=1024**2)
exec(compile(ast.Module(body=[node], type_ignores=[]), str(SOURCE), 'exec'), ns)
Client = ns['Client']


class Protocol(unittest.TestCase):
    def client(self):
        c = object.__new__(Client)
        c.r = dict(source_sha256='a'*64, configuration_sha256='b'*64)
        c.ordinal = 0; c.is_ready = True; c.archiving = False; c.finished = False; c.results = {}
        c.writer = io.BytesIO()
        return c

    def response(self, c, value):
        raw = encode(value)
        c.reader = io.BytesIO(struct.pack('<I', len(raw)) + raw)

    def test_all_26_roles_barrier_and_finish(self):
        c = self.client()
        wire = dict(source_sha256='a'*64, configuration_sha256='b'*64)
        physical = SimpleNamespace(external=lambda spec, cap: b'output' if spec == 'raw' else encode(wire),
                                   parse=lambda raw, cap: json.loads(raw))
        ns['physical'] = physical
        ns['normalize_native'] = lambda w: dict(stdout_capture=dict(grant_sha256='seal', raw='raw'))
        limits = SimpleNamespace(memory_bytes=1024**3, cpu_seconds=180, processes=3, wall_seconds=300)
        for ordinal in range(26):
            role = 'role-' + str(ordinal)
            command = ['fixture', role]
            wire.update(role=role, command=command)
            self.response(c, dict(schema='PILOT74-GUARDIAN-ROLE-RESULT-v1', ordinal=ordinal, role=role, native={}))
            c.run(command, limits, '.', capture_grant={}, capture_seal='seal',
                  source_sha256='a'*64, configuration_sha256='b'*64, role=role, request={})
        self.assertEqual(c.ordinal, 26)
        self.response(c, dict(schema='PILOT74-GUARDIAN-BARRIER-v1'))
        c.barrier(True)
        self.response(c, dict(schema='PILOT74-GUARDIAN-FINISH-v1'))
        c.finish(dict(evidence_complete=True))
        end = c.writer.tell()
        c.finish(dict(evidence_complete=True))
        self.assertEqual(c.writer.tell(), end)
        self.assertTrue(c.finished)

    def test_incomplete_run_cannot_request_success_barrier(self):
        c = self.client()
        with self.assertRaises(AssertionError):
            c.barrier(True)
        self.assertEqual(c.writer.getvalue(), b'')

    def test_bad_evidence_does_not_advance_role(self):
        c = self.client()
        self.response(c, dict(schema='PILOT74-GUARDIAN-ROLE-RESULT-v1', ordinal=0, role='r', native={}))
        ns['physical'] = SimpleNamespace(parse=lambda raw, cap: json.loads(raw),
                                        external=lambda *a: (_ for _ in ()).throw(ValueError('bad digest')))
        limits = SimpleNamespace(memory_bytes=1024**3, cpu_seconds=180, processes=3, wall_seconds=300)
        with self.assertRaises(ValueError):
            c.run(['fixture'], limits, '.', capture_grant={}, capture_seal='s',
                  source_sha256='a'*64, configuration_sha256='b'*64, role='r', request={})
        self.assertEqual(c.ordinal, 0)

    def test_truncated_oversize_and_native_failure_frames(self):
        for raw in (b'', b'xx', struct.pack('<I', 65537), struct.pack('<I', 4) + b'{}'):
            c = self.client(); c.reader = io.BytesIO(raw)
            with self.assertRaises((OSError, AssertionError)):
                c.exchange('HELLO')
        c = self.client()
        ns['physical'] = SimpleNamespace(parse=lambda raw, cap: json.loads(raw))
        self.response(c, dict(schema='PILOT74-GUARDIAN-FIRST-FAILURE-v1'))
        with self.assertRaises(RuntimeError):
            c.exchange('HELLO')


if __name__ == '__main__':
    unittest.main()
