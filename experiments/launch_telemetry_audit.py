"""Read-only LAUNCH-01 interpretation; no native launcher or worker imported."""
import argparse
import hashlib
import json
from pathlib import Path
from experiments import heartbeat_template_audit as replay


def require(value,reason):
    if not value:raise ValueError(reason)


def audit(folder,source,revision):
    folder,source=Path(folder),Path(source);data=json.loads((folder/'evidence.json').read_bytes())
    require(data['schema']=='launch01-v1' and data['revision']==revision,'Exact panel source')
    expected_sources=set((*replay.FILES,'experiments/isolation_capability.py','experiments/isolation_worker.py','experiments/isolation_capability_audit.py','experiments/process_limits.py','docs/ISOLATION-01-CONTRACT.md','experiments/__init__.py','experiments/world_telemetry.py','experiments/launch_telemetry.py','experiments/launch_telemetry_worker.py','experiments/launch_telemetry_audit.py','docs/LAUNCH-01-CONTRACT.md','docs/LAUNCH-01-STORAGE-ERRATUM.md'))
    require(set(data['source_sha256'])==expected_sources and data['source_sha256']=={p:hashlib.sha256((source/p).read_bytes()).hexdigest() for p in expected_sources},'Pinned full launcher/law/contract')
    require(data['runtime_sha256']=={p.relative_to(folder/'runtime').as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (folder/'runtime').rglob('*') if p.is_file()},'Copied runtime unchanged')
    require(len(data['rows'])==6 and [(r['trial'],r['case']) for r in data['rows']]==[(t,k) for t in range(2) for k in ('reference','resource','resume')],'All six launches')
    require(len(data['profiles'])==6 and len({r['sid'] for r in data['profiles']})==6 and all(r['deleted'] for r in data['profiles']),'Six new deleted SIDs')
    births=set();checked=[]
    for row in data['rows']:
        require('error' not in row and row['resumed'] and row['stopped'] and row['exit_code']==(86 if row['case']=='resource' else 0),'Native launch/termination')
        binding=row['binding'];births.add(binding['birth_filetime']);require(binding['pid']==row['pid'] and binding['birth_filetime']>0,'Real launch birth')
        require(row['token']==dict(is_appcontainer=True,capabilities=0,package_sid=row['package_sid']),'Zero-capability token')
        for limits in (row['job_before'],row['job_after']):require(limits['configured_memory_bytes']==128*1024**2 and limits['configured_processes']==1 and limits['configured_cpu_ticks']==50000000 and limits['flags'] & (0x4|0x8|0x200|0x2000)==(0x4|0x8|0x200|0x2000),'Actual resource caps')
        launch=folder/f"{row['trial']}-{row['case']}-launch";require(json.loads((launch/'launch-binding.json').read_bytes())==binding,'Recorded operator birth binding')
        protected=folder/'operator-bindings'/f"{row['package_sid']}.json";require(row['binding_before_sha256']==row['binding_after_sha256']==hashlib.sha256(protected.read_bytes()).hexdigest() and json.loads(protected.read_bytes())==binding,'Protected operator binding unchanged')
        probe=json.loads((launch/'binding-probe.json').read_bytes());require(probe['denied'] and probe['error']=='PermissionError' and probe['python_errno']==13 and probe['winerror']==5 and probe['path']==row['binding_path'],'Native child binding overwrite refused')
        origins=json.loads((launch/'origins.json').read_bytes());runtime=str((folder/'runtime').resolve()).lower()
        # Root paths may relocate during backup restoration; validate original origin suffixes.
        original_runtime=Path(origins['executable']).parent
        require(Path(origins['executable']).name.lower()=='python.exe' and str(original_runtime).lower()==origins['prefix'].lower(),'Restored executable/prefix')
        prefix=str(original_runtime).lower().rstrip('\\/')
        require(all(str(v).lower().startswith(prefix+'\\') or str(v).lower().startswith(prefix+'/') for v in origins['modules'].values()),'No external file-backed module')
        require(all(str(p).lower()==prefix or str(p).lower().startswith(prefix+'\\') or str(p).lower().startswith(prefix+'/') for p in origins['path']),'Bounded runtime search paths')
        if row['case']=='resource':require(json.loads((launch/'resource-result.json').read_bytes())==dict(requested_bytes=256*1024**2,allocation_denied=True,error='MemoryError',tick=5),'Actual allocation refusal')
        path=folder/row['workspace']/'world';evidence=replay.inspect(path,revision);frames={f['frame_sha256']:f for f in evidence['frames']}
        require(evidence['manifest']['identity']==row['expected_identity'] and all(binding[k]==row['expected_identity'][k] for k in ('world_id','run_id','source_revision')),'Preserved world identity')
        require(all(r['before']==r['after'] for r in row['read_only']) and len(row['read_only'])==len(row['samples']),'Every observation read-only')
        require(row['expiry_wait_seconds']>=5.25,'Real wall-clock expiry hold')
        labels={};active_ticks=[]
        for sample in row['samples']:
            label,value=sample['label'],sample['value'];labels.setdefault(label,[]).append(value)
            frame=frames.get(value.get('frame_sha256'));require(frame is not None and value['world']==frame['state']['world'] and value['simulation_tick']==frame['state']['simulation_tick'] and value['noise_cursor']==frame['state']['noise_cursor'] and value['state_sha256']==frame['state_sha256'],'Authoritative observed world/RNG/noise')
            wanted=dict(first='awaiting_advance',advance='active',**{'same-tick':'awaiting_advance','wrong-birth':'process_identity_mismatch','wrong-world':'unknown','wrong-prefix':'history_mismatch','recorded':'recorded','expired-alive':'stale','stopped':'stopped'})[label]
            require(value['status']==wanted and value['active']==(label=='advance'),'Causal live/advance/expiry/refusal/stop classification')
            require(value['validated']==(label!='wrong-world'),'Validation separate from liveness')
            if label in ('first','advance','same-tick','expired-alive'):
                require(value['process']['verified'] and value['process']['alive'] and value['process']['pid']==row['pid'] and value['process']['birth_filetime']==binding['birth_filetime'],'Actual matching running process')
            if label=='recorded':require(value['mode']=='recorded' and 'process' not in value and 'binding' not in value,'No PID promotion from recording')
            if label=='advance':active_ticks.append(value['simulation_tick'])
        ticks=[5,6,7] if row['case']=='resume' else [1,2,5]
        require(row['handled_ticks']==ticks and active_ticks==ticks[1:] and len(labels['first'])==len(labels['expired-alive'])==len(labels['stopped'])==1 and all(len(labels[k])==3 for k in ('same-tick','wrong-birth','wrong-world','wrong-prefix','recorded')),'Complete native observation denominator')
        require(labels['stopped'][0]['simulation_tick']==(5 if row['case']=='resource' else 32),'Stop preserves actual final tick')
        checked.append(dict(trial=row['trial'],case=row['case'],samples=len(row['samples']),active_ticks=active_ticks,expiry_seconds=row['expiry_wait_seconds'],exit=row['exit_code']))
    require(len(births)==6,'New launch births, no stale binding reuse')
    for trial in range(2):
        reference=replay.inspect(folder/f'{trial}-reference/world',revision);resource=replay.inspect(folder/f'{trial}-resource/world',revision)
        require(replay.canonical(reference['states'])==replay.canonical(resource['states']) and len(resource['states'])==33,'All33 exact simulation states')
        require(replay.canonical([f['event'] for f in reference['frames'] if f['event'] is not None])==replay.canonical([f['event'] for f in resource['frames'] if f['event'] is not None]),'All32 exact events/ancestry')
        prefix=(folder/f'{trial}-resource/before-resume.jsonl').read_bytes();require((folder/f'{trial}-resource/world/frames.jsonl').read_bytes().startswith(prefix),'Original authoritative raw history prefix')
    return dict(schema='launch01-audit-v1',native_launches=6,profiles_deleted=6,exact_world_histories=2,states_per_history=33,events_per_history=32,checks=checked,continuous_world=False,science_demonstrated=False)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output-dir',required=True);parser.add_argument('--source-dir',required=True);parser.add_argument('--source-revision',required=True);parser.add_argument('--report',required=True);args=parser.parse_args()
    try:result=audit(args.output_dir,args.source_dir,args.source_revision)
    except (ValueError,OSError,KeyError,TypeError) as error:print('Rejected:',error);raise SystemExit(2)
    Path(args.report).write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))
