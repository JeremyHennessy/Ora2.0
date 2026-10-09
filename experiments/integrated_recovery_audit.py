"""Independent ISOLATION-04 byte/state audit; no launcher/worker/driver imports."""
import argparse
import hashlib
import json
from pathlib import Path
from experiments import isolation_resource_audit as previous

FILES=(*previous.FILES,'experiments/integrated_recovery.py','experiments/integrated_recovery_worker.py',
       'experiments/integrated_recovery_audit.py','docs/ISOLATION-04-CONTRACT.md')
require=previous.require; sha=previous.sha; tree=previous.tree; replay=previous.replay


def audit(output,source,revision):
    output,source=Path(output),Path(source); data=json.loads((output/'evidence.json').read_bytes())
    require(data['schema']=='isolation04-v1' and data['revision']==revision,'Exact source identity')
    require(set(data['source_sha256'])==set(FILES) and all(sha(source/p)==v for p,v in data['source_sha256'].items()),'Complete source binding')
    require(tree(output/'runtime')==data['runtime_sha256'],'Runtime hash binding')
    for name in (*replay.FILES,'experiments/__init__.py','experiments/isolation_resource_worker.py'):
        require(sha(output/'runtime'/name)==sha(source/name),'Exact world/pressure copies')
    require(sha(output/'runtime/integrated_worker.py')==sha(source/'experiments/integrated_recovery_worker.py'),'Fixed adapter')
    profiles=data['profiles']; require(len(profiles)==8 and len({p['sid'] for p in profiles.values()})==8,'Distinct profiles')
    require(all(p['deleted'] is True and p['cleanup_hresult']==0 for p in profiles.values()) and 0<data['elapsed_seconds']<300,'Cleanup / bounded horizon')
    cases={'ordinary','confined'}|{kind+'-'+suffix for kind in ('cpu','memory','wall') for suffix in ('resource','io','direct','ungranted','wrong-sid','restored')}
    require(len(data['rows'])==40 and {(r['trial'],r['case']) for r in data['rows']}=={(t,k) for t in range(2) for k in cases},'Complete frozen matrix')
    rows={(r['trial'],r['case']):r for r in data['rows']}
    references={t:replay.inspect(output/f'{t}-ordinary/world',revision) for t in range(2)}
    def inspected(path):
        before=tree(path); result=replay.inspect(path,revision)
        require(tree(path)==before,'Read-only audit changed world'); return result
    def equivalent(result,t):
        ref=references[t]
        require(result['manifest']==ref['manifest'] and result['states']==ref['states'],'Complete identity/state/ancestry/RNG/cursor equality')
        require([f['event'] for f in result['frames'] if f['event'] is not None]==[f['event'] for f in ref['frames'] if f['event'] is not None],'Complete event history equality')
        require(len(result['states'])==33 and result['report']['reported_status']=='stopped' and result['report']['checkpoint_current'] is True,'Finite complete history')
    for index,row in enumerate(data['rows']):
        t,case=row['trial'],row['case']; path=output/row['workspace']
        require(path.resolve().is_relative_to(output.resolve()) and row['resumed'] is True and row['stopped'] is True,'Fixed path / kernel start and stop')
        expected=dict(is_appcontainer=False,capabilities=0,package_sid=None) if case=='ordinary' else dict(is_appcontainer=True,capabilities=0,package_sid=profiles[row['profile']]['sid'])
        require(row['token']==expected,'Actual token binding')
        for key in ('job_before','job_after'):
            caps=row[key]
            require(caps['configured_memory_bytes']==128*1024**2 and caps['configured_cpu_ticks']==50_000_000 and caps['configured_processes']==(2 if case=='ordinary' else 1) and caps['flags'] & 0x220c==0x220c,'Unchanged native caps')
        if case.endswith(('-ungranted','-wrong-sid')):
            require(row['exit_code']==2 and not row['world_started'] and row['world_before']==row['world_after']==tree(path/'before-new-resume'),'Permission rejection / immutable restore')
            require('error' not in row and row['elapsed_seconds']<10,'Actual denied worker exit')
        elif case.endswith('-resource'):
            kind=case.split('-')[0]; marker=json.loads((path/'pressure.json').read_bytes())
            amount={'cpu':7,'memory':256*1024**2,'wall':12}[kind]
            require(marker==dict(case=kind,tick=5,kind=kind,requested=amount,completed=False,memory_denied=kind=='memory'),'Real targeted resource request')
            require(row['exit_code'] in ({124,1816} if kind=='cpu' else {42} if kind=='memory' else {124}),'Resource exit')
            if kind!='memory':
                require(caps['user_cpu_seconds']>=4.8 if kind=='cpu' else caps['user_cpu_seconds']<5,'CPU versus wall causality')
                if row['exit_code']==124: require(row['termination_reason']==kind,'Supervisor cause')
            require(row['elapsed_seconds']<10 if kind!='wall' else 10<=row['elapsed_seconds']<12,'Resource deadline')
            state=inspected(path/'before-resource-resume')
            require(state['report']['verified_simulation_tick']==5 and not state['report']['checkpoint_current'],'Durable resource boundary')
        elif case.endswith('-io'):
            require(row['exit_code']==2 and 'error' not in row and row['elapsed_seconds']<10,'I/O writer rejected')
        elif case=='cpu-direct':
            require(row['exit_code']==2 and row['world_before']==row['world_after']==tree(path/'before-io-resume'),'Partial tail rejected without mutation')
            before=tree(path/'before-io-resume')
            try: replay.inspect(path/'before-io-resume',revision)
            except ValueError: pass
            else: raise ValueError('Partial journal accepted')
            require(tree(path/'before-io-resume')==before,'Corruption check mutated input')
        else:
            require(row['exit_code']==0 and 'error' not in row and row['elapsed_seconds']<10,'Reference or continuation exit')
            require(row['world_started'],'Expected worker marker'); equivalent(inspected(path/'world'),t)
            if case.endswith('-restored'):
                require(row['profile']==f'{t}-{case.split("-")[0]}-new' and index>=profiles[f'{t}-original']['deleted_at_launch'],'New identity after original profile deletion')
                observed=previous.independent.observed(path/'world',revision)[1]
                require(observed==row['observation'],'Recorded read-only telemetry')
                require((path/'world/frames.jsonl').read_bytes().startswith((path/'before-new-resume/frames.jsonl').read_bytes()),'Restored durable prefix lost')
    for t in range(2):
        ref=references[t]
        require(ref['manifest']['identity']['world_id']==f'isolation04-trial-{t}','Stable world identity')
        for kind,io in (('cpu','journal'),('memory','pending'),('wall','replace')):
            path=output/f'{t}-{kind}'; trusted=inspected(path/'trusted-snapshot')
            require(trusted['report']['verified_simulation_tick']==7 and trusted['states']==ref['states'][:8],'Trusted tick-seven complete state')
            require((path/'trusted-snapshot/frames.jsonl').read_bytes().startswith((path/'before-resource-resume/frames.jsonl').read_bytes()),'Resource prefix lost at I/O continuation')
            target=(path/'target-frame.json').read_bytes(); frame=replay.decode(target)
            trace=json.loads((path/'io-fault.json').read_bytes())
            require(trace==dict(kind=io,tick=8,injections=1,payload_size=len(target),payload_sha256=hashlib.sha256(target).hexdigest()),'Exactly one fault payload')
            require(frame['reason']=='advanced' and frame['state']==ref['states'][8],'Target state eight')
            raw=(path/'trusted-snapshot/frames.jsonl').read_bytes()
            require(frame['previous_sha256']==trusted['frames'][-1]['frame_sha256'] and frame['frame_sha256']==replay.digest({k:v for k,v in frame.items() if k!='frame_sha256'}),'Payload chain integrity')
            damaged=path/'before-io-resume'
            require((damaged/'manifest.json').read_bytes()==(path/'trusted-snapshot/manifest.json').read_bytes(),'Manifest identity at failure')
            require((damaged/'frames.jsonl').read_bytes()==raw+(target[:len(target)//2] if io=='journal' else target),'Exact fault byte reconstruction')
            require((damaged/'checkpoint.json').read_bytes()==(path/'trusted-snapshot/checkpoint.pending').read_bytes(),'Last committed checkpoint seven')
            if io!='journal':
                require((damaged/'checkpoint.pending').read_bytes()==target,'Pending frame eight')
                require(inspected(damaged)['states']==ref['states'][:9],'Fault-time valid state eight')
            restored=output/f'{t}-{kind}-restored'
            source_copy=path/('trusted-snapshot' if io=='journal' else 'before-io-resume')
            require(tree(restored/'before-new-resume')==tree(source_copy),'Exact restored inputs; no replacement genesis')
    return dict(schema='isolation04-audit-v1',launch_cases=40,world_histories=16,resource_stops=6,storage_faults=6,
        unchanged_partial_tail_rejections=2,exact_direct_continuations=4,permission_rejections=12,
        exact_new_identity_restorations=6,profiles_cleaned=8,states_per_complete_history=33,
        read_only_recorded_observations=True,evidence_sha256=sha(output/'evidence.json'),
        physical_power_loss=False,real_disk_fault=False,production_security_verified=False,unattended_world=False,scientific_progress=False)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('output-dir','source-dir','source-revision'): p.add_argument('--'+name,required=True)
    a=p.parse_args()
    try: print(json.dumps(audit(a.output_dir,a.source_dir,a.source_revision),indent=2))
    except (ValueError,OSError,KeyError,TypeError) as error: print('Rejected:',error); raise SystemExit(2)
