"""Unqualified timestamped journal derivative. No import-time execution."""
import json,os,sys
from datetime import datetime,timezone
from pathlib import Path
from experiments import digital_pilot74_journal_child as retained
from experiments import digital_pilot74_journal as journal
from experiments import digital_pilot74_child as boundary
from experiments import digital_pilot74_publication_reader_v2 as physical
input_record=retained.input_record
load_without_prefix=retained.load_without_prefix
MIB=1024**2

def stamp():return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

def capture(directory,identity,committed_at):
    physical.timestamp(committed_at)
    p=Path(directory)/'head.json';raw=journal.read(p,16384)
    value=journal._head(raw,identity);info=p.lstat()
    return dict(head_ascii=raw.decode('ascii'),committed_at=committed_at,
                device=info.st_dev,inode=info.st_ino,tick=value['tick'])

def admit(wrapper,seal):
    assert type(wrapper) is dict and set(wrapper)=={'endpoint','initial_commit','owner_grant'}
    request=wrapper['endpoint'];grant=wrapper['owner_grant']
    assert type(grant) is dict and set(grant)=={'schema','role','source_sha256','configuration_sha256','endpoint_sha256','initial_commit_sha256','operator_lock'}
    assert grant['schema']=='PILOT74-OBSERVED-ENDPOINT-GRANT-v2' and journal.sha(journal.enc(grant))==seal
    assert grant['role']==request['role'] and grant['source_sha256']==request['source_sha256'] and grant['configuration_sha256']==request['configuration_sha256']
    assert grant['endpoint_sha256']==journal.sha(journal.enc(request))
    assert {'experiments/digital_pilot74_journal_observed_child_v2.py','experiments/digital_pilot74_publication_reader_v2.py'}<=set(request['source_files'])
    lock=grant['operator_lock'];assert type(lock) is dict and set(lock)=={'path','extent','sha256','device','inode'}
    assert Path(lock['path'])==Path('D:/OraLab/state/operator.lock')
    raw,identity=physical.read_exact(lock['path'],{k:lock[k] for k in ('extent','sha256')},16384)
    assert type(lock['device']) is int and type(lock['inode']) is int
    assert identity[:2]==(lock['device'],lock['inode'])
    initialraw,initial=input_record(wrapper['initial_commit'],16384)
    assert journal.sha(initialraw)==grant['initial_commit_sha256']
    assert type(initial) is dict and set(initial)=={'schema','role','identity','commit'}
    assert initial['schema']=='PILOT74-INITIAL-COMMIT-RECEIPT-v2' and initial['role']==request['role'] and initial['identity']==request['identity']
    c=initial['commit'];assert type(c) is dict and set(c)=={'head_ascii','committed_at','device','inode','tick'}
    physical.timestamp(c['committed_at']);assert type(c['head_ascii']) is str
    head=journal._head(c['head_ascii'].encode('ascii'),request['identity'])
    assert type(c['tick']) is int and c['tick']==head['tick']
    assert physical.timestamp(c['committed_at'])<=physical.timestamp(stamp())
    directory,audits=retained.admit(request)
    assert capture(directory,request['identity'],c['committed_at'])==c
    return request,directory,audits,initial

def execute(request,directory,audits,initial,counts,forbidden,history):
    from experiments import digital_pilot74_loader as loader,digital_pilot74_population as kernel,digital_pressure71_population as base
    pins=request['source_files'];root=Path.cwd()
    def check():boundary.boundary.verify_source(root,pins);boundary.boundary.module_origins(root,pins)
    check()
    authority,payload,proof=journal.select(directory,request['identity'],audits)
    original_step=base.World.step
    try:
        world=load_without_prefix(base,kernel,loader,payload,request['identity'],proof,counts,forbidden)
        del payload
        cut=world.tick;creation=journal.birth(os.getpid());assert type(creation) is int and 0<creation<2**64
        owner=dict(pid=os.getpid(),creation_filetime=creation,actual_self_query=True,stale_lock_removal=False)
        def counted(w):counts['steps']+=1;return original_step(w)
        base.World.step=counted
        endpoints=(9216,10240) if request['kind']=='sequence' else (10240,)
        for endpoint in endpoints:
            while world.tick<endpoint:assert world.step(),'extinction closes qualification failed'
            terminal,reference=input_record(request['inputs']['cut'+str(endpoint)],40*MIB)
            assert world.snapshot()==reference['state']
            if request['kind'] in ('crash','sequence'):
                fault=request['fault'] if request['kind']=='crash' else 'normal'
                committed=journal.commit(directory,terminal,audits[str(endpoint)],fault,3 if endpoint==10240 else 2,audits)
                assert committed==(fault in ('committed','normal'))
                if committed:history.append(capture(directory,request['identity'],stamp()))
            del reference,terminal
        assert counts==dict(genesis=0,steps=10240-cut,hydrates=1) and not any(forbidden.values());check()
        authority,_,_=journal.select(directory,request['identity'],audits)
        observed_at=stamp()
        value=dict(observed_at=observed_at,commit_history=history,initial_commit_sha256=journal.sha(journal.enc(initial)),role=request['role'],identity=request['identity'],owner=owner,counts=counts,forbidden_calls=forbidden,loaded_tick=cut,executed_tick=10240,authoritative_tick=authority['tick'],lost_instructions=10240-authority['tick'],exact_final_and_events=True,stage_credit=False,software_only=True)
        if request['kind']=='recover':
            value['final']=world.snapshot();journal.write(directory/'recovery.json',journal.enc(value),40*MIB)
        else:journal.write(directory/'observation.json',journal.enc(value),16384)
        check()
        if request['kind']=='crash' and request['fault']!='normal':os._exit(78)
        print(journal.enc({k:v for k,v in value.items() if k!='final'}).decode())
    finally:base.World.step=original_step
    check()

def main():
    counts=dict(genesis=0,steps=0,hydrates=0);forbidden=dict(genesis=0,prefix=0,restore=0);history=[]
    try:
        assert len(sys.argv)==5
        from experiments.digital_pilot74_custody import read_recording
        raw=read_recording(sys.argv[1],int(sys.argv[2]),sys.argv[3])
        wrapper=physical.parse(raw,MIB)
        request,directory,audits,initial=admit(wrapper,sys.argv[4])
        history.append(initial['commit'])
        execute(request,directory,audits,initial,counts,forbidden,history)
    except BaseException as error:
        print(journal.enc(dict(failed=True,first_exception=repr(error),counts=counts,forbidden_calls=forbidden,commit_history=history,unreceipted_state_unknown=True)).decode(),file=sys.stderr)
        raise

if __name__=='__main__':main()
