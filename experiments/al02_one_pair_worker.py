"""Fixed AL02 worker. Probe mode verifies imports without evaluating the context."""
import ctypes
from ctypes import wintypes
import hashlib
import importlib.abc
import importlib.util
import json
import msvcrt
import os
from pathlib import Path
import stat
import sys
import time

PROJECT = (
    'experiments', 'experiments.al02_one_pair', 'experiments.executed_heredity',
    'experiments.al02_depletion_checkpoint', 'experiments.al02_depletion_producer',
    'experiments.al02_depletion_projection', 'experiments.al02_depletion_suffix',
    'experiments.al02_selection_referee', 'experiments.al02_selection_request',
    'experiments.causal_genealogy_audit',
)
CONSENT = 'JeremyHennessy/Ora2.0#328:6740691539'
SUCCESSOR = 'AL02-SUCCESSOR-20261109-v3'
SUCCESSOR_ATTEMPT = Path('D:/OraLab/reports/al02-first-depletion-successor-20261109/attempt-v3')


def checked_bytes(path, pins):
    path = Path(path)
    if not path.is_absolute() or any(p.lstat().st_file_attributes &
            stat.FILE_ATTRIBUTE_REPARSE_POINT for p in (path, *path.parents)):
        raise ValueError(f'Unqualified path: {path}')
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != pins.get(str(path)):
        raise ValueError(f'Pinned source mismatch: {path}')
    return raw


class ProjectLoader(importlib.abc.MetaPathFinder, importlib.abc.Loader):
    def __init__(self, root, pins):
        self.sources = {}
        for name in PROJECT:
            path = root.joinpath(*name.split('.'))
            path = path / '__init__.py' if name == 'experiments' else path.with_suffix('.py')
            self.sources[name] = (path, checked_bytes(path, pins))

    def find_spec(self, fullname, path=None, target=None):
        if fullname in self.sources:
            file, _ = self.sources[fullname]
            return importlib.util.spec_from_file_location(
                fullname, file, loader=self,
                submodule_search_locations=[] if fullname == 'experiments' else None)
        if fullname.startswith('experiments.'):
            raise ImportError(f'Unapproved project import: {fullname}')
        return None

    def create_module(self, spec):
        return None

    def exec_module(self, module):
        path, raw = self.sources[module.__name__]
        exec(compile(raw, str(path), 'exec'), module.__dict__)


def load_project(root, pins):
    if any(n == 'experiments' or n.startswith('experiments.') for n in sys.modules):
        raise ValueError('Project code already imported')
    loader = ProjectLoader(root, pins)
    sys.meta_path.insert(0, loader)
    from experiments import al02_one_pair
    actual = {n for n in sys.modules if n == 'experiments' or n.startswith('experiments.')}
    if actual != set(PROJECT) or any(sys.modules[n].__loader__ is not loader for n in actual):
        raise ValueError('Imported project closure differs')
    return al02_one_pair, loader


def runtime_files():
    files = {str(Path(sys.executable))}
    for module in tuple(sys.modules.values()):
        path = getattr(module, '__file__', None)
        if path and not str(path).startswith('<'):
            file = Path(path)
            if file.is_file():
                files.add(str(file))
    return sorted(files)


def read_release(journal_sha256, expected_relay):
    """Accept exactly one live frame from the assigned relay, with bounded EOF."""
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    kernel.GetFileType.argtypes = [wintypes.HANDLE]
    kernel.IsProcessInJob.argtypes = [
        wintypes.HANDLE, wintypes.HANDLE, ctypes.POINTER(wintypes.BOOL)]
    kernel.GetNamedPipeServerProcessId.argtypes = [
        wintypes.HANDLE, ctypes.POINTER(wintypes.ULONG)]
    pipe = msvcrt.get_osfhandle(sys.stdin.fileno())
    assigned = wintypes.BOOL()
    server = wintypes.ULONG()
    if (kernel.GetFileType(pipe) != 3
            or not kernel.IsProcessInJob(kernel.GetCurrentProcess(), None, ctypes.byref(assigned))
            or not assigned.value):
        raise PermissionError('Release requires a live Job stdin pipe')
    if (not kernel.GetNamedPipeServerProcessId(pipe, ctypes.byref(server))
            or server.value != expected_relay):
        raise PermissionError('Release pipe server is not the recorded relay')
    raw = sys.stdin.buffer.read(513)
    if not raw or len(raw) > 512:
        raise PermissionError('Missing or oversized release frame')
    try:
        frame = json.loads(raw)
        expires = frame['expires']
        expected = dict(version=1, journal=journal_sha256, relay_pid=expected_relay,
                        expires=expires)
        if raw != json.dumps(expected).encode('ascii') or os.getppid() != expected_relay:
            raise ValueError('Release binding or relay differs')
        if type(expires) is not float or not 0 < expires - time.monotonic() <= 10:
            raise ValueError('Release expired or out of bounds')
    except (ValueError, TypeError, KeyError) as exc:
        raise PermissionError('Incorrect, duplicate or expired release frame') from exc


def main():
    if not (sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode):
        raise ValueError('Require isolated, no-site, no-bytecode Python')
    if len(sys.argv) != 3 or sys.argv[2] not in ('--probe', CONSENT, SUCCESSOR):
        raise ValueError('Unexpected worker arguments')
    manifest_path = Path(sys.argv[1])
    with manifest_path.open('rb') as stream:
        raw = stream.read(8 * 1024 * 1024 + 1)
    if len(raw) > 8 * 1024 * 1024:
        raise ValueError('Oversized manifest')
    manifest = json.loads(raw)
    pins = manifest['pins']
    checked_bytes(sys.executable, pins)
    checked_bytes(__file__, pins)
    root = Path(manifest['cwd'])
    if Path.cwd() != root or Path(__file__).parent.parent != root:
        raise ValueError('Worker root differs')
    release = sys.argv[2]
    if release != '--probe':
        expected = [sys.executable, '-I', '-S', '-B', __file__, sys.argv[1], release]
        environment = hashlib.sha256(json.dumps(dict(os.environ), sort_keys=True).encode()).hexdigest()
        if (manifest['command'] != expected or manifest['environment_sha256'] != environment
                or manifest['consent'] != release
                or manifest['evidence_tier'] != 'LOW_ASSURANCE_EXPLORATORY'):
            raise ValueError('Worker command or environment differs')
        intent_raw = (manifest_path.parent / '02-release-intent.json').read_bytes()
        intent = json.loads(intent_raw)
        verified = (manifest_path.parent / '01-verified.json').read_bytes()
        if (intent['verified_sha256'] != hashlib.sha256(verified).hexdigest()
                or json.loads(verified)['pending_sha256'] != hashlib.sha256(raw).hexdigest()):
            raise ValueError('Release journal differs')
    pair, loader = load_project(root, pins)
    files = runtime_files()
    if sys.argv[2] == '--probe':
        print(json.dumps(files))
        return
    for path in files:
        checked_bytes(path, pins)
    if manifest['context'] != pair.CONTEXT_SHA256:
        raise ValueError('Fixed context differs')
    read_release(hashlib.sha256(intent_raw).hexdigest(), json.loads(verified)['bootstrap_pid'])
    ora = Path('D:/OraLab')
    attempt = (SUCCESSOR_ATTEMPT if release == SUCCESSOR else
               ora / 'reports/al02-first-depletion-exploratory-20261109/attempt-6740691539')
    if (manifest_path != attempt / '00-pending.json'
            or root != ora / 'src/Ora2.0-al02-first-depletion-20261109'
            or manifest['owner'] != 'hennessydesktop\\hennessy'
            or (ora / 'automation/ora-codex/STOP').exists()):
        raise PermissionError('Scientific release outside fixed scope or STOP present')
    produce_bound_pair(pair, loader, attempt / "partial.jsonl")


def produce_bound_pair(pair, loader, evidence_path):
    """Scientific entry body for the admitted parent handoff only."""
    original = loader.sources['experiments.executed_heredity'][1]
    with evidence_path.open('xb', buffering=0) as stream:
        def save_event(phase, event):
            raw = json.dumps(dict(phase=phase, event=event), sort_keys=True, separators=(',', ':'),
                             ensure_ascii=True, allow_nan=False).encode('ascii') + b'\n'
            if stream.tell() + len(raw) > pair.MAX_OUTPUT:
                raise ValueError('Partial history exceeds evidence budget')
            if stream.write(raw) != len(raw):
                raise OSError('Short partial-history write')

        result = pair.produce(pair.CONTEXT, pair.CONTEXT_SHA256, pair.SEED, original,
                              save_event=save_event)
    sys.stdout.buffer.write(result)


if __name__ == '__main__':
    main()
