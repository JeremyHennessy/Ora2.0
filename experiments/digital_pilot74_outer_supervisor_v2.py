"""UNQUALIFIED bounded outer custody source. No automatic execution entrypoint.

No registration, qualification or launch is authorized by importing this file.
Outer closure is separate from the inner archive and never edits inner evidence.
"""
import os,sys,time,traceback
from pathlib import Path
from experiments import digital_pilot74_publication_reader_v2 as physical
from experiments import digital_pilot74_parent_ledger_v2 as ledger
from experiments import digital_pilot74_available_archive_v2 as available
from experiments import digital_pilot74_native_observed_v2 as native
from experiments import digital_pilot74_finite_inventory_v2 as inventory
from experiments import digital_pilot74_source_exports_v2 as exports
from experiments import process_limits as caps
MIB=1024**2
ROLE='parent'

def enc(value):return physical.encode(value)
def sha(raw):return physical.digest(raw)

def source_bound(r):
    root=Path(r['source_root']);pins=r['source_files']
    assert not sys.flags.optimize and root.is_absolute()
    assert Path(__file__).resolve()==root/'experiments/digital_pilot74_outer_supervisor_v2.py'
    assert sha(enc(pins))==r['source_sha256']
    rows=exports.rows(root,pins)
    for name,module in list(sys.modules.items()):
        if name=='experiments' or name.startswith('experiments.'):
            path=Path(module.__file__).resolve();relative=path.relative_to(root).as_posix()
            assert relative in pins and physical.digest(path.read_bytes())==pins[relative]
    return rows

def control_plan(rows):
    # This allowance is separate from raw/failure/archive/restore phases.
    leaves={'raw/stdout/parent.bin':MIB,'failure/native-first-output.bin':2*MIB,
      'registration.json':65536,'capture-grant.json':65536,'native.json':256*1024,
      'first-exception.json':128*1024,'available-partials.json':512*1024,
      'receipt.json':256*1024,'source-manifest.json':65536,'budget.json':65536}
    for row in rows:leaves['source/'+row['name']]=row['extent']
    assert len(leaves)<=1024 and sum(leaves.values())<=8*MIB
    return leaves

def precharge(root,leaves,slots):
    # slots is populated progressively so initialization failure cannot erase it.
    assert not root.exists();root.mkdir()
    for name,limit in leaves.items():
        path=root/name;path.parent.mkdir(parents=True,exist_ok=True)
        for parent in path.parents:physical.plain(parent,True)
        fd=os.open(path,os.O_CREAT|os.O_EXCL|os.O_RDWR|getattr(os,'O_BINARY',0))
        try:
            info=os.fstat(fd);assert info.st_size==0
            slots[name]=dict(path=str(path),limit=limit,device=info.st_dev,inode=info.st_ino)
            os.fsync(fd)
        finally:os.close(fd)

def partials(r,rows,deadline):
    """Only named raw/failure leaves. No recursion, new role, replay or archive."""
    plan=inventory.plan(rows);root=Path(r['root']);records=[]
    for phase in ('raw','failure'):
        for row in plan[phase]:
            if time.monotonic()>=deadline:raise TimeoutError('Outer custody deadline; existing partials retained without a complete inventory')
            path=root/phase/row['name']
            try:
                info=physical.plain(path)
            except FileNotFoundError:
                records.append(dict(name=phase+'/'+row['name'],missing=True));continue
            # Hash bounded available partials; unexpected excess is disclosed.
            if info.st_size>row['limit']:
                records.append(dict(name=phase+'/'+row['name'],extent=info.st_size,over_limit=True));continue
            records.append(dict(name=phase+'/'+row['name'],extent=info.st_size,device=info.st_dev,inode=info.st_ino,content_not_reaudited=True))
    assert len(records)<=1024
    return dict(schema='PILOT74-OUTER-AVAILABLE-PARTIALS-v2',files=records,inner_archive_completion_unknown=True)

def supervise(spec,expected_sha):
    """Future externally reviewed caller supplies exact separate registration pin.

    Existing owner lock must already be held. Never create/delete/replace it.
    Actual external review ancestry remains a prerequisite beyond these checks.
    """
    raise RuntimeError('Python outer topology REFUSED; separately admitted native guardian required')
    started=time.monotonic();cpu_started=time.process_time()
    assert spec['sha256']==expected_sha
    raw=physical.external(spec,65536);r=physical.parse(raw,65536)
    rows=source_bound(r)
    assert r['schema']=='PILOT74-FINITE-REGISTRATION-v2' and r['mode']=='finite_qualification'
    assert Path(r['python']['path']).resolve()==Path('D:/OraLab/tools/Python312/python.exe').resolve()==Path(sys.executable).resolve()
    physical.external(r['python'],16*MIB)
    inner=Path(r['root']);assert inner.is_absolute() and inner.resolve().is_relative_to(Path('D:/OraLab/runs').resolve()) and not inner.exists()
    control=inner.with_name(inner.name+'-controller');leaves=control_plan(rows)
    slots={};first=None;later=[];result=None;worker=None;accepted=False
    def save(name,value):return ledger.write_empty(slots[name],enc(value))
    try:
        precharge(control,leaves,slots)
        ledger.write_empty(slots['registration.json'],raw)
        save('source-manifest.json',dict(source_sha256=r['source_sha256'],files=r['source_files']))
        for row in rows:
            value=physical.external(dict(path=str(Path(r['source_root'])/row['name']),extent=row['extent'],sha256=row['sha256']),MIB)
            ledger.write_empty(slots['source/'+row['name']],value)
        save('budget.json',dict(schema='PILOT74-OUTER-BUDGET-v2',leaves=leaves,charged=sum(leaves.values()),ceiling=8*MIB))
        command=[r['python']['path'],'-B','-m','experiments.digital_pilot74_parent_worker_v2',slots['registration.json']['path'],str(len(raw)),sha(raw)]
        capture=dict(version='PILOT74-PARENT-CAPTURE-GRANT-v2',root=str(control),source_sha256=r['source_sha256'],configuration_sha256=r['configuration_sha256'],role=ROLE,command_sha256=sha(enc(command)),operator_lock=r['operator_lock'],raw=slots['raw/stdout/parent.bin'],overflow=slots['failure/native-first-output.bin'])
        save('capture-grant.json',capture)
        remaining=3600-(time.monotonic()-started);assert remaining>0
        limits=caps.Limits(memory_bytes=2048*MIB,cpu_seconds=2400,wall_seconds=remaining,processes=4)
        result=native.run_parent(command,limits,r['source_root'],capture_grant=capture,capture_seal=sha(enc(capture)),source_sha256=r['source_sha256'],configuration_sha256=r['configuration_sha256'],role=ROLE)
        # Exact output is in the physical capture, never duplicate it into JSON.
        record={k:v for k,v in result.items() if k!='output'}
        save('native.json',record)
        assert result['exit_code']==0 and result['timed_out'] is False and result['supervisor_cpu_stop'] is False and result['post_close_processes_exited'] is True and result['usage']['active_before_close']==0
        c=result['stdout_capture'];assert c['capture_complete'] is True and c['eof'] is True and c['errors']==[] and c['stdout_limit_exceeded'] is False and c['overflow']['extent']==0
        output=physical.external(c['raw'],MIB);assert output.endswith(b'\n') and output.count(b'\n')==1
        worker=physical.parse_host(output[:-1],MIB)
        assert worker['schema']=='PILOT74-PARENT-WORKER-RESULT-v2' and worker['registration_sha256']==sha(raw) and worker['source_sha256']==r['source_sha256']
        assert worker['owner'] in result['observed_job_processes']
        proof=worker['archive'];assert proof['evidence_complete'] is True and proof['available_files_exactly_restored'] is True
        archive=proof['archive'];assert Path(archive['path'])==inner/'archive/complete.zip'
        actual=available.scan(archive['path'],1280*MIB)
        assert all(actual[k]==archive[k] for k in ('extent','sha256'))
        assert worker['publication_accepted'] is False and worker['live_attachment'] is False
        source_bound(r);accepted=True
    except BaseException as error:
        first=error
        try:
            save('first-exception.json',dict(first_exception=repr(first),traceback=''.join(traceback.format_exception(first)),inner_complete_archive_claimed=False))
        except BaseException as failure:later.append('first-exception retention: '+repr(failure))
        try:save('available-partials.json',partials(r,rows,started+3600))
        except BaseException as failure:later.append('available partial inventory: '+repr(failure))
    # No inner mutation, retry, archival retry, lock deletion or replacement.
    cpu=time.process_time()-cpu_started
    job_cpu=None if result is None else result['usage']['user_cpu_seconds']
    wall=time.monotonic()-started
    accounted=job_cpu is not None and cpu+job_cpu<=2400 and wall<=3600
    receipt=dict(schema='PILOT74-OUTER-CLOSURE-v2',registration_sha256=expected_sha,source_sha256=r['source_sha256'],parent_job_closed=False if result is None else result['post_close_processes_exited'],inner_archive_and_restore_attested=accepted and accounted,outer_available_evidence_only=not(accepted and accounted),first_exception=None if first is None else repr(first),custody_errors=later,worker=worker,outer_cpu_seconds=cpu,parent_job_cpu_seconds=job_cpu,total_accounted_cpu_seconds=None if job_cpu is None else cpu+job_cpu,wall_seconds=wall,resource_accounting_within_frozen_ceilings=accounted,unified_host_confinement_proven=False,publication_accepted=False,live_attachment=False)
    # Receipt write is terminal; its own interruption cannot authenticate success.
    try:save('receipt.json',receipt)
    except BaseException as terminal:
        if first is not None:
            first.add_note('Outer terminal receipt unavailable: '+repr(terminal))
            raise first
        raise
    if first is not None:raise first
    assert accepted and accounted and not later
    return receipt
