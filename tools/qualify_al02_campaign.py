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
TESTS=('test_al02_campaign_admission','test_al02_campaign_evidence','test_al02_natural_b_analysis',
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
    for name in ('campaign-binding.json','campaign-package.json'):
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
    return dict(status='NO-GO', verified_checks='PASS', terminal_sha256=sha(terminal),
                identities=identities, remaining=[
                    'Controller-native campaign concurrency and crash qualification absent',
                    'Positive B-uptake campaign transport fixture not exercised',
                    'Campaign parent and independent-review resource reservations unmeasured'])


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
