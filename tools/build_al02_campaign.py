"""Build deterministic inactive campaign artifacts from the frozen V3 inventory."""
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
LAB=Path('D:/OraLab')
BASE=LAB/'drafts/ora-al02-release-v3/installed-binding-v3.json'
OUT=Path(sys.argv[1])
def raw(obj): return (json.dumps(obj,sort_keys=True,indent=2)+'\n').encode('ascii')
def sha(data): return sha256(data).hexdigest()
assert sha(BASE.read_bytes())=='922f882c0d9013408f0c4a94c9c9c7643f8b844eb90dd3174aba3b7b409329d9'
v3=json.loads(BASE.read_bytes())
prod=Path(v3['proposed_cwd'])
pins=v3['installed_file_pins']
for name in ('al02_one_pair.py','al02_one_pair_worker.py','al02_one_pair_custody.py'):
    pins[str(prod/'experiments'/name)]=sha((ROOT/'experiments'/name).read_bytes())
b=raw(dict(schema='al02-campaign-binding-v1', scientific_authorization=False,
           contexts_sha256='065149a3c3aa278c9dbc14527a8f54e354602e6ebcd3a87360cf20fa6e377804',
           checkout=str(prod), production_head=v3['production_git_head'],
           destination=str(LAB/'reports/al02-natural-b-campaign-attempts-20261109'),
           python=v3['proposed_command'][0], worker=v3['proposed_command'][4],
           limits=v3['limits'], pins=pins,
           budget=dict(pairs=128,instructions=153600,cpu_seconds=640,job_wall_seconds=1280,
                       archive_bytes=1073741824, raw_bytes_per_pair=1048576,
                       journal_bytes_per_pair=1048576, archive_bytes_per_pair=8388608,
                       expected_births_per_pair=2, simultaneous_jobs=1),
           halt_policy='halt after any unreviewed claim, STOP, integrity or capacity failure'))
p=raw(dict(schema='al02-campaign-package-v1',scientific_authorization=False,
           binding_sha256=sha(b), controls='separate protocols; excluded'))
runtime_paths = [
    'experiments/al02_campaign_admission.py', 'experiments/al02_one_pair.py',
    'experiments/al02_one_pair_worker.py', 'experiments/al02_one_pair_custody.py',
    'experiments/al02_depletion_suffix.py', 'tools/run_al02_campaign.py',
    'tools/al02_campaign_evidence.py', 'tools/al02_natural_b_analysis.py',
    'tools/build_al02_campaign.py', 'tools/qualify_al02_campaign.py',
    'tests/test_al02_campaign_controller.py',
    'tests/al02_release_rehearsal/campaign-controller-probe.py',
]
external=raw(dict(schema='al02-campaign-external-verification-v1',
    scientific_authorization=False, binding_sha256=sha(b), package_sha256=sha(p),
    raw_source_sha256={name:sha((ROOT/name).read_bytes()) for name in runtime_paths},
    review_trust='Independent reviewer publication identity must be provisioned before activation'))
for name,data in [('campaign-binding.json',b),('campaign-package.json',p),
                  ('campaign-verification.json',external)]:
    path=OUT/name
    if path.exists():
        if path.read_bytes()!=data: raise ValueError(f'Refusing to replace {name}')
    else:
        with path.open('xb') as f:f.write(data)
print(sha(b),sha(p))
