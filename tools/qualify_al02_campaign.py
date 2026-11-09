"""Run the isolated campaign checks. Full readiness remains fail-closed."""
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import mkdtemp

ROOT=Path(__file__).resolve().parents[1]
ART=Path('D:/OraLab/reports/ora-al02-natural-b-panel-20261109')
TESTS=('test_al02_campaign_controller','test_al02_campaign_admission','test_al02_campaign_evidence','test_al02_natural_b_analysis',
       'test_al02_depletion_integration','test_al02_restore_entry','test_al02_one_pair_custody',
       'test_al02_one_pair_consent','test_al02_one_pair_release','test_al02_partial_history')

def sha(path):return sha256(path.read_bytes()).hexdigest()

def qualify(out):
    if os.name!='nt' or sys.flags.optimize:
        raise ValueError('Windows with enabled assertions required')
    if subprocess.check_output(['git','status','--porcelain'],cwd=ROOT).strip():
        raise ValueError('Clean worktree required')
    subprocess.run([sys.executable,'-B','-S',str(ROOT/'tools/build_al02_campaign.py'),
                    str(out)],cwd=ROOT,check=True,timeout=30)
    for name in ('campaign-binding.json','campaign-package.json','campaign-verification.json'):
        if sha(out/name)!=sha(ART/name):
            raise ValueError(f'Rebuild differs: {name}')
    env=dict(os.environ, AL02_CAMPAIGN_TEST_EVIDENCE=str(out))
    with (out/'tests.log').open('xb') as log:
        subprocess.run([sys.executable,'-B','-S','-m','unittest','-v',
                        *(f'tests.{name}' for name in TESTS)],cwd=ROOT,env=env,
                        stdout=log,stderr=subprocess.STDOUT,check=True,timeout=90)
    terminal=out/'inert-attempt/04-terminal.json'
    identities=json.loads(terminal.read_bytes())['release_identities']
    if (identities['binding_sha256']!=sha(ART/'campaign-binding.json')
            or identities['package_sha256']!=sha(ART/'campaign-package.json')
            or identities['contexts_sha256']!=sha(ART/'contexts.json')
            or identities['inert_execution'] is not True):
        raise ValueError('Inert terminal identity differs')
    controller_terminals = {}
    for index in range(2):
        path = out/f'controller-transitions/attempt-{index:03d}/04-terminal.json'
        terminal = json.loads(path.read_bytes())
        identity = terminal['release_identities']
        if (identity['context_index'] != index or identity['inert_execution'] is not True
                or identity['binding_sha256'] != sha(ART/'campaign-binding.json')):
            raise ValueError('Controller terminal identity differs')
        controller_terminals[str(index)] = sha(path)
    positive = out/'controller-positive-uptake/attempt-000/04-terminal.json'
    result = json.loads(positive.read_bytes())['result']
    if result['branches']['accessible']['b_meals'] != 10 or result['contrast'] != 3:
        raise ValueError('Positive uptake fixture result differs')
    return dict(status='NO-GO', verified_checks='PASS',
                controller_terminals=controller_terminals, positive_fixture_sha256=sha(positive),
                terminal_sha256=sha(out/'inert-attempt/04-terminal.json'),
                identities=identities, remaining=[
                    'Production reviewer publication identity and authenticated admission channel not provisioned',
                    'Physical parent and independent-review reservations not established',
                    'Controller race uses real lock and claim with Job dispatch blocked for the crash probe'])



if __name__=='__main__':
    out=Path(mkdtemp(prefix='ora-al02-campaign-qualification-'))
    print(f'Evidence: {out}',flush=True)
    try:
        result=qualify(out)
    except Exception as exc:
        result=dict(status='FAIL',error=repr(exc))
    (out/'qualification.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(result['status'])
    raise SystemExit(1)
