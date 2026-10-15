"""Read-only complete closed corpus qualification; constructors/targets forbidden."""
import hashlib,io,json,sys,unittest,zipfile
from pathlib import Path
root=Path.cwd();sys.path.insert(0,str(root))
request=json.loads(Path(sys.argv[1]).read_bytes())
def sha(path):
    result=hashlib.sha256()
    with Path(path).open('rb') as f:
        while block:=f.read(1024**2):result.update(block)
    return result.hexdigest()
for name,value in request['source_files'].items():assert sha(root/name)==value
ALLOWED={'experiments.digital_credited_fallback87v2_metrics','experiments.digital_credited_fallback87v2_metric_binding',
         'experiments.digital_recording82_reader','experiments.evidence_write_grant68','experiments.process_limits'}
class Guard:
    def find_spec(self,fullname,path=None,target=None):
        if fullname.startswith('experiments.') and fullname not in ALLOWED:
            raise AssertionError('World/source/target/referee/acceptance import forbidden: '+fullname)
sys.meta_path.insert(0,Guard())
from experiments import digital_credited_fallback87v2_metrics as metrics
from experiments import digital_credited_fallback87v2_metric_binding as binding
from experiments.digital_recording82_reader import read_spec
from experiments import evidence_write_grant68 as transport
buffer=io.StringIO()
result=unittest.TextTestRunner(stream=buffer,verbosity=2).run(
    unittest.defaultTestLoader.discover(str(root/'tests'),pattern='test_digital_credited_fallback87v2_metrics.py'))
if not result.wasSuccessful():print(buffer.getvalue())
assert result.wasSuccessful() and result.testsRun==6

closed=Path('D:/OraLab/runs/credited-fallback87v2-paid-software-v1-20261015')
report_spec=request['closed_report'];raw=Path(report_spec['path']).read_bytes()
assert len(raw)==report_spec['extent'] and hashlib.sha256(raw).hexdigest()==report_spec['sha256']
report=json.loads(raw);assert report['verified'] is True and report['archive_exact'] is True
assert report['native_calls']==22 and report['completed_software_geneses']==102
archive=Path(request['cached_archive']);assert sha(archive)==report['archive_sha256']
assert archive.stat().st_size<64*1024**2
membership=[];bindings=[];specs=report['completed_roles']
with zipfile.ZipFile(archive) as z:
    def member(path):
        path=Path(path);name=path.relative_to(closed).as_posix()
        expected=z.getinfo(name);assert expected.file_size==path.stat().st_size
        h=hashlib.sha256()
        with z.open(name) as stream:
            while block:=stream.read(1024**2):h.update(block)
        value=h.hexdigest();assert sha(path)==value
        membership.append(dict(member=name,extent=expected.file_size,sha256=value))
    regpath=closed/'raw/registration.json';member(regpath)
    configuration=json.loads(regpath.read_bytes())['configuration']
    for role,spec in specs.items():
        stem=role.replace(':','-');reqpath=closed/'raw/request'/(stem+'.json')
        nativepath=closed/'raw/native'/(stem+'.json');path=Path(spec['path'])
        for p in (reqpath,nativepath,path):member(p)
        req=json.loads(reqpath.read_bytes());native=json.loads(nativepath.read_bytes())
        info=transport.plain(path)
        grant_path=str(Path(req['grant']['root'])/req['grant']['phase']/req['grant']['name'])
        bindings.append(binding.authenticate(req,native,spec,role,configuration,grant_path,(info.st_dev,info.st_ino)))
        export=role.split(':')[0]
        for name,digest in req['source_files'].items():
            p=closed/'raw'/export/name;member(p);assert sha(p)==digest
    assert len(bindings)==18

batches=[]
for group in metrics.GROUPS:
    orig=specs[f'original:2100382:{group}:generate']
    replay=specs[f'restored:2100382:{group}:generate']
    assert (orig['extent'],orig['sha256'])==(replay['extent'],replay['sha256'])
    proofspec=specs[f'original:2100382:{group}:audit']
    body=read_spec(orig);proof=read_spec(proofspec)
    binding.bind_inputs(orig,body,proof)
    batches.append(metrics.batch(body,proof))
    del body,proof
value=metrics.combine(batches)
value.update(cached_archive_sha256=report['archive_sha256'],cached_source_native_membership=membership,
             old_native_bindings=bindings,worlds=0,targets=0)
for name,digest in request['source_files'].items():assert sha(root/name)==digest
for name,module in tuple(sys.modules.items()):
    if name.startswith('experiments.'):
        assert name in ALLOWED and Path(module.__file__).resolve()==root/(name.replace('.','/')+'.py')
receipt=transport.record(request['grant'],request['seal'],request['source_sha'],request['config_sha'],request['role'],value)
print(json.dumps(dict(verified=True,checks=6,closed_originals=51,closed_bindings=len(bindings),
    worlds=0,targets=0,source_free=True,execution_admission=False,receipt=receipt),sort_keys=True))
