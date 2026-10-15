"""Finite prepared qualification; no registered World or scientific target."""
import ast,io,json,sys,unittest,zipfile,shutil
from pathlib import Path
import oralab
LAB=Path('D:/OraLab');DEV=LAB/'src/Ora2.0-recording82';M=1024**2
sys.path.insert(0,str(DEV))
from experiments.evidence_budget import Budget
from experiments.process_limits import Limits,run
from experience75_controller_core import native_ok,enc,fill_reserved
TAG='credited-fallback86-active-controller-prepared-v3';REG=LAB/'reports'/(TAG+'-registration.json');ROOT=LAB/'runs'/(TAG+'-20261015')
from run_credited_fallback86_active_v1 import FILES as PINNED
FILES=sorted(PINNED)
WORKER=LAB/'tools/credited_fallback86_active_prepared_worker_v2.py'
OLD_REPORT=LAB/'reports/credited-fallback86-active-controller-prepared-v1.json'
OLD_ARCHIVE=LAB/'runs/credited-fallback86-active-controller-prepared-v1-20261015/archive/evidence.zip'
def spec(path):return dict(path=str(path),extent=path.stat().st_size,sha256=oralab.sha(path))

def pins():return {str(p):oralab.sha(p) for p in [DEV/n for n in FILES]+[Path(__file__),WORKER,LAB/'tools/oralab.py',LAB/'tools/experience75_controller_core.py',DEV/'experiments/evidence_budget.py',LAB/'reports/credited-fallback86-active-control-contract-v1-20261015.md',LAB/'reports/credited-fallback86-control-prepared-v1.json',LAB/'tools/run_credited_fallback86_active_v1.py',LAB/'reports/credited-fallback86-active-custody-qualification-v1-20261015.md',LAB/'reports/credited-fallback86-active-custody-v2-20261015.md',LAB/'reports/credited-fallback86-active-custody-v3-20261015.md',OLD_REPORT,OLD_ARCHIVE]}

def check(r):assert pins()==r['pins']
def worker(owner):
    r=json.loads(REG.read_bytes());check(r);assert oralab.sha(LAB/'state/operator.lock')==owner
    budget=Budget(ROOT,{p:32*M for p in ('raw','archive','restore','failure')},128*M);error=None;results=[]
    def save(p,n,data,reserve=0):
        with budget.create(p,n,reserve=reserve) as stream:stream.write(data)
    try:
        save('raw','registration.json',REG.read_bytes())
        for number,name in enumerate(sorted(r['pins'])):
            path=Path(name)
            save('raw','owners/'+str(number)+'-'+path.name,path.read_bytes())
        for label in ('original','restored'):
            save('raw',label+'-native.json',b'',M)
        bundle=io.BytesIO()
        with zipfile.ZipFile(bundle,'w',zipfile.ZIP_DEFLATED) as archive:
            for name in FILES:
                data=(DEV/name).read_bytes();save('raw','original/'+name,data);archive.writestr(name,data)
            data=WORKER.read_bytes();save('raw','original/prepared_worker.py',data);archive.writestr('prepared_worker.py',data)
        save('archive','source.zip',bundle.getvalue())
        assert len(bundle.getvalue())<=2*M
        with zipfile.ZipFile(io.BytesIO((ROOT/'archive/source.zip').read_bytes())) as archive:
            for name in archive.namelist():save('restore','restored/'+name,archive.read(name))
        for name in FILES+['prepared_worker.py']:
            assert (ROOT/'raw/original'/name).read_bytes()==(ROOT/'restore/restored'/name).read_bytes()
        for label in ('original','restored'):
            save('raw',label+'-request.json',enc(dict(source_files=dict(
                {n:oralab.sha(DEV/n) for n in FILES},**{'prepared_worker.py':oralab.sha(WORKER)}),
                reuse_v1=dict(report=spec(OLD_REPORT),archive=spec(OLD_ARCHIVE)),
                original_test_path=str(DEV/'tests/test_digital_credited_fallback86_active.py'))))
        for label,path in (('original',ROOT/'raw/original'),('restored',ROOT/'restore/restored')):
            request_path=ROOT/'raw'/(label+'-request.json')
            native=run([sys.executable,'-B','prepared_worker.py',str(request_path)],Limits(memory_bytes=384*M,cpu_seconds=15,wall_seconds=30,processes=3),cwd=path)
            fill_reserved(ROOT,label+'-native.json',enc(native),M)
            assert native_ok(native),native['output']
            results.append(json.loads(native['output']))
        assert results[0]==results[1];check(r)
    except BaseException as e:error=e
    finally:
        save('failure','outcome.json',enc(dict(error=None if error is None else repr(error),results=results)))
        budget.write_snapshot('failure')
        members=sorted(p for phase in ('raw','failure') for p in (ROOT/phase).rglob('*') if p.is_file())
        assert sum(p.stat().st_size for p in members)<16*M
        evidence=io.BytesIO()
        with zipfile.ZipFile(evidence,'w',zipfile.ZIP_STORED) as archive:
            for p in members:archive.writestr(p.relative_to(ROOT).as_posix(),p.read_bytes())
        save('archive','evidence.zip',evidence.getvalue())
        with zipfile.ZipFile(io.BytesIO((ROOT/'archive/evidence.zip').read_bytes())) as archive:
            for name in archive.namelist():
                value=archive.read(name);assert value==(ROOT/name).read_bytes()
                save('restore','evidence-readback/'+name,value)
        budget.write_snapshot('failure','final-budget.json')
        oralab.write_json(LAB/'reports'/(TAG+'.json'),dict(passed=error is None,checks=results[0]['checks'] if results else 0,reused_checks=results[0]['reused_checks'] if results else 0,scientific_worlds=0,scientific_targets=0,source_archive_exact_readback=error is None,evidence_archive_sha256=oralab.sha(ROOT/'archive/evidence.zip'),evidence_archive_exact_readback=True,results=results,pins=r['pins'],error=None if error is None else repr(error)))
    if error:raise error
    print('Prepared qualification passed: '+str(results[0]['checks'])+' checks in both exact source exports; no scientific contexts.')
if __name__=='__main__':
    if sys.argv[1]=='register':
        with oralab.lock():
            assert not REG.exists() and not ROOT.exists()
            assert shutil.disk_usage(LAB).free>=136*M
            assert sum((DEV/n).stat().st_size for n in FILES)*2+WORKER.stat().st_size*2<=4*M
            assert sum(Path(p).stat().st_size for p in pins())<=2*M
            for name in FILES:
                if name.endswith('.py'):ast.parse((DEV/name).read_bytes())
            oralab.write_json(REG,dict(pins=pins(),scope='five pure scope/precharge/dependency/per-seed parity fail-stop checks; AST/data only; ZERO Worlds and target calls; no scientific admission',child=dict(memory_mib=384,cpu=15,wall=30,processes=3),parent=dict(memory_mib=512,cpu=120,wall=240,processes=4),evidence_mib=128,controller_mib=8))
    elif sys.argv[1]=='execute':
        with oralab.lock():
            check(json.loads(REG.read_bytes()));budget=Budget(LAB/'runs'/(TAG+'-controller-20261015'),dict(raw=6*M,failure=2*M),8*M)
            native=run([sys.executable,'-B',str(Path(__file__)),'worker',oralab.sha(LAB/'state/operator.lock')],Limits(memory_bytes=512*M,cpu_seconds=120,wall_seconds=240,processes=4),cwd=DEV)
            with budget.create('raw','native.json') as stream:stream.write(enc(native))
            budget.write_snapshot('failure');assert native_ok(native),native['output'];print(native['output'])
    else:worker(sys.argv[2])
