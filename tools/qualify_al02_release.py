"""Qualify the frozen AL02 V2 release with inert Windows transactions only."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
FROZEN = Path('D:/OraLab/drafts/ora-al02-release-v2')
PRODUCTION = Path('D:/OraLab/src/Ora2.0-al02-first-depletion-20261109')
V1 = FROZEN.with_name('ora-al02-production-installation')
HELPERS = ROOT / 'tests/al02_release_rehearsal'
TESTS = (
    'test_al02_final_v2', 'test_al02_candidate_binding', 'test_al02_one_pair_consent',
    'test_al02_one_pair_release', 'test_al02_partial_history', 'test_al02_one_pair_custody',
    'test_al02_depletion_integration',
)
EXPECTED = {
    'source-pins-v2.json': '56c343f5824ef86497db5f4cb2702431c446799e3756a0983269d6d2e1c79e7c',
    'installed-binding-v2.json': 'dbf11f4ba6dfecdbc205d392176e186b9072d682d2de229a20f025e5639a3327',
    'human-release-package-v2.json': '380087f218147745a1e06bd51f47dfe841255415126a5d156b483654d700104e',
    'installation-verification-v2.json': '5e6e11cf0661257dec9281d0b0dfa535f33b75acc9ba4913e2b0fdd02ab2d33c',
}

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read(path):
    return json.loads(path.read_bytes())

def require(condition, message):
    if not condition:
        raise ValueError(message)

def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args], text=True).strip()

def audit():
    require(ROOT.resolve() != PRODUCTION.resolve(), 'Production checkout prohibited')
    require(not git('status', '--porcelain'), 'Qualification requires a clean worktree')
    for name, expected in EXPECTED.items():
        require(sha(FROZEN / name) == expected, f'Frozen artifact changed: {name}')
    binding = read(FROZEN / 'installed-binding-v2.json')
    attempt = Path(binding['attempt'])
    require(not attempt.exists(), 'Production attempt must remain absent')
    require(binding['scientific_authorization'] is False, 'Inactive binding required')
    require(read(FROZEN/'human-release-package-v2.json')['scientific_authorization'] is False,
            'Inactive package required')
    require(read(Path('D:/OraLab/automation/ora-codex/status.json'))['status'] == 'parked',
            'Supervisor must remain PARKED')
    receipt = read(FROZEN / 'installation-verification-v2.json')
    production_pins = read(V1 / 'installed-binding-v1.json')['installed_file_pins']
    for target, expected in production_pins.items():
        require(sha(Path(target)) == expected, f'Production pin changed: {target}')
    for target, pair in receipt['replacements'].items():
        path = Path(target)
        require(sha(path) == pair['before'], f'Production replacement baseline changed: {path}')
        require(sha(ROOT / path.relative_to(PRODUCTION)) == pair['after'],
                f'Qualification module differs: {path}')
    local = {}
    for target, expected in binding['installed_file_pins'].items():
        path = Path(target)
        if path.is_relative_to(PRODUCTION):
            path = ROOT / path.relative_to(PRODUCTION)
        require(sha(path) == expected, f'V2 source inventory mismatch: {path}')
        local[str(path)] = expected
    for name in ('installed-binding-v1.json', 'human-release-package-v1.json'):
        expected = {'installed-binding-v1.json':'4da179bad479aadaec04d96483a6032bb33187593abc0ed45cd1493f0ed1a7fb',
                    'human-release-package-v1.json':'9f01cd5355961fa769efd38fc5cb956fb0abbdfa59cf6423169c4cc5e7843208'}[name]
        require(sha(V1/name) == expected, f'V1 artifact changed: {name}')
    return dict(head=git('rev-parse', 'HEAD'), pins=local, artifacts=EXPECTED,
                production_attempt=str(attempt), scientific_authorization=False,
                helpers={path.name: sha(path) for path in sorted(HELPERS.glob('*.py'))})

def run(out, name, args, *, source=None):
    with (out / name).open('xb') as log:
        subprocess.run([sys.executable, '-B', '-S', *args], cwd=ROOT,
                       input=source, stdout=log, stderr=subprocess.STDOUT,
                       timeout=90, check=True)

def qualify(out):
    baseline = audit()
    run(out, 'rebuild.log', [str(ROOT/'tools/build_al02_release_v2.py'), str(out/'rebuilt')])
    for name, expected in EXPECTED.items():
        require(sha(out/'rebuilt'/name) == expected, f'Rebuilt bytes differ: {name}')
    run(out, 'regressions.log', ['-m', 'unittest', '-v', *(f'tests.{n}' for n in TESTS)])
    rehearsal = out / 'inert'
    rehearsal.mkdir()
    shutil.copyfile(HELPERS/'inert-worker.py', rehearsal/'inert-worker.py')
    run(out, 'rehearsal.log', ['-', str(rehearsal)], source=(HELPERS/'rehearse.py').read_bytes())
    results = read(rehearsal/'results.json')
    require(set(results) == {'lawful', 'forged', 'interrupt', 'wrong-pin', 'stop', 'no-authority',
                            'race', 'substitute', 'auth-swap', 'pending-fail', 'receipt-swap',
                            'late-stop', 'crash-boundary'}, 'Mandatory scenario missing')
    attempt = rehearsal/'lawful/lawful'
    terminal = read(attempt/'04-terminal.json')
    identities = terminal['release_identities']
    for field, name in [('source_inventory_sha256', 'source-pins-v2.json'),
                        ('binding_sha256', 'installed-binding-v2.json'),
                        ('package_sha256', 'human-release-package-v2.json')]:
        require(identities[field] == EXPECTED[name], f'Terminal {field} differs')
    for name in ('00-pending.json','01-verified.json','02-release-intent.json','03-transport.json'):
        path = attempt/name
        require(sha(path) == terminal['receipt_sha256'][name], f'Receipt hash differs: {name}')
        require(read(path)['release_identities'] == identities, f'Identity differs: {name}')
    pending = read(attempt/'00-pending.json')
    require(pending['command'] == identities['inert_execution']['command']
            and pending['command'][4] == str(rehearsal/'inert-worker.py')
            and pending['command'] != read(FROZEN/'installed-binding-v2.json')['proposed_command'],
            'Execution was not the identified inert command')
    require(sha(attempt/'raw.bin') == terminal['raw_sha256'], 'Raw receipt mismatch')
    require(terminal['result']['authenticated_execution'] is False, 'Expected inert outcome')
    require(results['lawful']['second_claim'] == 'FileExistsError', 'Duplicate not refused')
    require(audit() == baseline, 'Baseline changed during qualification')
    return dict(status='PASS', scope='inert qualification only', baseline=baseline,
                terminal_sha256=sha(attempt/'04-terminal.json'), results_sha256=sha(rehearsal/'results.json'),
                release_identities=identities)

if __name__ == '__main__':
    if os.name != 'nt' or sys.flags.optimize:
        raise SystemExit('Windows and enabled assertions are required')
    out = Path(tempfile.mkdtemp(prefix='ora-al02-qualification-'))
    print(f'Evidence: {out}', flush=True)
    try:
        report = qualify(out)
    except Exception as error:
        report = dict(status='FAIL', error=repr(error))
    (out/'qualification.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(report['status'])
    raise SystemExit(report['status'] != 'PASS')
