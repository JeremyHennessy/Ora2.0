"""Finite26-role request/custody builders, no native launch or World imports."""
from pathlib import Path
from experiments import digital_pilot74_parent_ledger_v2 as ledger
from experiments import digital_pilot74_publication_reader_v2 as physical
from experiments import digital_pilot74_available_archive_v2 as custody
CONFIG=dict(version='DIGITAL-PILOT74-NATIVE-qualification-v1',seeds=[3],cuts=[8192,9216,10240],horizon=10240,mode='faithful',inheritance_mode='parent_copy',fuel_mode='renewed',dose=8,software_only=True)
CUTS=(8192,9216,10240)

class Requests:
    def __init__(self,root,slots,revision,pins,source_rows,operator_lock):
        self.root=Path(root);self.slots=slots;self.revision=revision;self.pins=pins;self.source_rows=source_rows;self.operator_lock=operator_lock
        assert self.root.is_absolute() and self.root.resolve().is_relative_to(Path('D:/OraLab/runs').resolve())
        assert type(revision) is str and len(revision)==40 and all(c in '0123456789abcdef' for c in revision)
        self.source_sha=ledger.digest(ledger.encode(pins));self.config_sha=ledger.digest(ledger.encode(CONFIG))
        self.identity=dict(revision=revision,source_sha256=self.source_sha,config_sha256=self.config_sha,law='DIGITAL-PILOT74-FINITE-QUALIFICATION-v1')
    def common(self):return dict(configuration=CONFIG,revision=self.revision,source_files=self.pins,source_sha256=self.source_sha,configuration_sha256=self.config_sha)
    def spec(self,name,cap):
        slot=self.slots['raw/'+name];assert slot['limit']<=cap
        p=Path(slot['path']);i=physical.plain(p);assert 0<i.st_size<=slot['limit'] and (i.st_dev,i.st_ino)==(slot['device'],slot['inode'])
        actual=custody.scan(p,slot['limit'])
        assert (actual['device'],actual['inode'])==(slot['device'],slot['inode'])
        spec={k:actual[k] for k in ('path','extent','sha256')};physical.external(spec,cap);return spec
    def grant(self,name,role):return ledger.grant(self.slots['raw/'+name],self.root,name,self.source_sha,self.config_sha,role)
    def task(self,export,kind,cut=None):
        assert export in ('original','restored') and kind in ('generate','audit','resume')
        assert cut is None if kind=='generate' else type(cut) is int and cut in CUTS
        role=f'{export}:3:{kind}'+('' if cut is None else ':'+str(cut));request=dict(self.common(),seed=3,export=export,kind=kind,cut=cut,role=role)
        if kind=='generate':
            inputs={};outputs={str(c):self.grant(f'data/{export}/capsule{c}.json',role+':'+str(c)) for c in CUTS}
        else:
            inputs=dict(capsule=self.spec(f'data/{export}/capsule{cut}.json',40*1024**2))
            if kind=='resume':inputs.update(audit=self.spec(f'data/{export}/audit{cut}.json',128*1024),reference=self.spec(f'data/{export}/capsule10240.json',40*1024**2))
            outputs=dict(main=self.grant(f'data/{export}/{kind}{cut}.json',role))
        request.update(inputs=inputs,outputs=outputs);return request
    def readiness(self,export):
        assert export in ('original','restored');role=export+'/prepared'
        return dict(self.common(),schema='PILOT74-SOURCE-READINESS-REQUEST-v2',export=export,role=role,source_rows=self.source_rows,operator_lock=self.operator_lock,output=self.grant('receipts/'+role+'.json',role))
    def journal(self,kind,fault,initial_receipt):
        assert kind in ('crash','recover','sequence') and fault in ('partial','orphan','committed','normal') and (kind!='sequence' or fault=='normal')
        role='normal-sequence' if kind=='sequence' else kind+'/'+fault
        prefix='journal/'+('sequence' if kind=='sequence' else fault)+'/'
        names=['head.json','head.pending','observation.json','payload.pending','capsule-2.json','capsule-3.json']+(['capsule-1.json'] if kind=='sequence' else ['recovery.json'])
        outputs={}
        for name in names:
            slot=self.slots['raw/'+prefix+name];outputs[name]={k:slot[k] for k in ('limit','device','inode')}
        inputs={}
        for cut in CUTS:
            inputs['cut'+str(cut)]=self.spec(f'data/original/capsule{cut}.json',40*1024**2)
            inputs['audit'+str(cut)]=self.spec(f'data/original/audit{cut}.json',128*1024)
        endpoint=dict(self.common(),identity=self.identity,kind=kind,fault=fault,role=role,directory=str(self.root/'raw'/prefix),inputs=inputs,outputs=outputs)
        grant=dict(schema='PILOT74-OBSERVED-ENDPOINT-GRANT-v2',role=role,source_sha256=self.source_sha,configuration_sha256=self.config_sha,endpoint_sha256=ledger.digest(ledger.encode(endpoint)),initial_commit_sha256=initial_receipt['sha256'],operator_lock=self.operator_lock)
        return dict(endpoint=endpoint,initial_commit=initial_receipt,owner_grant=grant),ledger.digest(ledger.encode(grant))
    def inherit_recovery(self,fault,native,observation_spec,expected_command):
        """Use actual previous commit time/head, never utc() or a fresh commit."""
        assert fault in ('partial','orphan','committed','normal') and native['command']==expected_command
        assert native['exit_code']==(0 if fault=='normal' else 78) and native['post_close_processes_exited'] is True and native['usage']['active_before_close']==0
        assert native['timed_out'] is False and native['output_truncated'] is False and native['stdout_limit_exceeded'] is False and native['stdout_capture']['capture_complete'] is True
        o=physical.parse(physical.external(observation_spec,16384),16384)
        assert o['role']=='crash/'+fault and o['identity']==self.identity and o['counts']==dict(genesis=0,steps=1024,hydrates=1)
        assert o['forbidden_calls']==dict(genesis=0,prefix=0,restore=0) and o['exact_final_and_events'] is True
        assert all(type(v) is int for v in o['counts'].values()) and all(type(v) is int for v in o['forbidden_calls'].values())
        owner=o['owner'];assert type(owner['pid']) is int and type(owner['creation_filetime']) is int
        producer=dict(pid=owner['pid'],creation_filetime_decimal=str(owner['creation_filetime']))
        assert owner['actual_self_query'] is True and producer in native['observed_job_processes'] and owner['pid'] in native['owned_pids_before_close']
        expected_cut=9216 if fault in ('partial','orphan') else 10240
        assert o['loaded_tick']==9216 and o['executed_tick']==10240 and o['authoritative_tick']==expected_cut and o['lost_instructions']==10240-expected_cut
        commit=o['commit_history'][-1];assert commit['tick']==expected_cut
        physical.timestamp(commit['committed_at']);assert physical.timestamp(commit['committed_at'])<=physical.timestamp(o['observed_at'])
        raw=commit['head_ascii'].encode('ascii');p=self.root/'raw'/'journal'/fault/'head.json'
        actual,identity=physical.read_exact(p,dict(extent=len(raw),sha256=ledger.digest(raw)),16384)
        assert actual==raw and identity[:2]==(commit['device'],commit['inode'])
        receipt=dict(schema='PILOT74-INITIAL-COMMIT-RECEIPT-v2',role='recover/'+fault,identity=self.identity,commit=commit)
        return ledger.write_empty(self.slots['raw/metadata/initial-commit/recover/'+fault+'.json'],ledger.encode(receipt))
    def closed(self,registration_spec):
        role='closed-projection-publication-audit'
        return dict(self.common(),schema='PILOT74-CLOSED-AUDIT-REQUEST-v2',role=role,registration=registration_spec,output=self.grant('receipts/'+role+'.json',role),operator_lock=self.operator_lock)
