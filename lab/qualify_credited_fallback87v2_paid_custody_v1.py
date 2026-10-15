"""Finite source-only qualification: exact exports, no Worlds or fresh targets."""
import ast
import io
import json
import shutil
import sys
import zipfile
from pathlib import Path
import oralab

LAB=Path('D:/OraLab');DEV=LAB/'src/Ora2.0-recording82';M=1024**2
sys.path.insert(0,str(DEV))
from experiments.evidence_budget import Budget
from experiments.process_limits import Limits,run
from experience75_controller_core import native_ok,enc,fill_reserved
TAG='credited-fallback87v2-paid-controller-prepared-v1'
REG=LAB/'reports'/(TAG+'-registration.json');ROOT=LAB/'runs'/(TAG+'-20261015')
WORKER=LAB/'tools/credited_fallback87v2_paid_custody_worker_v1.py'
import runpy
PARENT=DEV/'lab/run_credited_fallback87v2_paid_v1.py'
FILES=sorted(runpy.run_path(str(PARENT))['FILES'])
def pins():
    paths=[DEV/n for n in FILES]+[Path(__file__),WORKER,
      LAB/'tools/oralab.py',LAB/'tools/experience75_controller_core.py',
      LAB/'tools/credited_fallback87v2_paid_provenance_v1.py',
      LAB/'tools/cognitive76_controller_core_v2.py',
      LAB/'reports/credited-fallback87v2-paid-custody-qualification-v1-20261015.md',
      LAB/'reports/credited-fallback87-paid-integration-contract-v2-20261015.md',
      LAB/'reports/credited-fallback87-ci-portability-v1.json',
      LAB/'reports/credited-fallback87-source-prepared-v1.json',
      LAB/'reports/credited-fallback87-v2-binding-prepared-v2.json']
    return {str(p):oralab.sha(p) for p in paths}

def worker(owner):
    registration=json.loads(REG.read_bytes())
    assert pins()==registration['pins'] and oralab.sha(LAB/'state/operator.lock')==owner
    budget=Budget(ROOT,{p:32*M for p in ('raw','archive','restore','failure')},128*M)
    results=[];error=None
    def save(phase,name,data,reserve=0):
        with budget.create(phase,name,reserve=reserve) as f:f.write(data)
    try:
        save('raw','registration.json',REG.read_bytes())
        for i,name in enumerate(sorted(registration['pins'])):
            save('raw','owners/'+str(i)+'-'+Path(name).name,Path(name).read_bytes())
        for label in ('original','restored'):save('raw',label+'-native.json',b'',M)
        source=io.BytesIO()
        with zipfile.ZipFile(source,'w',zipfile.ZIP_DEFLATED) as z:
            for name in FILES:
                raw=(DEV/name).read_bytes();save('raw','original/'+name,raw);z.writestr(name,raw)
            raw=WORKER.read_bytes();save('raw','original/prepared_worker.py',raw);z.writestr('prepared_worker.py',raw)
        assert len(source.getvalue())<=M
        save('archive','source.zip',source.getvalue())
        with zipfile.ZipFile(io.BytesIO(source.getvalue())) as z:
            for name in z.namelist():save('restore','restored/'+name,z.read(name))
        for name in FILES+['prepared_worker.py']:
            assert (ROOT/'raw/original'/name).read_bytes()==(ROOT/'restore/restored'/name).read_bytes()
        for label in ('original','restored'):
            save('raw',label+'-request.json',enc(dict(source_files={
                **{n:oralab.sha(DEV/n) for n in FILES},'prepared_worker.py':oralab.sha(WORKER)})))
        for label,path in (('original',ROOT/'raw/original'),('restored',ROOT/'restore/restored')):
            native=run([sys.executable,'-B','prepared_worker.py',str(ROOT/'raw'/(label+'-request.json'))],
                Limits(memory_bytes=384*M,cpu_seconds=15,wall_seconds=30,processes=3),cwd=path)
            fill_reserved(ROOT,label+'-native.json',enc(native),M)
            assert native_ok(native),native['output']
            results.append(json.loads(native['output']))
        assert results[0]==results[1] and pins()==registration['pins']
    except BaseException as e:error=e
    finally:
        save('failure','outcome.json',enc(dict(error=None if error is None else repr(error),results=results)))
        budget.write_snapshot('failure')
        members=sorted(p for phase in ('raw','failure') for p in (ROOT/phase).rglob('*') if p.is_file())
        assert sum(p.stat().st_size for p in members)<16*M
        bundle=io.BytesIO()
        with zipfile.ZipFile(bundle,'w',zipfile.ZIP_STORED) as z:
            for p in members:z.writestr(p.relative_to(ROOT).as_posix(),p.read_bytes())
        save('archive','evidence.zip',bundle.getvalue())
        with zipfile.ZipFile(io.BytesIO(bundle.getvalue())) as z:
            for name in z.namelist():
                raw=z.read(name);assert raw==(ROOT/name).read_bytes()
                save('restore','evidence-readback/'+name,raw)
        budget.write_snapshot('failure','final-budget.json')
        oralab.write_json(LAB/'reports'/(TAG+'.json'),dict(passed=error is None,
            checks=results[0]['checks'] if results else 0,worlds=0,targets=0,
            paid_physics_qualified=False,source_archive_exact_readback=error is None,
            evidence_archive_sha256=oralab.sha(ROOT/'archive/evidence.zip'),
            evidence_archive_exact_readback=True,results=results,pins=registration['pins'],
            error=None if error is None else repr(error)))
    if error:raise error
    print('Six new22-role custody checks pass both exact exports;0Worlds/targets;paid physics not yet admitted.')

if __name__=='__main__':
    if sys.argv[1]=='register':
        with oralab.lock():
            assert not REG.exists() and not ROOT.exists() and shutil.disk_usage(LAB).free>=136*M
            from credited_fallback87v2_paid_provenance_v1 import verify
            verify()
            assert sum(Path(p).stat().st_size for p in pins())<12*M
            assert sum((DEV/n).stat().st_size for n in FILES)+WORKER.stat().st_size<2*M
            for name in FILES:
                if name.endswith('.py'):ast.parse((DEV/name).read_bytes())
            oralab.write_json(REG,dict(pins=pins(),scope='Source-only; no World, step or fresh label evaluation',
                child=dict(memory_mib=384,cpu=15,wall=30,processes=3),
                parent=dict(memory_mib=512,cpu=120,wall=240,processes=4),evidence_mib=128,controller_mib=8))
    elif sys.argv[1]=='execute':
        with oralab.lock():
            assert pins()==json.loads(REG.read_bytes())['pins']
            budget=Budget(LAB/'runs'/(TAG+'-controller-20261015'),dict(raw=6*M,failure=2*M),8*M)
            native=run([sys.executable,'-B',str(Path(__file__)),'worker',oralab.sha(LAB/'state/operator.lock')],
                Limits(memory_bytes=512*M,cpu_seconds=120,wall_seconds=240,processes=4),cwd=DEV)
            with budget.create('raw','native.json') as f:f.write(enc(native))
            budget.write_snapshot('failure');assert native_ok(native),native['output'];print(native['output'])
    else:worker(sys.argv[2])
