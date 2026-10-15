"""Finite read-only raw origin and old-native binding qualification; no Worlds."""
import ast,io,json,shutil,sys,zipfile
from pathlib import Path
import oralab
LAB=Path('D:/OraLab');DEV=LAB/'src/Ora2.0-recording82';M=1024**2
sys.path.insert(0,str(DEV))
from experiments.evidence_budget import Budget
from experiments.evidence_write_grant68 import plain,digest
from experiments.process_limits import Limits,run
from experience75_controller_core import native_ok,enc,fill_reserved
TAG='credited-fallback87v2-origin-prepared-v1';ROOT=LAB/'runs'/(TAG+'-20261015')
REG=LAB/'reports'/(TAG+'-registration.json');WORKER=LAB/'tools/credited_fallback87v2_origin_worker_v1.py'
ARCHIVE=LAB/'runs/credited-fallback87v2-paid-software-v1-20261015/archive/complete.zip'
CLOSED=LAB/'reports/credited-fallback87v2-paid-software-v1.json'
FILES=['experiments/__init__.py','experiments/process_limits.py','experiments/digital_recording82_reader.py',
 'experiments/evidence_write_grant68.py','experiments/digital_credited_fallback87v2_metrics.py',
 'experiments/digital_credited_fallback87v2_metric_binding.py','tests/test_digital_credited_fallback87v2_metrics.py',
 'docs/DIGITAL-CREDITED-FALLBACK87-V2-ORIGIN-QUALIFICATION.md']
def spec(p):return dict(path=str(p),extent=p.stat().st_size,sha256=oralab.sha(p))
def pins():return {str(p):oralab.sha(p) for p in [*[DEV/n for n in FILES],Path(__file__),WORKER,
 LAB/'tools/oralab.py',LAB/'tools/experience75_controller_core.py',DEV/'experiments/evidence_budget.py',
 LAB/'tools/credited_fallback87v2_paid_provenance_v1.py',
 LAB/'reports/credited-fallback87v2-origin-qualification-v1-20261015.md',
 LAB/'reports/credited-fallback87-v2-binding-prepared-v2.json',
 LAB/'reports/credited-fallback87v2-paid-publication-v1.json',CLOSED,ARCHIVE]}

def worker(owner):
    reg=json.loads(REG.read_bytes());assert pins()==reg['pins'] and oralab.sha(LAB/'state/operator.lock')==owner
    b=Budget(ROOT,dict(raw=128*M,archive=192*M,restore=192*M,failure=64*M),576*M)
    results=[];error=None;exact=False;derivations=[]
    def save(phase,name,data,reserve=0):
        with b.create(phase,name,reserve=reserve) as f:f.write(data)
    try:
        save('raw','registration.json',REG.read_bytes())
        for i,path in enumerate(reg['pins']):
            if Path(path)!=ARCHIVE:save('raw','owners/'+str(i)+'-'+Path(path).name,Path(path).read_bytes())
        save('raw','cached-previous.zip',ARCHIVE.read_bytes())
        for label in ('original','restored'):
            save('raw',label+'-native.json',b'',M)
            save('raw',label+'-derived.json',b'',8*M)
            save('raw',label+'-request.json',b'',64*1024)
        source=io.BytesIO()
        with zipfile.ZipFile(source,'w',zipfile.ZIP_DEFLATED) as z:
            for name in FILES:
                raw=(DEV/name).read_bytes();save('raw','original/'+name,raw);z.writestr(name,raw)
            save('raw','original/prepared_worker.py',WORKER.read_bytes());z.writestr('prepared_worker.py',WORKER.read_bytes())
        assert len(source.getvalue())<2*M
        save('archive','source.zip',source.getvalue())
        with zipfile.ZipFile(io.BytesIO(source.getvalue())) as z:
            for name in z.namelist():save('restore','restored/'+name,z.read(name))
        files={**{n:oralab.sha(DEV/n) for n in FILES},'prepared_worker.py':oralab.sha(WORKER)}
        assert sum((ROOT/'raw/original'/n).stat().st_size for n in files)*2<4*M
        for name in files:assert (ROOT/'raw/original'/name).read_bytes()==(ROOT/'restore/restored'/name).read_bytes()
        ss=digest(files);cs=digest(dict(version=TAG,closed_report=spec(CLOSED)))
        requests={}
        for label in ('original','restored'):
            p=ROOT/'raw'/(label+'-derived.json');info=plain(p);role='origin-qualification-'+label
            grant=dict(version='sharedlineage68-file-grant-candidate-v1',root=str(ROOT),phase='raw',
                name=p.name,limit=8*M,source_sha=ss,config_sha=cs,role=role,device=info.st_dev,inode=info.st_ino)
            requests[label]=dict(source_files=files,closed_report=spec(CLOSED),cached_archive=str(ROOT/'raw/cached-previous.zip'),
                source_sha=ss,config_sha=cs,role=role,grant=grant,seal=digest(grant))
            fill_reserved(ROOT,label+'-request.json',enc(requests[label]),64*1024)
        for label,path in (('original',ROOT/'raw/original'),('restored',ROOT/'restore/restored')):
            native=run([sys.executable,'-B','prepared_worker.py',str(ROOT/'raw'/(label+'-request.json'))],
                Limits(memory_bytes=512*M,cpu_seconds=60,wall_seconds=90,processes=3),cwd=path)
            fill_reserved(ROOT,label+'-native.json',enc(native),M)
            assert native_ok(native),native['output']
            result=json.loads(native['output']);results.append(result)
            p=ROOT/'raw'/(label+'-derived.json');receipt=result['receipt'];request=requests[label]
            assert receipt['grant_sha256']==request['seal'] and receipt['role']==request['role']
            assert receipt['source_sha']==ss and receipt['config_sha']==cs
            assert receipt['extent']==p.stat().st_size and receipt['sha256']==oralab.sha(p)
            derivations.append(spec(p))
        assert derivations[0]['sha256']==derivations[1]['sha256'] and pins()==reg['pins']
    except BaseException as exc:error=exc
    finally:
        save('failure','outcome.json',enc(dict(error=None if error is None else repr(error),results=results)))
        b.write_snapshot('failure')
        members=sorted(p for phase in ('raw','failure') for p in (ROOT/phase).rglob('*') if p.is_file())
        assert sum(p.stat().st_size for p in members)<160*M
        blob=io.BytesIO()
        with zipfile.ZipFile(blob,'w',zipfile.ZIP_STORED) as z:
            for p in members:z.writestr(p.relative_to(ROOT).as_posix(),p.read_bytes())
        save('archive','evidence.zip',blob.getvalue())
        with zipfile.ZipFile(io.BytesIO(blob.getvalue())) as z:
            for name in z.namelist():
                data=z.read(name);assert data==(ROOT/name).read_bytes();save('restore','evidence/'+name,data)
        exact=True
        oralab.write_json(LAB/'reports'/(TAG+'.json'),dict(passed=error is None,worlds=0,targets=0,
            source_free=True,execution_admission=False,checks=6,closed_originals=51,old_native_bindings=18,
            results=results,derivations=derivations,pins=reg['pins'],source_archive_exact=True,
            evidence_archive_sha256=oralab.sha(ROOT/'archive/evidence.zip'),evidence_exact_readback=exact,
            error=None if error is None else repr(error)))
    if error:raise error
    print('All51 CLOSED originals/18old native bindings and six NON-PHYSICS groups pass both exports;0Worlds/targets.')

if __name__=='__main__':
    if sys.argv[1]=='register':
        with oralab.lock():
            assert not ROOT.exists() and not REG.exists() and shutil.disk_usage(LAB).free>=584*M
            from credited_fallback87v2_paid_provenance_v1 import verify
            verify();assert ARCHIVE.stat().st_size<64*M
            assert sum(Path(p).stat().st_size for p in pins() if Path(p)!=ARCHIVE)<16*M
            for p in pins():
                if p.endswith('.py'):ast.parse(Path(p).read_bytes())
            oralab.write_json(REG,dict(pins=pins(),scope='Read-only all51 closed originals; no producer/target/referee imports',
                child=dict(memory_mib=512,cpu=60,wall=90,processes=3),
                parent=dict(memory_mib=768,cpu=180,wall=300,processes=4),evidence_mib=576,controller_mib=8))
    elif sys.argv[1]=='execute':
        with oralab.lock():
            assert pins()==json.loads(REG.read_bytes())['pins']
            b=Budget(LAB/'runs'/(TAG+'-controller-20261015'),dict(raw=6*M,failure=2*M),8*M)
            n=run([sys.executable,'-B',str(Path(__file__)),'worker',oralab.sha(LAB/'state/operator.lock')],
                Limits(memory_bytes=768*M,cpu_seconds=180,wall_seconds=300,processes=4),cwd=DEV)
            with b.create('raw','native.json') as f:f.write(enc(n))
            b.write_snapshot('failure');assert native_ok(n),n['output'];print(n['output'])
    else:worker(sys.argv[2])
