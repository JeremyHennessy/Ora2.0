"""Finite21-role software custody qualification, then separately registered69-role science.

Run only in the approved D:/OraLab layout; the public lab copy is byte-identical.
No valid scientific role is launched without complete software/CI/custody gates.
"""
import ast,json,os,shutil,sys,zipfile
from pathlib import Path
LAB=Path('D:/OraLab');DEV=LAB/'src/Ora2.0-recording82';M=1024**2
sys.path.insert(0,str(LAB/'tools'));sys.path.insert(0,str(DEV))
import oralab
from experiments.digital_cognitive76_child import REQUIRED
from experiments.evidence_budget import Budget
from experiments.evidence_write_grant68 import seal
from experiments.process_limits import Limits,run
from experiments.digital_revision84_child import CONFIG,PREPARED
from experiments.digital_revision84_plan import plan,capacity,required_raw,pipeline
from experiments.digital_revision84_custody import open_reserved,mirror_limits
from cognitive76_controller_core_v2 import enc,sha,fill_reserved,retain_native,native_ok

PUBLIC=DEV/'lab/run_revision84_panel_v1.py'
FILES={n:DEV/n for n in REQUIRED|{'experiments/digital_memory80.py',
 'experiments/digital_memory80_recording.py','experiments/digital_recording82_reader.py',
 'experiments/digital_latehistory78_source.py','experiments/digital_revision84_source.py',
 'experiments/digital_revision84_world.py','experiments/digital_revision84_referee.py',
 'experiments/digital_revision84_metrics.py','experiments/digital_revision84_acceptance.py',
 'experiments/digital_revision84_child.py','experiments/digital_revision84_plan.py',
 'experiments/digital_revision84_custody.py','tests/test_digital_revision84_controller.py',
 'lab/run_revision84_panel_v1.py'}}
BASE_OWNERS=[Path(__file__),LAB/'tools/oralab.py',LAB/'tools/cognitive76_controller_core_v2.py',
 LAB/'reports/revision84-prospective-contract-v1-20261015.md',
 LAB/'reports/revision84-whole-custody-qualification-contract-v1-20261015.md',
 LAB/'reports/revision84-source-prepared-v2.json',LAB/'reports/revision84-paid-prepared-v1.json',
 LAB/'reports/revision84-interpretation-prepared-v2.json']

def read(path):return json.loads(path.read_bytes())
def spec(path):return dict(path=str(path),extent=path.stat().st_size,sha256=oralab.sha(path))
def configuration(phase):return PREPARED if phase=='prepared' else CONFIG
def paths(phase):
    tag='revision84-whole-'+phase+'-v1'
    return LAB/'runs'/(tag+'-20261015'),LAB/'reports'/(tag+'-registration.json'),LAB/'reports'/(tag+'.json')
def ci_path(phase):
    # Head-specific immutable receipts preserve every earlier CI binding.
    head=oralab.git(DEV,'rev-parse','HEAD')
    return LAB/'reports'/('revision84-'+('whole' if phase=='prepared' else 'scientific')+'-source-ci-'+head[:12]+'.json')
def owners(phase):return BASE_OWNERS+[ci_path(phase)]+([paths('prepared')[2]] if phase=='science' else [])
def pins(phase):return {str(p):oralab.sha(p) for p in list(FILES.values())+owners(phase)}
def check(reg,phase):assert pins(phase)==reg['pins']

def gate(phase):
    assert PUBLIC.read_bytes()==Path(__file__).read_bytes()
    ci=read(ci_path(phase));assert ci['passed'] and ci['conclusion']=='success'
    assert ci['source_head']==oralab.git(DEV,'rev-parse','HEAD')
    for name,key in (('revision84-source-prepared-v2.json','passed'),
                     ('revision84-paid-prepared-v1.json','verified'),
                     ('revision84-interpretation-prepared-v2.json','passed')):
        proof=read(LAB/'reports'/name);assert proof[key]
        for path,value in proof['pins'].items():assert oralab.sha(Path(path))==value
    assert sha((LAB/'reports/revision84-prospective-contract-v1-20261015.md').read_bytes())==CONFIG['contract_sha256']
    if phase=='science':
        proof=read(paths('prepared')[2]);assert proof['verified'] and proof['native_calls']==21
        assert proof['negative_requests_rejected']==4 and proof['scientific_worlds']==0 and proof['archive_exact']
        assert proof['source_files']=={name:oralab.sha(p) for name,p in FILES.items()}
        # Prepared CI/registration are immutable; science gets its own exact CI.
        for path,value in proof['pins'].items():assert oralab.sha(Path(path))==value
    assert required_raw(CONFIG)<3584*M

def census(metric_specs):
    totals={};strata=[]
    for source in metric_specs:
        data=read(Path(source['path']));assert data['verified']
        for row in data['records']:
            key=row['role']+'/'+row['control']
            target=totals.setdefault(key,{k:0 for k in ('ticks','decisions','successes','deaths',
                'paid_cost','captured_energy','cap_heat','failed_packet_heat','retained_operating_surplus')})
            for k in target:target[k]+=row[k]
        own=next(r['own'] for r in data['records'] if r['role']=='learner8' and r['control']=='intact')
        before=own['personally_observed_initial'];after=own['personally_observed_later']
        full=set(before)==set(after)=={str(k) for k in range(8)}
        changed=[k for k in range(8) if str(k) in before and str(k) in after and before[str(k)]!=after[str(k)]]
        strata.append(dict(seed=data['seed'],map_observation_complete=full,
            observed_changed_cues=changed,observed_unchanged_cues=[k for k in range(8)
                if str(k) in before and str(k) in after and before[str(k)]==after[str(k)]],
            observed_initial=before,observed_later=after,unobserved_targets_queried=False))
    return dict(source_control_totals=totals,strata=strata)

def worker(phase,owner):
    root,registration,report=paths(phase);reg=read(registration);check(reg,phase)
    assert oralab.sha(LAB/'state/operator.lock')==owner
    cfg=configuration(phase);source_files={n:oralab.sha(p) for n,p in FILES.items()}
    ss=sha(enc(source_files));cs=sha(enc(cfg));raw={};payloads={};negative_names=[]
    def fixed(name,data):assert name not in raw;raw[name]=len(data);payloads[name]=data
    fixed('registration.json',registration.read_bytes())
    for name,p in FILES.items():
        fixed('original/'+name,p.read_bytes())
        raw['restored/'+name]=p.stat().st_size
    for p in owners(phase):fixed('owners/'+p.name,p.read_bytes())
    source_zip_bound=sum(p.stat().st_size for p in FILES.values())+1024*len(FILES)+4096
    raw['source.zip']=source_zip_bound
    for role in plan(cfg):
        stem=role.replace(':','-')
        raw['data/'+stem+'.json']=capacity(role)
        raw['native/'+stem+'.json']=M;raw['request/'+stem+'.json']=64*1024
    for number in range(4):
        raw[f'native/refused{number}.json']=M;raw[f'request/refused{number}.json']=64*1024
    failure={'outcome.json':4*M,'budget.json':4*M}
    limits=mirror_limits(raw,failure);assert limits['raw']<=required_raw(cfg)
    b=Budget(root,limits,12032*M);error=None;calls=0;negatives=0;launched=[];complete={}
    # Precharge every file INCLUDING archive and every restoration slot, not
    # only the generators. Nothing new is created after the first native role.
    for name,size in raw.items():
        with b.create('raw',name,reserve=size):pass
    for name,size in failure.items():
        with b.create('failure',name,reserve=size):pass
    with b.create('archive','complete.zip',reserve=limits['archive']):pass
    for prefix,entries in (('raw',raw),('failure',failure)):
        for name,size in entries.items():
            with b.create('restore',prefix+'/'+name,reserve=size):pass
    try:
        for name,data in payloads.items():fill_reserved(root,name,data,raw[name])
        with open_reserved(b,'raw','source.zip') as stream:
            with zipfile.ZipFile(stream,'w',zipfile.ZIP_STORED) as z:
                for name in FILES:z.write(root/'raw/original'/name,name)
        with zipfile.ZipFile(root/'raw/source.zip') as z:
            for name in FILES:
                fill_reserved(root,'restored/'+name,z.read(name),raw['restored/'+name])
        assert all(oralab.sha(root/'raw'/export/name)==value
            for export in ('original','restored') for name,value in source_files.items())
        slots={}
        # Files already precharged: seal the identical grant description without
        # calling Budget.create again or changing its physical inode.
        from experiments.evidence_write_grant68 import plain,digest
        for role in plan(cfg):
            name='data/'+role.replace(':','-')+'.json';path=root/'raw'/name;info=plain(path)
            grant=dict(version='sharedlineage68-file-grant-candidate-v1',root=str(root),phase='raw',
                name=name,limit=capacity(role),source_sha=ss,config_sha=cs,role=role,device=info.st_dev,inode=info.st_ino)
            slots[role]=(grant,digest(grant))
        def native_role(req,stem,expected_failure=False):
            nonlocal calls
            fill_reserved(root,'request/'+stem+'.json',enc(req),64*1024)
            native=run([sys.executable,'-B','-m','experiments.digital_revision84_child',str(root/'raw/request'/(stem+'.json'))],
                Limits(memory_bytes=512*M,cpu_seconds=60,wall_seconds=90,processes=3),
                cwd=root/'raw'/('restored' if req['role'].startswith('restored:') else 'original'))
            calls+=1;fill_reserved(root,'native/'+stem+'.json',enc(native),M)
            if expected_failure:
                assert native['exit_code']!=0 and not native['timed_out'] and not native['output_truncated']
                assert native['post_close_processes_exited'] and native['usage']['active_before_close']==0
                assert '"rejected_before_world":true' in native['output']
            else:assert native_ok(native),native['output']
            return native
        first=plan(cfg)[0];grant,signature=slots[first]
        base=dict(configuration=cfg,source_files=source_files,source_sha=ss,config_sha=cs,
            role=first,kind='generate',input=None,grant=grant,seal=signature)
        for number,field in enumerate(('role','configuration','source_sha','seal')):
            req=json.loads(json.dumps(base))
            if field=='role':req['role']='original:1009400:generate'
            elif field=='configuration':req['configuration']['horizon']=512
            else:req[field]='0'*64
            native_role(req,'refused'+str(number),True)
            assert (root/'raw'/grant['name']).stat().st_size==0;negatives+=1
        def launch(role,inputs):
            grant,signature=slots[role];stem=role.replace(':','-');kind=role.split(':')[-1]
            req=dict(configuration=cfg,source_files=source_files,source_sha=ss,config_sha=cs,
                role=role,kind=kind,input=inputs,grant=grant,seal=signature)
            launched.append(role);native=native_role(req,stem)
            out=json.loads(native['output']);assert out['role']==role and out['source_sha']==ss and out['config_sha']==cs
            path=root/'raw'/grant['name'];receipt=out['receipt']
            assert receipt['extent']==path.stat().st_size and receipt['sha256']==oralab.sha(path)
            assert receipt['grant_sha256']==signature
            value=read(path);assert path.read_bytes()==enc(value)
            if kind=='generate':
                assert value['error'] is None and len(value['records'])==18
                assert value['scientific_worlds']==(0 if phase=='prepared' else 18)
            else:
                assert value['verified'] and value['evidence_inputs']==inputs
            complete[role]=spec(path)
            check(reg,phase);return spec(path)
        result=pipeline(cfg,launch)
        interpretation=read(Path(result['final']['path']))
        summary=census(result['metrics'])
        assert calls==(21 if phase=='prepared' else 69) and negatives==4
    except BaseException as exc:error=exc;result=None;interpretation=None;summary=None
    finally:
        outcome=dict(error=None if error is None else repr(error),native_calls=calls,
            launched_roles=launched,complete_roles=complete,negative_requests_rejected=negatives)
        data=enc(outcome);assert len(data)<=4*M
        with open_reserved(b,'failure','outcome.json') as stream:stream.write(data)
        with open_reserved(b,'failure','budget.json') as stream:stream.write(enc(b.snapshot()))
        names=['raw/'+n for n in raw]+['failure/'+n for n in failure]
        with open_reserved(b,'archive','complete.zip') as stream:
            with zipfile.ZipFile(stream,'w',zipfile.ZIP_STORED) as z:
                for name in names:z.write(root/name,name)
        with zipfile.ZipFile(root/'archive/complete.zip') as z:
            for name in names:
                with open_reserved(b,'restore',name) as dest:
                    with z.open(name) as src:
                        while True:
                            chunk=src.read(M)
                            if not chunk:break
                            dest.write(chunk)
        exact=all(oralab.sha(root/name)==oralab.sha(root/'restore'/name) for name in names);assert exact
        originals=sum(r.startswith('original:') and r.endswith(':generate') for r in complete)
        replays=sum(r.startswith('restored:') and r.endswith(':generate') for r in complete)
        report_data=dict(verified=error is None,phase=phase,source_head=reg['source_head'],
            native_calls=calls,negative_requests_rejected=negatives,source_files=source_files,
            scientific_worlds=(originals+replays)*18 if phase=='science' else 0,
            logical_originals_completed=originals*18,replay_histories_completed=replays*18,
            software_only=phase=='prepared',launched_roles=launched,complete_roles=complete,
            error=None if error is None else repr(error),archive_exact=exact,
            archive_sha256=oralab.sha(root/'archive/complete.zip'),interpretation=interpretation,
            census=summary,pins=reg['pins'])
        assert len(enc(report_data))<=4*M;oralab.write_json(report,report_data)
    if error:raise error
    print('REVISION84 '+phase+' complete; originals='+str(originals*18)+'; accepted='+str(interpretation['accepted_capacities']))

if __name__=='__main__':
    action,phase=sys.argv[1:3];assert phase in ('prepared','science')
    root,registration,report=paths(phase)
    if action=='register':
        with oralab.lock():
            gate(phase);assert not root.exists() and not registration.exists()
            assert shutil.disk_usage(LAB).free>=12040*M
            for p in list(FILES.values())+owners(phase):
                if p.suffix=='.py':ast.parse(p.read_bytes())
            oralab.write_json(registration,dict(pins=pins(phase),configuration=configuration(phase),
                source_head=oralab.git(DEV,'rev-parse','HEAD'),child=dict(memory_mib=512,cpu=60,wall=90,processes=3),
                parent=dict(memory_mib=768,cpu=600 if phase=='prepared' else 6000,wall=1200 if phase=='prepared' else 9000,processes=4),
                evidence_mib=12032,controller_mib=8,required_raw_bytes=required_raw(configuration(phase))))
    elif action=='execute':
        with oralab.lock():
            gate(phase);check(read(registration),phase)
            b=Budget(LAB/'runs'/(root.name+'-controller'),dict(raw=6*M,failure=2*M),8*M)
            native=run([sys.executable,'-B',str(Path(__file__)),'worker',phase,oralab.sha(LAB/'state/operator.lock')],
                Limits(memory_bytes=768*M,cpu_seconds=600 if phase=='prepared' else 6000,
                       wall_seconds=1200 if phase=='prepared' else 9000,processes=4),cwd=DEV)
            with b.create('raw','native.json') as stream:stream.write(enc(native))
            b.write_snapshot('failure');assert native_ok(native),native['output'];print(native['output'])
    else:
        assert action=='worker';worker(phase,sys.argv[3])
