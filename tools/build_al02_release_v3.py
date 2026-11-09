"""Build inactive successor artifacts from fixed V2 identities and reviewed overlays."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

def sha(data):
    return hashlib.sha256(data).hexdigest()

def encode(obj):
    return (json.dumps(obj,sort_keys=True,indent=2)+'\n').encode('ascii')

root=Path(__file__).resolve().parents[1]
v2=Path('D:/OraLab/drafts/ora-al02-release-v2')
original=(v2/'installed-binding-v2.json').read_bytes()
assert sha(original)=='dbf11f4ba6dfecdbc205d392176e186b9072d682d2de229a20f025e5639a3327'
b=json.loads(original)
prod=Path(b['proposed_cwd'])
attempt=Path('D:/OraLab/reports/al02-first-depletion-successor-20261109/attempt-v3')
assert not attempt.exists()
assert b['seed']==8195177122164069225 and b['scientific_authorization'] is False
pins=b['installed_file_pins']
b['project_git_blobs'].pop('experiments/al02_one_pair_consent.py',None)
changes={}
for name in ('al02_depletion_producer.py','al02_one_pair_worker.py',
             'al02_one_pair_custody.py','al02_one_pair_consent.py'):
    relative='experiments/'+name
    target=str(prod/relative)
    changes[target]=dict(before_sha256=sha(Path(target).read_bytes()),
                         after_sha256=sha((root/relative).read_bytes()))
    if name!='al02_one_pair_consent.py':
        assert pins[target]==changes[target]['before_sha256']
        pins[target]=changes[target]['after_sha256']
        b['project_git_blobs'][relative]=subprocess.check_output(
            ['git','-C',str(root),'hash-object','--path='+relative,str(root/relative)],
            text=True).strip()
command=b['proposed_command']
command[5:]=[str(attempt/'00-pending.json'),'AL02-SUCCESSOR-20261109-v3']
b['proposed_relay_argv'][-1]=json.dumps(command)
for name in ('approved_worker_sha256','prior_release_sha256','candidate_binding_sha256',
             'reconciliation_sha256','actual_entry_qualification_sha256','inert_equivalence_sha256'):
    b.pop(name,None)
inventory=encode(pins)
b.update(schema='ora.al02.installed-binding.v3', candidate_commit='01b4ae6f7b468d5924322816da1d6c4520886011',
         attempt=str(attempt),candidate_worker_sha256=pins[command[4]],
         source_inventory_sha256=sha(inventory), engineering_status='Inactive successor proposal',
         one_attempt_policy='Atomic directory claim consumes attempt; no retry',
         precondition='Separate approval for installation and exact successor scientific authorization')
binding=encode(b)
package=encode(dict(schema='AL02-INACTIVE-HUMAN-RELEASE-PACKAGE-v3',candidate=b['candidate_commit'],
    production_head=b['production_git_head'],seed=str(b['seed']),attempt=str(attempt),
    scientific_authorization=False,artifact_sha256={'installed-binding-v3.json':sha(binding),
                                                    'source-pins-v3.json':sha(inventory)}))
files={'source-pins-v3.json':inventory,'installed-binding-v3.json':binding,
       'human-release-package-v3.json':package}
files['installation-verification-v3.json']=encode(dict(scientific_authorization=False,
    replacements=changes, consent_git_blob=subprocess.check_output(
        ['git','-C',str(root),'hash-object','--path=experiments/al02_one_pair_consent.py',
         str(root/'experiments/al02_one_pair_consent.py')],text=True).strip(),
    artifact_sha256={name:sha(raw) for name,raw in files.items()},
    rollback='Restore byte-exact backups of authorized replacements and preserve all attempt paths.'))
out=Path(sys.argv[1])
out.mkdir(exist_ok=True)
for name,raw in files.items():
    path=out/name
    if path.exists():
        if path.read_bytes()!=raw:
            raise ValueError(f'Refusing changed artifact: {path}')
    else:
        with path.open('xb') as stream:
            stream.write(raw)
print(sha(binding),sha(package),pins[command[4]],pins[str(prod/'experiments/al02_one_pair_custody.py')])
