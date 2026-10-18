"""Unqualified finite26-role controller, no automatic/CLI execution entrypoint.

External reviewed registration and actual parent Job are mandatory. The outer
wall/early-hard-stop supervisor remains a distinct source/admission dependency.
"""
import ctypes,hashlib,os,shutil,sys,traceback
from pathlib import Path
from experiments import process_limits as caps
from experiments import digital_pressure71_scientific_child as source_boundary
from experiments import digital_pilot74_publication_reader_v2 as physical
from experiments import digital_pilot74_parent_ledger_v2 as ledger
from experiments import digital_pilot74_finite_requests_v2 as requests
from experiments import digital_pilot74_source_exports_v2 as exports
from experiments import digital_pilot74_native_observed_v2 as native
from experiments import digital_pilot74_available_archive_v2 as archive
MIB=1024**2
CHILD=caps.Limits(memory_bytes=1024*MIB,cpu_seconds=180,processes=3,wall_seconds=300)
GATES={'interface','custody','union_failure','source_fit','whole_source_ci'}
CONTRACT_SHA={'qualification': '4b129f2f31bb257c93476c7e434e874f7fcc105658f9d15325a675740133ec5b', 'publication': '8feccd53b883568a2e8e0311df078871d7fab010d473c1c29e9f5755d2aca759', 'observer_agreement': '16552ae599326808d683d0d23c74174529aec5da52356d087faee25bd9e78e90'}

def enc(v):return physical.encode(v)
def sha(b):return physical.digest(b)
def read(spec,cap):return physical.external(spec,cap)
def parsed(spec,cap):return physical.parse(read(spec,cap),cap)

def parent_job():
    """Query actual inherited Job; a self-authored metadata flag cannot suffice."""
    assert os.name=='nt'
    kernel=caps.kernel();value=caps.ExtendedLimits()
    caps.checked(kernel.QueryInformationJobObject(None,9,ctypes.byref(value),ctypes.sizeof(value),None))
    assert value.basic.flags & (0x4|0x8|0x200|0x2000)==(0x4|0x8|0x200|0x2000)
    assert value.job_memory==2048*MIB and value.basic.active_processes==4 and value.basic.job_cpu==2400*10_000_000
    return dict(memory_bytes=int(value.job_memory),processes=int(value.basic.active_processes),cpu_ticks=int(value.basic.job_cpu))

def registration(spec,expected_sha):
    assert spec['sha256']==expected_sha
    raw=read(spec,65536);r=physical.parse(raw,65536)
    assert type(r) is dict and set(r)=={'schema','mode','run_id','world_id','root','source_root','revision','source_files','source_sha256','configuration','configuration_sha256','python','operator_lock','contracts','reviews','compatibility'}
    assert r['schema']=='PILOT74-FINITE-REGISTRATION-v2' and r['mode']=='finite_qualification'
    assert enc(r['configuration'])==enc(requests.CONFIG) and sha(enc(r['configuration']))==r['configuration_sha256']
    for key in ('run_id','world_id'):
        text=r[key];assert type(text) is str and 1<=len(text)<=80 and text.isascii() and all(c.isalnum() or c in '-_.' for c in text)
    revision=r['revision'];assert type(revision) is str and len(revision)==40 and all(c in '0123456789abcdef' for c in revision)
    root=Path(r['root']);source_root=Path(r['source_root'])
    assert root.is_absolute() and root.resolve().is_relative_to(Path('D:/OraLab/runs').resolve()) and not root.exists()
    assert source_root.is_absolute() and Path(__file__).resolve()==source_root/'experiments/digital_pilot74_finite_controller_v2.py'
    assert source_boundary.verify_source(source_root,r['source_files'])==r['source_sha256']==sha(enc(r['source_files']))
    source_boundary.module_origins(source_root,r['source_files'])
    assert Path(r['python']['path']).resolve()==Path('D:/OraLab/tools/Python312/python.exe').resolve()==Path(sys.executable).resolve()
    read(r['python'],16*MIB)
    assert shutil.disk_usage(root.parent).free>=6*1024**3
    assert type(r['contracts']) is dict and set(r['contracts'])=={'qualification','publication','observer_agreement'}
    for kind,contract in r['contracts'].items():
        assert contract['sha256']==CONTRACT_SHA[kind];read(contract,128*1024)
    assert type(r['reviews']) is dict and set(r['reviews'])==GATES
    reviews={}
    for kind,specification in r['reviews'].items():
        review=parsed(specification,128*1024)
        assert review['schema']=='PILOT74-EXTERNAL-GATE-REVIEW-v2' and review['kind']==kind
        assert review['revision']==revision and review['source_sha256']==r['source_sha256'] and review['configuration_sha256']==r['configuration_sha256']
        assert review['verdict']=='PASS' and review['scope']=='new_pilot74_whole_source_only'
        # Exact review-file pins come from SEPARATE trusted registration. These
        # predicates alone do not authenticate the reviewer's execution origin.
        if kind=='whole_source_ci':
            assert review['head_sha']==revision and review['conclusion']=='success' and review['old_suites_rerun'] is False
        else:
            assert type(review['native_records']) is list and review['native_records'] and review['archive_restore_exact'] is True
            for item in review['native_records']:
                n=physical.parse_native(read(item,MIB),MIB)
                assert n['exit_code']==0 and n['timed_out'] is False and n['output_truncated'] is False and n['post_close_processes_exited'] is True and n['usage']['active_before_close']==0
        reviews[kind]=review
    assert type(r['compatibility']) is dict and set(r['compatibility'])=={'capsule','audit'}
    read(r['compatibility']['capsule'],24*MIB);read(r['compatibility']['audit'],128*1024)
    lock=r['operator_lock'];assert Path(lock['path'])==Path('D:/OraLab/state/operator.lock')
    _,identity=physical.read_exact(lock['path'],{k:lock[k] for k in ('extent','sha256')},16384)
    assert identity[:2]==(lock['device'],lock['inode'])
    return r,raw,reviews,parent_job()

class Controller:
    def __init__(self,r,raw,reviews,job):
        self.r=r;self.root=Path(r['root']);self.reviews=reviews;self.job=job
        self.rows=exports.rows(r['source_root'],r['source_files'])
        self.budget,self.slots,self.plan=ledger.precharge(self.root,self.rows)
        self.completed=[];self.attempted=[];self.native={};self.commands={};self.observations={};self.publications=[];self.initial={};self.finalized=False
        self.builder=requests.Requests(self.root,self.slots,r['revision'],r['source_files'],self.rows,r['operator_lock'])
        self.wire=dict(run_id=r['run_id'],world_id=r['world_id'],source_revision=r['revision'],source_manifest_sha256=r['source_sha256'],configuration_sha256=r['configuration_sha256'])
        self.save('metadata/registration.json',raw)
        self.save('metadata/configuration.json',enc(r['configuration']))
        self.save('metadata/source-pins.json',enc(r['source_files']))
        self.save('metadata/qualification-receipts.json',enc(reviews))
        self.exported=exports.export(r['source_root'],self.slots,r['source_files'],self.rows,r['revision'],r['configuration_sha256'])
        self.save('metadata/source/owners.json',enc(dict(source_root=r['source_root'],exports=self.exported,parent_job=job,operator_lock=r['operator_lock'])))
        for key in ('capsule','audit'):
            self.save('compatibility/old-'+('capsule' if key=='capsule' else 'audit')+'8192.json',read(r['compatibility'][key],24*MIB if key=='capsule' else 128*1024))
    def save(self,name,raw):return ledger.write_empty(self.slots['raw/'+name],raw)
    def spec(self,name,cap):return self.builder.spec(name,cap)
    def value(self,name,cap):return parsed(self.spec(name,cap),cap)
    def refresh(self,prefix,names):
        for name in names:
            slot=self.slots['raw/'+prefix+name];i=physical.plain(Path(slot['path']));assert i.st_size<=slot['limit']
            slot.update(device=i.st_dev,inode=i.st_ino)
    def launch(self,name,module,request,export='original',extra=()):
        index=len(self.attempted);assert index<26 and self.plan['roles'][index]['name']==name
        for root in self.exported['roots'].values():assert exports.rows(root,self.r['source_files'])==self.rows
        spec=self.save('requests/'+name+'.json',enc(request))
        command=[self.r['python']['path'],'-B',str(Path(self.exported['roots'][export])/'experiments/digital_pilot74_entrypoint_v2.py'),module,spec['path'],str(spec['extent']),spec['sha256']]+list(extra)
        capture=ledger.capture_grant(self.slots,self.root,self.r['source_sha256'],self.r['configuration_sha256'],name,command,self.r['operator_lock'])
        self.save('metadata/grants/'+name+'.json',enc(dict(request=spec,command=command,capture=capture,endpoint=request)))
        self.attempted.append(name);self.commands[name]=command
        n=native.run(command,CHILD,self.exported['roots'][export],capture_grant=capture['grant'],capture_seal=capture['seal'],source_sha256=self.r['source_sha256'],configuration_sha256=self.r['configuration_sha256'],role=name)
        self.native[name]=n;ledger.retain_native(self.slots,name,n)
        expected=self.plan['roles'][index]
        assert n['command']==command and n['limits']==vars(CHILD) and n['exit_code']==expected['exit_code'] and n['timed_out'] is False and n['supervisor_cpu_stop'] is False and n['post_close_processes_exited'] is True and n['usage']['active_before_close']==0
        assert n['stdout_capture']['grant_sha256']==capture['seal'] and n['stdout_capture']['eof'] is True and n['stdout_capture']['errors']==[]
        raw=read(self.spec('stdout/'+name+'.bin',MIB),MIB) if n['stdout_capture']['raw']['extent'] else b''
        assert raw==n['output'].encode('utf8')
        row=None
        if raw:
            assert raw.endswith(b'\n') and raw.count(b'\n')==1
            row=physical.parse_host(raw[:-1],MIB)
        return n,row
    def finish_role(self,name,counts,details,child_receipt=False):
        expected=self.plan['roles'][len(self.completed)];assert name==expected['name']
        assert type(counts) is dict and set(counts)=={'genesis','hydrates','steps'} and all(type(v) is int for v in counts.values())
        assert all(counts[k]==expected[k] for k in counts)
        receipt=dict(schema='PILOT74-FINITE-ROLE-RECEIPT-v2',name=name,counts=counts,native=self.spec('native/'+name+'.json',MIB),command=self.commands[name],details=details)
        if not child_receipt:self.save('receipts/'+name+'.json',enc(receipt))
        self.completed.append(receipt)
    def task(self,export,kind,cut=None):
        name=export+'/'+kind+('' if cut is None else str(cut));request=self.builder.task(export,kind,cut)
        n,row=self.launch(name,'digital_pilot74_child',request,export)
        assert row['role']==request['role'] and row['identity']==self.builder.identity and row['software_only'] is True and row['stage_credit'] is False
        assert all(type(v) is int and v==0 for v in row['forbidden_calls'].values())
        for label,item in request['outputs'].items():
            manifest=row['manifests'][label];grant=item['grant'];name_out=grant['name']
            assert manifest['grant_sha256']==item['seal'] and manifest['source_sha']==self.r['source_sha256'] and manifest['config_sha']==self.r['configuration_sha256'] and manifest['role']==grant['role']
            actual=self.spec(name_out,grant['limit']);assert actual['extent']==manifest['extent'] and actual['sha256']==manifest['sha256']
        c=row['counts'];counts=dict(genesis=c['genesis'],hydrates=c['hydrations'],steps=c['ordinary_steps'])
        self.finish_role(name,counts,dict(result=row,outputs={k:v['grant']['name'] for k,v in request['outputs'].items()}))
    def exported_roles(self):
        for export in ('original','restored'):
            name=export+'/prepared';request=self.builder.readiness(export)
            n,row=self.launch(name,'digital_pilot74_source_ready_v2',request,export)
            proof=self.value('receipts/'+name+'.json',128*1024)
            assert row['role']==name and proof['role']==name and proof['new_refusals']==['schema','role','configuration_sha256','source_sha256'] and proof['execution_admitted'] is False
            self.finish_role(name,dict(genesis=0,hydrates=0,steps=0),dict(proof=row),True)
            self.task(export,'generate')
            for cut in requests.CUTS:
                self.task(export,'audit',cut);self.task(export,'resume',cut)
        parity=[]
        for cut in requests.CUTS:
            a=self.spec(f'data/original/capsule{cut}.json',40*MIB);b=self.spec(f'data/restored/capsule{cut}.json',40*MIB)
            assert (a['extent'],a['sha256'])==(b['extent'],b['sha256'])
            assert read(a,40*MIB)==read(b,40*MIB);parity.append(cut)
        old=self.value('compatibility/old-capsule8192.json',24*MIB);old_audit=self.value('compatibility/old-audit8192.json',128*1024)
        new=self.value('data/original/capsule8192.json',24*MIB)
        assert old['state']==new['state'] and old['checkpoint64']==new['checkpoint64']
        assert old_audit['verified'] is True and old_audit['capsule_sha256']==self.spec('compatibility/old-capsule8192.json',24*MIB)['sha256'] and old_audit['state_sha256']==sha(enc(old['state']))
        self.save('metadata/compatibility.json',enc(dict(parity_cuts=parity,old_8192_complete_state_equal=True,old_source_identity=old['identity'],new_source_identity=new['identity'],closed_old_data_only=True,old_audit_executed=False)))
    def journal_slots(self,prefix):return {n.rsplit('/',1)[-1]:s for n,s in self.slots.items() if n.startswith('raw/'+prefix) and '/' not in n[len('raw/'+prefix):]}
    def initialize_journal(self,kind,fault):
        role='normal-sequence' if kind=='sequence' else 'crash/'+fault
        prefix='journal/'+('sequence' if kind=='sequence' else fault)+'/';cut=8192 if kind=='sequence' else 9216
        result=ledger.initial_commit(self.root/'raw'/prefix,self.journal_slots(prefix),read(self.spec(f'data/original/capsule{cut}.json',40*MIB),40*MIB),read(self.spec(f'data/original/audit{cut}.json',128*1024),128*1024),self.builder.identity,role,self.slots['raw/metadata/initial-commit/'+role+'.json'],self.r['operator_lock'])
        self.slots['raw/'+prefix+'head.json'].update(device=result['head_slot']['device'],inode=result['head_slot']['inode'])
        self.slots['raw/'+prefix+'head.pending'].update(device=result['pending_slot']['device'],inode=result['pending_slot']['inode'])
        self.initial[role]=result['spec'];return result['spec']
    def journal(self,kind,fault,initial):
        name='normal-sequence' if kind=='sequence' else kind+'/'+fault
        prefix='journal/'+('sequence' if kind=='sequence' else fault)+'/'
        wrapper,seal=self.builder.journal(kind,fault,initial)
        n,row=self.launch(name,'digital_pilot74_journal_observed_child_v2',wrapper,extra=(seal,))
        # Source-bound rename operations legitimately change logical slot inodes.
        # Validate actual authority/payload and count receipt BEFORE new grants.
        expected_tick=8192 if kind=='sequence' else 9216
        expected_authority=9216 if fault in ('partial','orphan') and kind!='sequence' else 10240
        filename='recovery.json' if kind=='recover' else 'observation.json'
        slot=self.slots['raw/'+prefix+filename];info=physical.plain(Path(slot['path']))
        assert (info.st_dev,info.st_ino)==(slot['device'],slot['inode'])
        observation=self.value(prefix+filename,40*MIB if kind=='recover' else 16384)
        assert observation['role']==name and observation['identity']==self.builder.identity and observation['exact_final_and_events'] is True
        assert all(type(v) is int and v==0 for v in observation['forbidden_calls'].values())
        assert observation['authoritative_tick']==expected_authority and observation['lost_instructions']==10240-expected_authority and observation['executed_tick']==10240
        counts=observation['counts'];assert all(type(v) is int for v in counts.values())
        if kind=='recover':
            proof=self.value('data/original/audit10240.json',128*1024)
            assert sha(enc(observation['final']))==proof['state_sha256'];del observation['final']
        else:
            assert observation['loaded_tick']==expected_tick
        assert observation['stage_credit'] is False and observation['software_only'] is True
        if n['exit_code']==0:assert row==observation
        else:assert row is None
        history=observation['commit_history'];head=physical.parse(history[-1]['head_ascii'].encode('ascii'),16384)
        assert head['identity']==self.builder.identity and head['tick']==expected_authority
        actual_head=Path(self.slots['raw/'+prefix+'head.json']['path'])
        raw,ident=physical.read_exact(actual_head,dict(extent=len(enc(head)),sha256=sha(enc(head))),16384)
        assert raw==enc(head) and ident[:2]==(history[-1]['device'],history[-1]['inode'])
        reference=self.spec('data/original/capsule'+str(expected_authority)+'.json',40*MIB)
        actual_payload=physical.plain(self.root/'raw'/prefix/head['payload_name'])
        payload_spec=dict(path=str(self.root/'raw'/prefix/head['payload_name']),extent=reference['extent'],sha256=reference['sha256'])
        read(payload_spec,40*MIB)
        from experiments import digital_pilot74_available_archive_v2 as observed_files
        empty=sha(b'')
        for pending_name in ('head.pending','payload.pending'):
            slot=self.slots['raw/'+prefix+pending_name];actual=observed_files.scan(slot['path'],slot['limit'])
            if pending_name=='payload.pending' and fault=='partial' and kind!='sequence':
                full=read(self.spec('data/original/capsule10240.json',40*MIB),40*MIB);part=full[:len(full)//2]
                assert actual['extent']==len(part) and actual['sha256']==sha(part);del full,part
            else:assert actual['extent']==0 and actual['sha256']==empty
        for sequence in ((1,2,3) if kind=='sequence' else (2,3)):
            target=prefix+'capsule-'+str(sequence)+'.json';slot=self.slots['raw/'+target];actual=observed_files.scan(slot['path'],slot['limit'])
            if sequence==3 and fault=='partial' and kind!='sequence':assert actual['extent']==0
            else:
                reference=self.spec('data/original/capsule'+str((8192,9216,10240)[sequence-1])+'.json',40*MIB)
                assert (actual['extent'],actual['sha256'])==(reference['extent'],reference['sha256'])
        self.refresh(prefix,list(self.journal_slots(prefix)))
        self.observations[name]=observation
        self.finish_role(name,dict(genesis=counts['genesis'],hydrates=counts['hydrates'],steps=counts['steps']),dict(observation=observation))
    def journals(self):
        for fault in ('partial','orphan','committed','normal'):
            initial=self.initialize_journal('crash',fault);self.journal('crash',fault,initial)
            name='crash/'+fault
            inherited=self.builder.inherit_recovery(fault,self.native[name],self.spec('journal/'+fault+'/observation.json',16384),self.commands[name])
            self.journal('recover',fault,inherited)
        self.journal('sequence','normal',self.initialize_journal('sequence','normal'))
    def publish(self):
        from experiments import digital_pilot74_projection_v2 as producer,digital_pilot74_publication_v2 as publisher
        observation=self.observations['normal-sequence'];history=observation['commit_history'];assert len(history)==3
        process_authority=dict(kind='stopped',native=self.spec('native/normal-sequence.json',MIB),observation=self.spec('journal/sequence/observation.json',16384),command=self.commands['normal-sequence'],stdout=self.spec('stdout/normal-sequence.bin',MIB))
        owner=observation['owner'];public_producer=dict(pid=owner['pid'],creation_filetime_decimal=str(owner['creation_filetime']))
        current_head=b'';final=None;publications=[];cuts={}
        initial=dict(capsule=self.spec('journal/sequence/capsule-1.json',24*MIB),audit=self.spec('data/original/audit8192.json',128*1024))
        for seq,cut in enumerate(requests.CUTS,1):
            capspec=self.spec('journal/sequence/capsule-'+str(seq)+'.json',40*MIB);auditspec=self.spec('data/original/audit'+str(cut)+'.json',128*1024)
            cuts[str(seq)]=dict(capsule=capspec,audit=auditspec)
            def just(spec):return {k:spec[k] for k in ('extent','sha256')}
            projection=producer.project(read(initial['capsule'],24*MIB),read(initial['audit'],128*1024),read(capspec,40*MIB),read(auditspec,128*1024),source_identity=self.builder.identity,identity=self.wire,initial_authority={k:just(v) for k,v in initial.items()},terminal_authority=dict(capsule=just(capspec),audit=just(auditspec)),mode='recorded')
            world_head=history[seq-1]['head_ascii'].encode('ascii');now=ledger.utc()
            process=dict(schema='ora-pilot-process-attestation-v1',identity=self.wire,sequence=seq,observed_at=observation['observed_at'],producer=public_producer,operator=None,process_status='stopped',reason='Registered producer birth observed in closed native Job; recorded only')
            publication=publisher.build(projection,world_head,read(capspec,40*MIB),read(auditspec,128*1024),process,identity=self.wire,world_authority=dict(head=dict(extent=len(world_head),sha256=sha(world_head)),capsule=just(capspec),audit=just(auditspec)),committed_at=history[seq-1]['committed_at'],observation=dict(tick=10240,at=observation['observed_at']),published_at=now,verified_at=now)
            slots={name:{k:self.slots['raw/publication/'+name][k] for k in ('limit','device','inode')} for name in publisher.slot_limits()}
            old=self.slots['raw/publication/head.json']
            grant=dict(version='PILOT74-PUBLICATION-WRITE-GRANT-v2',root=str(self.root/'raw/publication'),source_sha256=self.r['source_sha256'],configuration_sha256=self.r['configuration_sha256'],role='pilot74:owner-publication',operator_lock=self.r['operator_lock'],slots=slots,head_before=dict(extent=len(current_head),sha256=sha(current_head),device=old['device'],inode=old['inode']))
            grant_spec=self.save(f'metadata/publication/grant-{seq}.json',enc(grant))
            receipt=publisher.publish(grant,sha(enc(grant)),self.r['source_sha256'],self.r['configuration_sha256'],publication)
            receipt_spec=self.save(f'metadata/publication/receipt-{seq}.json',enc(receipt));current_head=publication['head']
            self.slots['raw/publication/head.json'].update(device=receipt['head']['device'],inode=receipt['head']['inode'])
            self.slots['raw/publication/head.pending'].update(device=receipt['pending']['device'],inode=receipt['pending']['inode'])
            files={name:dict(extent=len(raw),sha256=sha(raw)) for name,raw in publication['files'].items()}
            publications.append(dict(grant=grant_spec,receipt=receipt_spec,files=files))
            historical=dict(schema='PILOT74-HISTORICAL-PUBLICATION-INPUT-v2',identity=self.wire,sequence=seq,world_history_index=seq-1,observation=process_authority['observation'],grant=grant_spec,receipt=receipt_spec,files=files)
            if seq<3:self.save(f'metadata/publication/registration-{seq}.json',enc(historical))
            else:
                final=dict(schema='PILOT74-PUBLICATION-REGISTRATION-v2',identity=self.wire,source_identity=self.builder.identity,sequence=3,mode='recorded',head=dict(extent=len(current_head),sha256=sha(current_head)),files=files,world=dict(head=self.spec('journal/sequence/head.json',16384),capsule=capspec,audit=auditspec,committed_at=history[2]['committed_at']),initial=initial,owner_observation=dict(tick=10240,at=observation['observed_at']),process_authority=process_authority)
            del projection,publication
        closed=dict(schema='PILOT74-CLOSED-PUBLICATION-REGISTRATION-v2',final=final,observation=process_authority['observation'],initial_commit=self.initial['normal-sequence'],publications=publications,cuts=cuts)
        registration_spec=self.save('metadata/publication/registration-3.json',enc(closed))
        name='closed-projection-publication-audit';n,row=self.launch(name,'digital_pilot74_closed_audit_child_v2',self.builder.closed(registration_spec))
        proof=self.value('receipts/'+name+'.json',128*1024)
        assert proof['physical_integrity'] is True and proof['projection_verified'] is True and proof['historical_sequences']==[1,2,3]
        assert proof['publication_accepted'] is False and proof['live_attachment'] is False and proof['worlds_constructed']==proof['vm_steps']==0
        self.finish_role(name,dict(genesis=0,hydrates=0,steps=0),dict(proof=row,closed_registration=registration_spec),True)
    def finalize(self,complete,first=None):
        assert self.finalized is False;self.finalized=True
        if first is not None:
            failure=dict(schema='PILOT74-FIRST-FAILURE-v2',first_exception=repr(first),traceback=''.join(traceback.format_exception(first)),attempted=self.attempted,completed=[x['name'] for x in self.completed],unreceipted_state_unknown=True)
            ledger.write_empty(self.slots['failure/first-exception.json'],enc(failure))
        totals={k:sum(row['counts'][k] for row in self.completed) for k in ('genesis','hydrates','steps')}
        if complete:assert len(self.completed)==len(self.attempted)==26 and totals==dict(genesis=2,hydrates=15,steps=34816)
        self.save('metadata/ancestry.json',enc(dict(attempted=self.attempted,completed=self.completed,totals=totals)))
        self.save('metadata/summary.json',enc(dict(schema='PILOT74-FINITE-CONTROLLER-RESULT-v2',complete=complete,first_exception=None if first is None else repr(first),totals=totals,publication_accepted=False,live_attachment=False,scientific_acceptance=False)))
        self.save('metadata/budget-after.json',enc(self.budget.snapshot()))
        available=[]
        for phase in ('raw','failure'):
            for row in self.plan[phase]:
                slot=self.slots[phase+'/'+row['name']];i=physical.plain(Path(slot['path']))
                available.append(dict(name=phase+'/'+row['name'],extent=i.st_size,limit=slot['limit'],device=i.st_dev,inode=i.st_ino))
        ledger.write_empty(self.slots['failure/partial-inventory.json'],enc(dict(available=available,complete_run=complete)))
        return archive.archive_and_restore(self.slots,self.plan,evidence_complete=complete,allow_observed_identity_changes=not complete)

def execute_registered(spec,expected_sha):
    """Called only by separately reviewed outer supervisor, never automation text."""
    r,raw,reviews,job=registration(spec,expected_sha)
    controller=None
    try:
        controller=Controller.__new__(Controller)
        Controller.__init__(controller,r,raw,reviews,job)
        controller.exported_roles();controller.journals();controller.publish()
        return controller.finalize(True)
    except BaseException as first:
        if controller is not None and hasattr(controller,'completed') and not controller.finalized:
            try:controller.finalize(False,first)
            except BaseException as later:first.add_note('Failure custody/archive incomplete: '+repr(later))
        else:first.add_note('Outer supervisor must retain partial precharge/finalization; no inner complete archive assumed')
        raise
