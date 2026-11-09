"""Qualify only the inactive eight-context supervised pilot in isolation."""
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import mkdtemp

ROOT=Path(__file__).resolve().parents[1]
ART=Path('D:/OraLab/reports/ora-al02-natural-b-panel-20261109')
TESTS=('test_al02_campaign_controller','test_al02_campaign_admission','test_al02_campaign_evidence',
       'test_al02_natural_b_analysis','test_al02_depletion_integration','test_al02_restore_entry',
       'test_al02_one_pair_custody','test_al02_one_pair_consent','test_al02_one_pair_release',
       'test_al02_partial_history')

def sha(path):return sha256(path.read_bytes()).hexdigest()

def protected():
    reports=ART.parent
    assert json.loads(Path('D:/OraLab/automation/ora-codex/status.json').read_bytes())['status']=='parked'
    for version in ('v2','v3'):
        rows=json.loads((reports/f'ora-al02-{version}-scientific-release-20261109/evidence-sha256.json').read_bytes())
        for row in rows:
            path=Path(row['path'])
            assert path.stat().st_size==row['bytes'] and sha(path)==row['sha256'], path
    assert not (reports/'al02-supervised-eight-attempts-20261109').exists()
    assert not (reports/'al02-natural-b-campaign-attempts-20261109').exists()


def run(out):
    assert os.name=='nt' and not sys.flags.optimize
    protected()
    assert not subprocess.check_output(['git','status','--porcelain'],cwd=ROOT).strip()
    for name in ('contexts.json','campaign-binding.json','campaign-package.json'):
        shutil.copyfile(ART/name,out/name)
    subprocess.run([sys.executable,'-B','-S',str(ROOT/'tools/build_al02_supervised_eight.py'),str(out)],
                   cwd=ROOT,check=True,timeout=15)
    pin=sha(ART/'supervised-eight-binding.json')
    assert sha(out/'supervised-eight-binding.json')==pin
    with (out/'tests.log').open('xb') as log:
        subprocess.run([sys.executable,'-B','-S','-m','unittest','-v',*(f'tests.{name}' for name in TESTS)],
            cwd=ROOT,env=dict(os.environ,AL02_CAMPAIGN_TEST_EVIDENCE=str(out)),
            stdout=log,stderr=subprocess.STDOUT,check=True,timeout=90)
    receipts={}
    for index in range(2):
        path=out/f'supervised-eight-transitions/attempt-{index:03d}/04-terminal.json'
        terminal=json.loads(path.read_bytes())
        identity=terminal['release_identities']
        assert identity['pilot_binding_sha256']==pin and identity['context_index']==index
        assert identity['inert_execution'] is True and terminal['result']['contrast']==0
        receipts[str(index)]=sha(path)
    assert not (out/'supervised-eight-transitions/reviewed-admissions.json').exists()
    assert not Path('D:/OraLab/reports/al02-supervised-eight-attempts-20261109').exists()
    protected()
    return dict(status='PASS', scope='inert supervised pilot only',
                pilot_binding_sha256=pin,terminals=receipts,
                head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                scientific_authorization=False,strict_campaign_qualified=False)

if __name__=='__main__':
    out=Path(mkdtemp(prefix='ora-al02-supervised-eight-'))
    print(f'Evidence: {out}',flush=True)
    try: result=run(out)
    except Exception as exc: result=dict(status='FAIL',error=repr(exc))
    (out/'qualification.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(result['status'])
    raise SystemExit(result['status']!='PASS')
