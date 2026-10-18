"""Closed historical publication composition; no producer, writer or VM import.

External registered native/parent/grant execution ancestry is a trust premise.
This role verifies bytes, literal physics and recorded provenance; it cannot
manufacture that ancestry from publisher checksums. Source-only, unqualified.
"""
from pathlib import Path
from experiments import digital_pilot74_publication_reader_v2 as physical
from experiments import digital_pilot74_projection_referee_v2 as literal
MIB=1024**2
CUTS={1:8192,2:9216,3:10240}

def encoded(v):return physical.encode(v)
def digest(v):return physical.digest(v)
def read(spec,cap):return physical.external(spec,cap)
def value(spec,cap):return physical.parse(read(spec,cap),cap)

def refs(head):
    assert type(head) is dict and set(head)=={'schema','identity','sequence'}|{k+'_'+f for k in ('status','process','audit','event_manifest') for f in ('name','extent','sha256')}
    assert head['schema']=='ora-pilot-publication-head-v2'
    seq=physical.integer(head['sequence'],1,3)
    result={}
    for kind in ('status','process','audit','event_manifest'):
        name=('manifest' if kind=='event_manifest' else kind)+'.'+format(seq,'06d')+'.json'
        assert head[kind+'_name']==name
        result[name]=dict(extent=physical.integer(head[kind+'_extent'],1,16384),sha256=physical.checksum(head[kind+'_sha256']))
    return result

def capsule(spec,audit_spec,source,seq):
    raw=read(spec,40*MIB);cap=physical.parse(raw,40*MIB)
    ar=read(audit_spec,128*1024);proof=physical.parse(ar,128*1024)
    assert set(cap)=={'version','identity','checkpoint64','state','state_sha256'} and cap['version']=='DIGITAL-PILOT74-STATE-data-v1' and cap['identity']==source
    assert type(cap['state']['tick']) is int and cap['state']['tick']==CUTS[seq]
    assert cap['state_sha256']==digest(encoded(cap['state']))
    assert proof['version']=='DIGITAL-PILOT74-AUDIT-v1' and proof['verified'] is True and proof['engineering_only'] is True and proof['stage_credit'] is False
    assert proof['identity']==source and type(proof['extent']) is int and proof['extent']==len(raw) and proof['capsule_sha256']==digest(raw)
    assert proof['state_sha256']==cap['state_sha256'] and type(proof['tick']) is int and proof['tick']==CUTS[seq]
    return dict(state_sha256=cap['state_sha256'],capsule_sha256=digest(raw),extent=len(raw),audit_sha256=digest(ar))

def audit(root,registration):
    """ONE registered closed role; no World, entropy, publication or repair."""
    r=registration
    assert type(r) is dict and set(r)=={'schema','final','observation','initial_commit','publications','cuts'}
    assert r['schema']=='PILOT74-CLOSED-PUBLICATION-REGISTRATION-v2'
    final=r['final'];assert final['sequence']==3 and final['mode']=='recorded'
    root=Path(root);result=physical.read_publication(root,final)
    # Capture CURRENT physical identities, not fabricated historical head paths.
    phraw,phid=physical.read_exact(root/'head.json',final['head'],16384)
    whspec=final['world']['head'];whraw,whid=physical.read_exact(whspec['path'],{k:whspec[k] for k in ('extent','sha256')},16384)
    source=final['source_identity'];identity=final['identity']
    authority=final['process_authority'];assert authority['kind']=='stopped' and authority['observation']==r['observation']
    observation_raw=read(r['observation'],16384);observation=physical.parse(observation_raw,16384)
    assert observation['role']=='normal-sequence' and observation['identity']==source
    assert type(observation['counts']) is dict and all(type(v) is int for v in observation['counts'].values())
    assert type(observation['forbidden_calls']) is dict and all(type(v) is int for v in observation['forbidden_calls'].values())
    assert observation['counts']==dict(genesis=0,steps=2048,hydrates=1) and observation['forbidden_calls']==dict(genesis=0,prefix=0,restore=0)
    for key,expected in [('loaded_tick',8192),('executed_tick',10240),('authoritative_tick',10240),('lost_instructions',0)]:
        assert type(observation[key]) is int and observation[key]==expected
    assert observation['exact_final_and_events'] is True and observation['software_only'] is True and observation['stage_credit'] is False
    physical.timestamp(observation['observed_at'])
    initial_raw=read(r['initial_commit'],16384);initial=physical.parse(initial_raw,16384)
    assert initial['schema']=='PILOT74-INITIAL-COMMIT-RECEIPT-v2' and set(initial)=={'schema','role','identity','commit'}
    assert initial['role']=='normal-sequence' and initial['identity']==source and observation['initial_commit_sha256']==digest(initial_raw)
    history=observation['commit_history'];assert type(history) is list and len(history)==3 and history[0]==initial['commit']
    assert type(r['cuts']) is dict and set(r['cuts'])=={'1','2','3'}
    cuts={};last_time=None
    for seq in (1,2,3):
        c=r['cuts'][str(seq)];assert type(c) is dict and set(c)=={'capsule','audit'}
        cuts[seq]=capsule(c['capsule'],c['audit'],source,seq)
        h=history[seq-1];assert type(h) is dict and set(h)=={'head_ascii','committed_at','device','inode','tick'}
        assert type(h['head_ascii']) is str and type(h['device']) is int and type(h['inode']) is int and type(h['tick']) is int and h['tick']==CUTS[seq]
        time=physical.timestamp(h['committed_at']);assert last_time is None or time>=last_time;last_time=time
        head=physical.parse(h['head_ascii'].encode('ascii'),16384)
        assert set(head)=={'version','sequence','tick','identity','payload_name','extent','sha256','audit_sha256'} and head['version']=='DIGITAL-PILOT74-COMMIT-v1'
        assert head['identity']==source and type(head['sequence']) is int and head['sequence']==seq and type(head['tick']) is int and head['tick']==CUTS[seq]
        assert head['payload_name']==f'capsule-{seq}.json' and head['extent']==cuts[seq]['extent'] and head['sha256']==cuts[seq]['capsule_sha256'] and head['audit_sha256']==cuts[seq]['audit_sha256']
    assert history[2]['head_ascii'].encode('ascii')==whraw and (history[2]['device'],history[2]['inode'])==whid[:2]
    assert history[2]['committed_at']==final['world']['committed_at']
    assert last_time<=physical.timestamp(observation['observed_at'])
    assert r['cuts']['1']==final['initial']
    assert r['cuts']['3']=={k:final['world'][k] for k in ('capsule','audit')}
    assert type(r['publications']) is list and len(r['publications'])==3
    rows=[]
    for seq,spec in enumerate(r['publications'],1):
        assert type(spec) is dict and set(spec)=={'grant','receipt','files'}
        grant_raw=read(spec['grant'],32768);grant=physical.parse(grant_raw,32768)
        receipt=value(spec['receipt'],65536)
        assert grant['version']=='PILOT74-PUBLICATION-WRITE-GRANT-v2' and grant['role']=='pilot74:owner-publication'
        assert Path(grant['root'])==root and grant['source_sha256']==source['source_sha256'] and grant['configuration_sha256']==source['config_sha256']
        assert receipt['schema']=='PILOT74-PUBLICATION-WRITE-RECEIPT-v2' and receipt['grant_sha256']==digest(grant_raw)
        assert type(receipt['sequence']) is int and receipt['sequence']==seq and receipt['publication_accepted'] is False and receipt['live_attachment'] is False
        rows.append((spec,grant,receipt))
    assert rows[0][2]['previous_head_ascii']==''
    final_manifest=physical.parse(result['projection_files']['manifest.000003.json'],16384)
    previous_head_raw=b'';last_published=None
    for seq,(spec,grant,receipt) in enumerate(rows,1):
        head_raw=rows[seq][2]['previous_head_ascii'].encode('ascii') if seq<3 else phraw
        head=physical.parse(head_raw,16384);assert head['identity']==identity and head['sequence']==seq
        if seq==3:assert (receipt['head']['device'],receipt['head']['inode'])==phid[:2]
        assert receipt['head']['name']=='head.json' and receipt['head']['extent']==len(head_raw) and receipt['head']['sha256']==digest(head_raw)
        assert receipt['previous_head_ascii'].encode('ascii')==previous_head_raw
        before=grant['head_before'];assert before['extent']==len(previous_head_raw) and before['sha256']==digest(previous_head_raw)
        if seq>1:
            previous=rows[seq-2][2]
            assert (before['device'],before['inode'])==(previous['head']['device'],previous['head']['inode'])
            assert grant['slots']['head.pending']['device']==previous['pending']['device'] and grant['slots']['head.pending']['inode']==previous['pending']['inode']
        refs_for_head=refs(head);files={}
        assert type(spec['files']) is dict
        for name,d in spec['files'].items():
            physical.basename(name);cap=65536 if name=='initial.000001.json' else MIB if name.startswith('events.') else 16384
            files[name]=physical.read_exact(root/name,d,cap)[0]
            stored=receipt['files'][name];assert stored['name']==name and stored['extent']==len(files[name]) and stored['sha256']==digest(files[name])
            assert (stored['device'],stored['inode'])==(grant['slots'][name]['device'],grant['slots'][name]['inode'])
        assert set(receipt['files'])==set(files)
        for name,d in refs_for_head.items():assert name in files and len(files[name])==d['extent'] and digest(files[name])==d['sha256']
        mfname=f'manifest.{seq:06d}.json';mf=physical.parse(files[mfname],16384)
        expected=dict(final_manifest,sequence=seq,last_tick=CUTS[seq],chunks=final_manifest['chunks'][:(seq-1)*8])
        assert mf==expected
        expected_names={'initial.000001.json','genesis.000001.json'}|{f'events.000001.{i:04d}.json' for i in range(1,(seq-1)*8+1)}|set(refs_for_head)
        assert set(files)==expected_names
        for name in expected_names-set(refs_for_head):assert files[name]==result['projection_files'][name]
        status=physical.parse(files[f'status.{seq:06d}.json'],16384)
        process=physical.parse(files[f'process.{seq:06d}.json'],16384)
        audit_row=physical.parse(files[f'audit.{seq:06d}.json'],16384)
        assert set(status)=={'schema','mode','live_attachment','identity','sequence','published_at','start_tick','end_tick','committed','observation','process_status'}
        assert type(status['sequence']) is int and type(status['start_tick']) is int and type(status['end_tick']) is int
        assert type(audit_row['sequence']) is int
        assert status['identity']==identity and status['sequence']==seq and status['schema']=='ora-pilot-status-v1' and status['mode']=='recorded' and status['live_attachment'] is False
        assert status['start_tick']==8192 and status['end_tick']==10240 and status['process_status']=='stopped'
        assert status['committed']==dict(tick=CUTS[seq],state_sha256=cuts[seq]['state_sha256'],at=history[seq-1]['committed_at'])
        assert status['observation']==final['owner_observation']==dict(tick=10240,at=observation['observed_at'])
        pub=physical.timestamp(status['published_at']);assert last_published is None or pub>=last_published;last_published=pub
        assert physical.timestamp(observation['observed_at'])<=pub
        physical.check_process(process,authority,identity,seq)
        assert audit_row==dict(schema='ora-pilot-publication-audit-v2',identity=identity,sequence=seq,status_sha256=digest(files[f'status.{seq:06d}.json']),world_journal_head_sha256=digest(history[seq-1]['head_ascii'].encode('ascii')),committed_capsule_sha256=cuts[seq]['capsule_sha256'],committed_literal_audit_sha256=cuts[seq]['audit_sha256'],process_sha256=digest(files[f'process.{seq:06d}.json']),event_manifest_sha256=digest(files[mfname]),scope='committed_literal_with_owner_reported_observation',verified_at=audit_row['verified_at'])
        assert physical.timestamp(history[seq-1]['committed_at'])<=physical.timestamp(audit_row['verified_at'])<=pub
        previous_head_raw=head_raw
    assert last_published==physical.timestamp(result['published_at'])
    inputs=result['raw_inputs']
    def authority_for(c):return {k:{f:c[k][f] for f in ('extent','sha256')} for k in ('capsule','audit')}
    proof=literal.verify_projection(inputs['initial_capsule'],inputs['initial_audit'],inputs['terminal_capsule'],inputs['terminal_audit'],result['projection_files'],source_identity=source,identity=identity,initial_authority=authority_for(r['cuts']['1']),terminal_authority=authority_for(r['cuts']['3']),mode='recorded',boundary_state_sha256={CUTS[s]:cuts[s]['state_sha256'] for s in (1,2,3)})
    # Final rereads after the full expensive work; original open identities bind.
    end,identity_after=physical.read_exact(root/'head.json',final['head'],16384);assert end==phraw and identity_after==phid
    end,identity_after=physical.read_exact(whspec['path'],{k:whspec[k] for k in ('extent','sha256')},16384);assert end==whraw and identity_after==whid
    return dict(schema='PILOT74-CLOSED-PUBLICATION-PROOF-v2',physical_integrity=True,projection_verified=True,historical_sequences=[1,2,3],literal=proof,registration_sha256=digest(encoded(r)),external_native_and_parent_ancestry_required=True,worlds_constructed=0,vm_steps=0,publication_accepted=False,live_attachment=False,stage_credit=False)
