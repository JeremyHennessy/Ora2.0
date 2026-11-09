"""Inert relay child: no experiment driver import, only worker journal/release functions."""
import hashlib, importlib.util, json, os, sys
from pathlib import Path
from types import SimpleNamespace
pending_path = Path(sys.argv[1])
assert sys.argv[2] == 'ORA-PHASE6-INERT'
pending = pending_path.read_bytes()
manifest = json.loads(pending)
attempt = pending_path.parent
worker_path = Path(manifest['cwd']) / 'experiments/al02_one_pair_worker.py'
assert hashlib.sha256(worker_path.read_bytes()).hexdigest() == manifest['pins'][str(worker_path)]
spec = importlib.util.spec_from_file_location('candidate_worker', worker_path)
worker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(worker)
verified = (attempt / '01-verified.json').read_bytes()
intent = (attempt / '02-release-intent.json').read_bytes()
assert json.loads(verified)['pending_sha256'] == hashlib.sha256(pending).hexdigest()
assert json.loads(intent)['verified_sha256'] == hashlib.sha256(verified).hexdigest()
worker.read_release(hashlib.sha256(intent).hexdigest(), json.loads(verified)['bootstrap_pid'])
fixture = attempt.parent / ('forged.bin' if attempt.name == 'forged' else 'lawful.bin')
raw = worker.checked_bytes(fixture, manifest['pins'])
payload = json.loads(raw)
def emit_fixture(*args, save_event):
    for event in json.loads(payload['checkpoint'])['state']['events']:
        save_event('prefix', event)
        if attempt.name == 'interrupt':
            os._exit(7)
    for role in ('accessible', 'sequestered'):
        for event in payload['branches'][role]['events']:
            save_event(role, event)
    return raw
inert = SimpleNamespace(CONTEXT='', CONTEXT_SHA256='', SEED=0, MAX_OUTPUT=1048576, produce=emit_fixture)
worker.produce_bound_pair(inert, SimpleNamespace(sources={'experiments.executed_heredity': (None, b'')}),
                          attempt / 'partial.jsonl')
