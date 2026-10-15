"""Whole primary controller qualification; no valid producer/World permitted."""
import ast,io,json,runpy,shutil,sys,zipfile
from pathlib import Path
import oralab
LAB=Path('D:/OraLab');DEV=LAB/'src/Ora2.0-recording82';M=1024**2
sys.path.insert(0,str(DEV))
from experiments.evidence_budget import Budget
from experiments.process_limits import Limits,run
from experiments.evidence_write_grant68 import plain,digest
from experience75_controller_core import enc,fill_reserved,native_ok
parent=runpy.run_path(str(DEV/'lab/run_credited_fallback87v2_primary_v1.py'))
FILES=sorted(parent['FILES']);CONFIG=parent['CONFIG'];ROLES=parent['ROLES']
WORKER=LAB/'tools/credited_fallback87v2_primary_prepared_worker_v2.py'
TAG='credited-fallback87v2-primary-prepared-v2';ROOT=LAB/'runs'/(TAG+'-20261015')
REG=LAB/'reports'/(TAG+'-registration.json')
def pins():return {str(p):oralab.sha(p) for p in [*[DEV/n for n in FILES],Path(__file__),WORKER,
 LAB/'tools/oralab.py',LAB/'tools/experience75_controller_core.py',LAB/'tools/cognitive76_controller_core_v2.py',
 LAB/'tools/credited_fallback87v2_primary_reuse_v1.py',LAB/'reports/credited-fallback87v2-primary-custody-qualification-v1-20261015.md',
 LAB/'reports/credited-fallback87v2-primary-controller-contract-v1-20261015.md',
 LAB/'reports/credited-fallback87v2-primary-custody-qualification-v2-20261015.md',LAB/'reports/credited-fallback87v2-primary-prepared-v1.json',
 LAB/'reports/credited-fallback87v2-origin-prepared-v2.json',LAB/'reports/credited-fallback87v2-origin-namespace-prepared-v1.json']}

def worker(owner):
    reg=json.loads(REG.read_bytes());assert pins()==reg['pins'] and oralab.sha(LAB/'state/operator.lock')==owner
    b=Budget(ROOT,dict(raw=192*M,archive=256*M,restore=256*M,failure=64*M),768*M)
    results=[];refusals=[];error=None
    def save(phase,name,data,reserve=0):
        with b.create(phase,name,reserve=reserve) as f:f.write(data)
    try:
        save('raw','registration.json',REG.read_bytes())
        for i,path in enumerate(reg['pins']):save('raw','owners/'+str(i)+'-'+Path(path).name,Path(path).read_bytes())
        for name in ('original-native.json','restored-native.json',*['refused'+str(i)+'-native.json' for i in range(4)]):save('raw',name,b'',M)
        for name in ('original-request.json','restored-request.json',*['refused'+str(i)+'-request.json' for i in range(4)]):save('raw',name,b'',64*1024)
        save('raw','refusal-slot.json',b'',64*M)
        source=io.BytesIO()
        with zipfile.ZipFile(source,'w',zipfile.ZIP_STORED) as z:
            for name in FILES:
                data=(DEV/name).read_bytes();save('raw','original/'+name,data);z.writestr(name,data)
            save('raw','original/prepared_worker.py',WORKER.read_bytes());z.writestr('prepared_worker.py',WORKER.read_bytes())
        assert len(source.getvalue())<=2*M
        save('archive','source.zip',source.getvalue())
        with zipfile.ZipFile(io.BytesIO(source.getvalue())) as z:
            for name in z.namelist():save('restore','restored/'+name,z.read(name))
        for name in FILES+['prepared_worker.py']:assert (ROOT/'raw/original'/name).read_bytes()==(ROOT/'restore/restored'/name).read_bytes()
        files={name:oralab.sha(DEV/name) for name in FILES};ss=digest(files);cs=digest(CONFIG)
        slot=ROOT/'raw/refusal-slot.json';info=plain(slot)
        grant=dict(version='sharedlineage68-file-grant-candidate-v1',root=str(ROOT),phase='raw',name='refusal-slot.json',
            limit=64*M,source_sha=ss,config_sha=cs,role=ROLES[0],device=info.st_dev,inode=info.st_ino)
        base=dict(configuration=CONFIG,source_files=files,source_sha=ss,config_sha=cs,role=ROLES[0],kind='generate',input=None,grant=grant,seal=digest(grant))
        oldroot=LAB/'runs/credited-fallback87v2-primary-prepared-v1-20261015'
        failed=json.loads((LAB/'reports/credited-fallback87v2-primary-prepared-v1.json').read_bytes())
        assert failed['passed'] is False and failed['actual_preWorld_refusals']==['role','configuration','source_sha','seal']
        assert oralab.sha(oldroot/'archive/evidence.zip')==failed['evidence_archive_sha256']
        proof=[]
        for i,field in enumerate(failed['actual_preWorld_refusals']):
            request_path=oldroot/'raw'/('refused'+str(i)+'-request.json')
            native_path=oldroot/'raw'/('refused'+str(i)+'-native.json')
            request=json.loads(request_path.read_bytes());native=json.loads(native_path.read_bytes())
            assert native['exit_code']!=0 and native['post_close_processes_exited'] is True
            assert native['usage']['active_before_close']==0 and not native['timed_out'] and not native['output_truncated']
            assert '"rejected_before_world":true' in native['output']
            for name in ('experiments/digital_credited_fallback87v2_primary_child.py',
                         'experiments/digital_credited_fallback87v2_primary_plan.py',
                         'experiments/digital_credited_fallback87v2_primary_boundary.py',
                         'tests/test_digital_credited_fallback87v2_primary.py'):
                assert oralab.sha(DEV/name)==request['source_files'][name]
            proof.append(dict(field=field,request=str(request_path),request_sha256=oralab.sha(request_path),
                              native=str(native_path),native_sha256=oralab.sha(native_path)))
            refusals.append(field)
        save('raw','reused-four-native-refusals.json',enc(dict(old_archive=failed['evidence_archive_sha256'],proofs=proof)))
        files['prepared_worker.py']=oralab.sha(WORKER)
        for label in ('original','restored'):fill_reserved(ROOT,label+'-request.json',enc(dict(source_files=files)),64*1024)
        for label,path in (('original',ROOT/'raw/original'),('restored',ROOT/'restore/restored')):
            native=run([sys.executable,'-B','prepared_worker.py',str(ROOT/'raw'/(label+'-request.json'))],
                Limits(memory_bytes=512*M,cpu_seconds=60,wall_seconds=90,processes=3),cwd=path)
            fill_reserved(ROOT,label+'-native.json',enc(native),M)
            assert native_ok(native),native['output'];results.append(json.loads(native['output']))
        assert results[0]==results[1] and pins()==reg['pins']
    except BaseException as exc:error=exc
    finally:
        save('failure','outcome.json',enc(dict(error=None if error is None else repr(error),results=results,refusals=refusals)))
        b.write_snapshot('failure')
        members=sorted(p for phase in ('raw','failure') for p in (ROOT/phase).rglob('*') if p.is_file())
        assert sum(p.stat().st_size for p in members)<128*M
        blob=io.BytesIO()
        with zipfile.ZipFile(blob,'w',zipfile.ZIP_STORED) as z:
            for p in members:z.writestr(p.relative_to(ROOT).as_posix(),p.read_bytes())
        save('archive','evidence.zip',blob.getvalue())
        with zipfile.ZipFile(io.BytesIO(blob.getvalue())) as z:
            for name in z.namelist():
                data=z.read(name);assert data==(ROOT/name).read_bytes();save('restore','evidence/'+name,data)
        oralab.write_json(LAB/'reports'/(TAG+'.json'),dict(passed=error is None,checks=6,actual_preWorld_refusals_reused=refusals,new_native_calls=2,
            worlds=0,targets=0,valid_primary_roles=0,results=results,pins=reg['pins'],
            evidence_archive_sha256=oralab.sha(ROOT/'archive/evidence.zip'),evidence_exact_readback=True,
            source_archive_exact=True,error=None if error is None else repr(error)))
    if error:raise error
    print('Six whole-primary NON-PHYSICS groups both exports pass;four prior real refusals bound by hash;0Worlds/targets.')

if __name__=='__main__':
    if sys.argv[1]=='register':
        with oralab.lock():
            assert not ROOT.exists() and not REG.exists() and shutil.disk_usage(LAB).free>=776*M
            from credited_fallback87v2_primary_reuse_v1 import verify
            verify()
            assert sum(Path(p).stat().st_size for p in pins())<16*M
            assert sum((DEV/n).stat().st_size for n in FILES)*2+WORKER.stat().st_size<4*M
            for p in pins():
                if p.endswith('.py'):ast.parse(Path(p).read_bytes())
            oralab.write_json(REG,dict(pins=pins(),scope='NON-PHYSICS305-role graph plus4native refusals; no valid producers',
                child=dict(memory_mib=512,cpu=60,wall=90,processes=3),
                parent=dict(memory_mib=768,cpu=300,wall=600,processes=4),evidence_mib=768,controller_mib=8))
    elif sys.argv[1]=='execute':
        with oralab.lock():
            assert pins()==json.loads(REG.read_bytes())['pins']
            b=Budget(LAB/'runs'/(TAG+'-controller-20261015'),dict(raw=6*M,failure=2*M),8*M)
            n=run([sys.executable,'-B',str(Path(__file__)),'worker',oralab.sha(LAB/'state/operator.lock')],
                Limits(memory_bytes=768*M,cpu_seconds=300,wall_seconds=600,processes=4),cwd=DEV)
            with b.create('raw','native.json') as f:f.write(enc(n))
            b.write_snapshot('failure');assert native_ok(n),n['output'];print(n['output'])
    else:worker(sys.argv[2])
