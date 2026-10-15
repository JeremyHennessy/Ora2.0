"""Bounded changed-test portability check; no World or fresh target execution."""
import ast
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile
import oralab

LAB=Path('D:/OraLab');DEV=LAB/'src/Ora2.0-recording82';M=1024**2
sys.path.insert(0,str(DEV))
from experiments.evidence_budget import Budget
from experiments.process_limits import Limits,run
from experience75_controller_core import native_ok,enc,fill_reserved
TAG='credited-fallback87-ci-portability-v1';ROOT=LAB/'runs'/(TAG+'-20261015')
REG=LAB/'reports'/(TAG+'-registration.json');WORKER=LAB/'tools/credited_fallback87_portable_worker_v1.py'
tree=ast.parse((LAB/'tools/qualify_credited_fallback87v2_binding_v2.py').read_bytes())
FILES=ast.literal_eval(next(n.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='FILES' for t in n.targets)))
OLD=[LAB/'runs/credited-fallback87-source-prepared-v1-20261015/raw/original/tests/test_digital_credited_fallback87_source.py',
     LAB/'runs/credited-fallback87-v2-binding-prepared-v2-20261015/raw/original/tests/test_digital_credited_fallback87v2_binding.py']
def gitbytes(name):return subprocess.check_output(['git','-C',str(DEV),'show',':'+name])
def spec(path):return dict(path=str(path),extent=path.stat().st_size,sha256=oralab.sha(path))
def sources():return {variant:{name:__import__('hashlib').sha256((DEV/name).read_bytes() if variant=='original' else gitbytes(name)).hexdigest() for name in FILES} for variant in ('original','git-lf')}
def pins():return {str(p):oralab.sha(p) for p in [Path(__file__),WORKER,*OLD,
 LAB/'tools/oralab.py',LAB/'tools/experience75_controller_core.py',DEV/'experiments/evidence_budget.py',
 LAB/'reports/credited-fallback87-ci-portability-qualification-v1-20261015.md',
 LAB/'reports/credited-fallback87-ci-38777587737-failed.log',
 LAB/'reports/credited-fallback87-source-prepared-v1.json',LAB/'reports/credited-fallback87-v2-binding-prepared-v2.json']}

def worker(owner):
    reg=json.loads(REG.read_bytes());assert reg['pins']==pins() and reg['sources']==sources()
    assert oralab.sha(LAB/'state/operator.lock')==owner
    budget=Budget(ROOT,{p:32*M for p in ('raw','archive','restore','failure')},128*M)
    results=[];error=None
    def save(phase,name,data,reserve=0):
        with budget.create(phase,name,reserve=reserve) as f:f.write(data)
    try:
        save('raw','registration.json',REG.read_bytes())
        for i,path in enumerate(reg['pins']):save('raw','owners/'+str(i)+'-'+Path(path).name,Path(path).read_bytes())
        for variant in reg['sources']:save('raw',variant+'-native.json',b'',M)
        blob=io.BytesIO()
        with zipfile.ZipFile(blob,'w',zipfile.ZIP_DEFLATED) as z:
            for variant in reg['sources']:
                for name in FILES:
                    raw=(DEV/name).read_bytes() if variant=='original' else gitbytes(name)
                    if variant=='original':save('raw','original/'+name,raw)
                    z.writestr(variant+'/'+name,raw)
                z.writestr(variant+'/prepared_worker.py',WORKER.read_bytes())
            save('raw','original/prepared_worker.py',WORKER.read_bytes())
        assert len(blob.getvalue())<=M;save('archive','source.zip',blob.getvalue())
        with zipfile.ZipFile(io.BytesIO(blob.getvalue())) as z:
            for name in z.namelist():save('restore',name,z.read(name))
        for name in FILES+['prepared_worker.py']:
            assert (ROOT/'raw/original'/name).read_bytes()==(ROOT/'restore/original'/name).read_bytes()
        for name in FILES:
            a=(ROOT/'raw/original'/name).read_bytes();b=(ROOT/'restore/git-lf'/name).read_bytes()
            if name.endswith('.py'):assert ast.dump(ast.parse(a))==ast.dump(ast.parse(b))
            elif name.endswith('.md'):assert a.decode('utf-8').splitlines()==b.decode('utf-8').splitlines()
        for variant in reg['sources']:
            save('raw',variant+'-request.json',enc(dict(source_files={**reg['sources'][variant],'prepared_worker.py':oralab.sha(WORKER)},
                old_source_test=spec(OLD[0]),old_binding_test=spec(OLD[1]))))
        for variant in reg['sources']:
            path=ROOT/('raw/original' if variant=='original' else 'restore/git-lf')
            native=run([sys.executable,'-B','prepared_worker.py',str(ROOT/'raw'/(variant+'-request.json'))],
                Limits(memory_bytes=384*M,cpu_seconds=15,wall_seconds=30,processes=3),cwd=path)
            fill_reserved(ROOT,variant+'-native.json',enc(native),M)
            assert native_ok(native),native['output'];results.append(json.loads(native['output']))
        assert results[0]==results[1] and pins()==reg['pins'] and sources()==reg['sources']
    except BaseException as exc:error=exc
    finally:
        save('failure','outcome.json',enc(dict(error=None if error is None else repr(error),results=results)))
        budget.write_snapshot('failure')
        members=sorted(p for phase in ('raw','failure') for p in (ROOT/phase).rglob('*') if p.is_file())
        assert sum(p.stat().st_size for p in members)<16*M
        blob=io.BytesIO()
        with zipfile.ZipFile(blob,'w',zipfile.ZIP_STORED) as z:
            for p in members:z.writestr(p.relative_to(ROOT).as_posix(),p.read_bytes())
        save('archive','evidence.zip',blob.getvalue())
        with zipfile.ZipFile(io.BytesIO(blob.getvalue())) as z:
            for name in z.namelist():
                raw=z.read(name);assert raw==(ROOT/name).read_bytes();save('restore','readback/'+name,raw)
        budget.write_snapshot('failure','final-budget.json')
        oralab.write_json(LAB/'reports'/(TAG+'.json'),dict(passed=error is None,worlds=0,targets=0,
            changed_methods=2,reused_other_source_groups=5,distinct_ci_source_fixtures=True,
            live_source_normalization=False,source_archive_readback=error is None,
            evidence_archive_sha256=oralab.sha(ROOT/'archive/evidence.zip'),evidence_exact_readback=True,
            error=None if error is None else repr(error),results=results,pins=reg['pins'],sources=reg['sources']))
    if error:raise error
    print('Two changed CI methods pass exact Windows and GitLF exports;0Worlds/targets; no live source normalization.')

if __name__=='__main__':
    if sys.argv[1]=='register':
        with oralab.lock():
            assert not REG.exists() and not ROOT.exists() and shutil.disk_usage(LAB).free>=136*M
            assert sum(Path(p).stat().st_size for p in pins())<12*M
            assert sum((DEV/n).stat().st_size+len(gitbytes(n)) for n in FILES)+2*WORKER.stat().st_size<2*M
            oralab.write_json(REG,dict(pins=pins(),sources=sources(),scope='Two changed CI methods only; distinct byte-pinned fixtures;0Worlds/targets',
                child=dict(memory_mib=384,cpu=15,wall=30,processes=3),parent=dict(memory_mib=512,cpu=120,wall=240,processes=4)))
    elif sys.argv[1]=='execute':
        with oralab.lock():
            reg=json.loads(REG.read_bytes());assert reg['pins']==pins() and reg['sources']==sources()
            budget=Budget(LAB/'runs'/(TAG+'-controller-20261015'),dict(raw=6*M,failure=2*M),8*M)
            native=run([sys.executable,'-B',str(Path(__file__)),'worker',oralab.sha(LAB/'state/operator.lock')],
                Limits(memory_bytes=512*M,cpu_seconds=120,wall_seconds=240,processes=4),cwd=DEV)
            with budget.create('raw','native.json') as f:f.write(enc(native))
            budget.write_snapshot('failure');assert native_ok(native),native['output'];print(native['output'])
    else:worker(sys.argv[2])
