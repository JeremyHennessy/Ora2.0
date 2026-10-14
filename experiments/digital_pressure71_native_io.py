"""Bounded parent endpoint IO candidate; NOT qualified or activation authority.

Caller owns the exclusive operator lock, prospectively pinned source/config,
80GiB phase accounting, source exports, failure archives and outer native job.
No World imports. Merely importing this module starts no process or experiment.
"""
import hashlib
import json
import sys
from pathlib import Path
from experiments import evidence_write_grant68 as transport
from experiments.process_limits import Limits, run
from experiments.digital_pressure71_scientific_child import read_spec, verify_source, plain
from experiments.digital_pressure71_runplan import EXPORTS, roles, schedule
from experiments.digital_pressure71_admission import digest


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False).encode('ascii')


class NativeIO:
    """Source and IO checks are necessary, never sufficient scientific admission."""
    def __init__(self, budget, exports, source_files, provenance, source_check,
                 prepared_modules, prepared_count):
        assert set(exports) == set(EXPORTS)
        assert type(prepared_modules) is list and prepared_modules
        assert all(type(name) is str and name.startswith('tests.test_digital_pressure71_') for name in prepared_modules)
        assert type(prepared_count) is int and prepared_count > 0
        self.budget = budget; self.exports = {e: Path(p) for e, p in exports.items()}
        self.source_files = dict(source_files); self.provenance = dict(provenance)
        assert digest(source_files) == provenance['source_sha256']
        self.check = source_check; self.prepared_modules = list(prepared_modules)
        self.prepared_count = prepared_count; self.grants = {}; self.native = []
        self.receipted_world_constructors = 0
        self.limits = Limits(memory_bytes=768 * 1024**2, cpu_seconds=90, wall_seconds=180, processes=3)

    def source_check(self):
        self.check()
        for path in self.exports.values():
            assert verify_source(path, self.source_files) == self.provenance['source_sha256']

    def save(self, phase, name, value):
        data = value if isinstance(value, bytes) else encoded(value)
        with self.budget.create(phase, name) as stream: stream.write(data)
        path = self.budget.root/phase/name
        return dict(path=str(path), sha256=hashlib.sha256(data).hexdigest(), extent=len(data))

    def precharge(self, plan, amount):
        assert not self.grants and not self.native and plan == schedule()
        assert amount == 14976 * 1024**2
        for export in EXPORTS:
            for role in roles():
                for endpoint, cap in (('raw', 64 * 1024**2), ('proof', 8 * 1024**2)):
                    key = (export, role['name'], endpoint)
                    self.grants[key] = transport.seal(self.budget, 'raw', 'data/' + '/'.join(key) + '.json',
                        cap, self.provenance['source_sha256'], self.provenance['configuration_sha256'], ':'.join(key))
        assert len(self.grants) == 416 and sum(g['limit'] for g, _ in self.grants.values()) == amount
        self.save('raw', 'prelaunch-grants.json', dict(items=[dict(key=list(k), grant=g, seal=s) for k, (g, s) in self.grants.items()],
                                                    ledger=self.budget.snapshot()))

    def native_check(self, receipt):
        assert receipt['exit_code'] == 0 and not receipt['timed_out'] and not receipt['output_truncated']
        assert receipt['post_close_processes_exited']
        u = receipt['usage']
        assert (u['flags'], u['configured_memory_bytes'], u['configured_cpu_ticks'],
                u['configured_processes'], u['active_before_close']) == (8716, 768 * 1024**2, 900000000, 3, 0)

    def launch(self, export, name, command):
        self.source_check()
        native = run(command, self.limits, cwd=self.exports[export])
        self.native.append(dict(export=export, name=name, native=native))
        self.save('raw', 'native/' + export + '/' + name + '.json', native)
        self.native_check(native); self.source_check()
        return native

    def prepared(self, export):
        assert len(self.grants) == 416
        native = self.launch(export, 'prepared', [sys.executable, '-B', '-m', 'unittest', *self.prepared_modules, '-v'])
        assert f'Ran {self.prepared_count} tests' in native['output'] and '\nOK' in native['output']

    def verify(self, key, receipt):
        grant, seal = self.grants[key]
        assert receipt['grant_sha256'] == seal and receipt['source_sha'] == self.provenance['source_sha256']
        assert receipt['config_sha'] == self.provenance['configuration_sha256'] and receipt['role'] == ':'.join(key)
        path = Path(grant['root'])/grant['phase']/grant['name']
        for parent in path.parents: plain(parent, True)
        info = plain(path)
        assert (info.st_dev, info.st_ino) == (grant['device'], grant['inode'])
        assert self.budget.files[grant['phase'] + '/' + grant['name']] == grant['limit']
        assert type(receipt['extent']) is int and 0 < receipt['extent'] <= grant['limit'] and info.st_size == receipt['extent']
        spec = dict(path=str(path), sha256=receipt['sha256'], extent=receipt['extent'])
        value = read_spec(spec, grant['limit'])
        assert digest(value) == receipt['sha256']
        return spec, value

    def endpoint(self, export, role, endpoint, input_spec, admission_spec):
        assert endpoint in ('raw', 'proof') and len(self.grants) == 416
        key = (export, role['name'], endpoint); grant, seal = self.grants[key]
        kind = role['kind'] + ('_ref' if endpoint == 'proof' else '')
        request = dict(role, kind=kind, export=export, role=':'.join(key), source_files=self.source_files,
                       **self.provenance, grant=grant, grant_seal=seal)
        if input_spec is not None: request['input'] = input_spec
        if admission_spec is not None: request['admission'] = admission_spec
        if endpoint == 'proof' or role['kind'] == 'fork': assert input_spec is not None
        treatment = role['kind'] == 'fork' or role.get('mode') == 'mutating'
        if treatment: assert admission_spec is not None
        params = self.save('raw', 'requests/' + '/'.join(key) + '.json', request)
        native = self.launch(export, role['name'] + '/' + endpoint,
            [sys.executable, '-B', '-m', 'experiments.digital_pressure71_scientific_child', params['path']])
        receipt = json.loads(native['output'])
        assert receipt['kind'] == kind and receipt['software_only'] is False and receipt['treatment'] is treatment
        assert type(receipt['world_constructors']) is int and receipt['world_constructors'] >= 0
        if endpoint == 'proof': assert receipt['world_constructors'] == 0
        artifact, value = self.verify(key, receipt)
        self.receipted_world_constructors += receipt['world_constructors']
        self.save('raw', 'receipts/' + '/'.join(key) + '.json', receipt)
        return artifact, value if endpoint == 'proof' else None

    def persist_admission(self, value): return self.save('raw', 'ordinary-scientific-admission.json', value)
    def read_admission(self, spec): return read_spec(spec, 1024**2)
    def record(self, name, value): return self.save('raw', name + '.json', value)
    def failed(self, value):
        self.save('failure', 'controller-flow-failure.json', dict(value,
            completed_native_children=len(self.native), receipted_world_constructors=self.receipted_world_constructors,
            unreceipted_constructor_count='UNKNOWN_IF_NATIVE_CHILD_FAILED', reserved_bank_queries=0))
