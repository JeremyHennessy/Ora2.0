"""Inert AL02 engineering and continuation-entry qualification. Never releases."""
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
CONSUMED = Path('D:/OraLab/reports/ora-al02-v2-scientific-release-20261109')
SUCCESSOR = FROZEN.with_name('ora-al02-release-v3')
RESTORE = 'experiments/al02_depletion_producer.py'
REPAIRED_RESTORE = '266677b97c920a11359f818943c17aef240578b8cf58220c14d9d5333a1a0279'
HELPERS = ROOT / 'tests/al02_release_rehearsal'
TESTS = (
    'test_al02_final_v2', 'test_al02_candidate_binding', 'test_al02_one_pair_consent',
    'test_al02_one_pair_release', 'test_al02_partial_history', 'test_al02_one_pair_custody',
    'test_al02_depletion_integration', 'test_al02_depletion_checkpoint',
    'test_al02_depletion_producer', 'test_al02_restore_entry', 'test_al02_successor_worker_entry',
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
    evidence = CONSUMED/'evidence-sha256.json'
    require(sha(evidence) == 'c39e0b3a4d6475a7b6f6c7f2d94e831dd25d4b5a047a9d5fe98805d0d1733eff',
            'Consumed evidence inventory changed')
    evidence_rows = read(evidence)
    attempt_files = {Path(row['path']).name for row in evidence_rows
                     if Path(row['path']).parent == attempt}
    require({p.name for p in attempt.iterdir()} == attempt_files,
            'Consumed attempt file set differs')
    for row in evidence_rows:
        path = Path(row['path'])
        require(path.stat().st_size == row['bytes'] and sha(path) == row['sha256'],
                f'Consumed evidence differs: {path}')
    require(not (attempt.parent/'candidate-scientific-authorization.json').exists(),
            'Unexpected V1 candidate authority')
    require(binding['scientific_authorization'] is False, 'Inactive binding required')
    require(read(FROZEN/'human-release-package-v2.json')['scientific_authorization'] is False,
            'Inactive package required')
    require(read(Path('D:/OraLab/automation/ora-codex/status.json'))['status'] == 'parked',
            'Supervisor must remain PARKED')
    receipt = read(FROZEN / 'installation-verification-v2.json')
    activation = read(CONSUMED/'activation.json')
    for target, pair in receipt['replacements'].items():
        path = Path(target)
        expected = activation['consent_after'] if path.name.endswith('_consent.py') else pair['after']
        require(sha(path) == expected, f'Consumed production module changed: {path}')
    proposal = read(SUCCESSOR/'installed-binding-v3.json')
    external = read(SUCCESSOR/'installation-verification-v3.json')
    package = read(SUCCESSOR/'human-release-package-v3.json')
    require(all(sha(SUCCESSOR/name)==pin for name,pin in external['artifact_sha256'].items()),
            'Successor artifact hashes differ')
    require(external['artifact_sha256'] == {
        **package['artifact_sha256'],
        'human-release-package-v3.json': sha(SUCCESSOR/'human-release-package-v3.json')},
        'Successor package links differ')
    require(not Path(proposal['attempt']).exists()
            and not (Path(proposal['attempt']).parent/'candidate-scientific-authorization-v3.json').exists(),
            'Successor production scope must remain unused')
    require(proposal['seed']==binding['seed'] and proposal['limits']==binding['limits'],
            'Successor scientific scope differs')
    require(all(record['scientific_authorization'] is False
                for record in (proposal,external,package)), 'Successor must be inactive')
    for target, pair in external['replacements'].items():
        path = Path(target)
        require(sha(path)==pair['before_sha256'] and
                sha(ROOT/path.relative_to(PRODUCTION))==pair['after_sha256'],
                f'Successor replacement differs: {target}')
    local = {}
    for target, expected in binding['installed_file_pins'].items():
        path = Path(target)
        require(sha(path) == expected, f'Consumed production pin changed: {path}')
        successor_pin = proposal['installed_file_pins'][target]
        if path.is_relative_to(PRODUCTION):
            path = ROOT/path.relative_to(PRODUCTION)
        require(sha(path)==successor_pin, f'Successor source pin differs: {path}')
        local[str(path)] = successor_pin
    for name in ('installed-binding-v1.json', 'human-release-package-v1.json'):
        expected = {'installed-binding-v1.json':'4da179bad479aadaec04d96483a6032bb33187593abc0ed45cd1493f0ed1a7fb',
                    'human-release-package-v1.json':'9f01cd5355961fa769efd38fc5cb956fb0abbdfa59cf6423169c4cc5e7843208'}[name]
        require(sha(V1/name) == expected, f'V1 artifact changed: {name}')
    return dict(head=git('rev-parse', 'HEAD'), pins=local, artifacts=EXPECTED,
                consumed_attempt=str(attempt), successor_artifacts=external['artifact_sha256'],
                repaired_restore_sha256=REPAIRED_RESTORE, scientific_authorization=False,
                helpers={path.name: sha(path) for path in sorted(HELPERS.glob('*.py'))})

def run(out, name, args, *, source=None):
    with (out / name).open('xb') as log:
        subprocess.run([sys.executable, '-B', '-S', *args], cwd=ROOT,
                       input=source, stdout=log, stderr=subprocess.STDOUT,
                       timeout=90, check=True)

def qualify(out):
    baseline = audit()
    run(out, 'successor-rebuild.log', [str(ROOT/'tools/build_al02_release_v3.py'),str(out/'rebuilt')])
    for name in (*baseline['successor_artifacts'], 'installation-verification-v3.json'):
        require(sha(out/'rebuilt'/name)==sha(SUCCESSOR/name), f'Successor rebuild differs: {name}')
    run(out, 'regressions.log', ['-m', 'unittest', '-v', *(f'tests.{n}' for n in TESTS)])
    # Reintroduce the exact historical failure in memory, without changing any file.
    mutation = r'''
from pathlib import Path
from unittest import main
from experiments import al02_depletion_producer as producer
from tests import test_al02_restore_entry
path = Path(producer.__file__)
raw = path.read_text()
fixed = "vars(obj).update(config)\n        vars(obj).update(state['counters'])"
assert raw.count(fixed) == 1
mutated = raw.replace(fixed, "vars(obj).update(config, state['counters'])")
exec(compile(mutated, str(path), 'exec'), producer.__dict__)
main(module=test_al02_restore_entry, argv=['mutation',
    'RestoreEntryTests.test_real_restore_and_both_branch_starts'])
'''
    with (out/'restore-mutation.log').open('xb') as log:
        result = subprocess.run([sys.executable, '-B', '-S', '-'], cwd=ROOT,
                                input=mutation.encode(), stdout=log,
                                stderr=subprocess.STDOUT, timeout=30)
    require(result.returncode != 0 and
            'TypeError: update expected at most 1 argument, got 2' in
            (out/'restore-mutation.log').read_text(),
            'Scientific-entry readiness did not reject the original restore defect')
    rehearsal = out / 'inert'
    rehearsal.mkdir()
    shutil.copyfile(HELPERS/'inert-worker.py', rehearsal/'inert-worker.py')
    run(out, 'rehearsal.log', ['-', str(rehearsal)], source=(HELPERS/'rehearse.py').read_bytes())
    results = read(rehearsal/'results.json')
    require(set(results) == {'lawful', 'forged', 'interrupt', 'wrong-pin', 'stop', 'no-authority',
                            'race', 'substitute', 'auth-swap', 'pending-fail', 'receipt-swap',
                            'late-stop', 'crash-boundary', 'final-auth-swap', 'wrong-destination'}, 'Mandatory scenario missing')
    attempt = rehearsal/'lawful/lawful'
    terminal = read(attempt/'04-terminal.json')
    identities = terminal['release_identities']
    for field, name in [('source_inventory_sha256', 'source-pins-v3.json'),
                        ('binding_sha256', 'installed-binding-v3.json'),
                        ('package_sha256', 'human-release-package-v3.json')]:
        require(identities[field] == baseline['successor_artifacts'][name], f'Terminal {field} differs')
    for name in ('00-pending.json','01-verified.json','02-release-intent.json','03-transport.json'):
        path = attempt/name
        require(sha(path) == terminal['receipt_sha256'][name], f'Receipt hash differs: {name}')
        require(read(path)['release_identities'] == identities, f'Identity differs: {name}')
    pending = read(attempt/'00-pending.json')
    require(pending['command'] == identities['inert_execution']['command']
            and pending['command'][4] == str(rehearsal/'inert-worker.py')
            and pending['command'] != read(SUCCESSOR/'installed-binding-v3.json')['proposed_command'],
            'Execution was not the identified inert command')
    require(sha(attempt/'raw.bin') == terminal['raw_sha256'], 'Raw receipt mismatch')
    transport = read(attempt/'03-transport.json')
    journal = attempt/'partial.jsonl'
    require(sha(journal) == transport['partial']['sha256']
            and journal.stat().st_size == transport['partial']['bytes'],
            'Journal receipt mismatch')
    job = transport['receipt']
    require(job['accepted'] and job['eof'] and job['observed_closed']
            and job['final']['started_processes'] == 2
            and job['final']['active_before_close'] == 0, 'Job closure incomplete')
    require(terminal['result']['authenticated_execution'] is False, 'Expected inert outcome')
    require(results['lawful']['second_claim'] == 'FileExistsError', 'Duplicate not refused')
    require(audit() == baseline, 'Baseline changed during qualification')
    return dict(status='PASS', scope='inactive V3 inert engineering only',
                scientific_entry='both initialized with zero ticks', future_release_qualified=False, baseline=baseline,
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
