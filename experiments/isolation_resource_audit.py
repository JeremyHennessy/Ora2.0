"""Independent ISOLATION-03 semantic replay; imports no driver or launcher."""
import argparse
import json
from pathlib import Path
from experiments import isolation_world_audit as independent

FILES=(*independent.FILES,'experiments/isolation_resource.py','experiments/isolation_resource_worker.py',
       'experiments/isolation_resource_audit.py','docs/ISOLATION-03-CONTRACT.md',
       'docs/ISOLATION-03-EXECUTION-ERRATUM.md')
require=independent.require
sha=independent.sha
tree=independent.tree
replay=independent.replay


def audit(output,source,revision):
    output,source=Path(output),Path(source)
    data=json.loads((output/'evidence.json').read_bytes())
    require(data['schema']=='isolation03-v1' and data['revision']==revision,'Source identity')
    require(set(data['source_sha256'])==set(FILES) and all(sha(source/p)==v for p,v in data['source_sha256'].items()),'Complete exact source')
    require(tree(output/'runtime')==data['runtime_sha256'],'Runtime copy')
    for name in (*replay.FILES,'experiments/__init__.py'):
        require(sha(output/'runtime'/name)==sha(source/name),'World source unchanged')
    require(sha(output/'runtime/resource_worker.py')==sha(source/'experiments/isolation_resource_worker.py'),'Fixed adapter')
    require(data['cleanup'] is True and data['cleanup_hresult']==0 and 0<data['elapsed_seconds']<300,'Cleanup / finite horizon')
    cases={'ordinary','confined','cpu','memory','wall','cpu-control','memory-control','wall-control','cpu-resume','memory-resume','wall-resume'}
    require(len(data['rows'])==22 and {(r['trial'],r['case']) for r in data['rows']}=={(t,k) for t in range(2) for k in cases},'Frozen complete matrix')
    references={t:independent.observed(output/f'{t}-ordinary/world',revision)[0] for t in range(2)}
    for row in data['rows']:
        trial,case=row['trial'],row['case']; folder=output/row['workspace']
        require(folder.resolve().is_relative_to(output.resolve()),'Path escape')
        require(row['resumed'] is True and row['world_started'] is True and row['stopped'] is True,'Native executed and stopped')
        expected=dict(is_appcontainer=False,capabilities=0,package_sid=None) if case=='ordinary' else dict(is_appcontainer=True,capabilities=0,package_sid=data['package_sid'])
        require(row['token']==expected,'Native token')
        usage=row['job_before']
        require(usage['configured_memory_bytes']==128*1024**2 and usage['configured_cpu_ticks']==50_000_000 and usage['configured_processes']==(2 if case=='ordinary' else 1) and usage['flags'] & 0x220c==0x220c,'Read-back native caps')
        pressure=case in {'cpu','memory','wall'}
        if pressure:
            marker=json.loads((folder/'pressure.json').read_bytes())
            request={'cpu':7,'memory':256*1024**2,'wall':12}[case]
            require(marker==dict(case=case,tick=5,kind=case,requested=request,completed=False,memory_denied=case=='memory'),'Pressure target and cause')
            if case=='memory':
                require(row['exit_code']==42 and 'error' not in row and row['elapsed_seconds']<10,'Actual memory denial')
            else:
                require(row['exit_code'] in ({1816,124} if case=='cpu' else {124}),'Actual CPU/wall stop')
                if row['exit_code']==124:
                    require(row.get('error')=='Capability worker exceeded time cap' and row['termination_reason']==case,'Supervisor causal time stop')
                else:
                    require('error' not in row,'Native CPU stop')
                require(row['elapsed_seconds']<10 if case=='cpu' else 10<=row['elapsed_seconds']<12,'Causal CPU/wall boundary')
                require(row['job_after']['user_cpu_seconds']>=4.8 if case=='cpu' else row['job_after']['user_cpu_seconds']<5,'CPU versus wall usage')
            evidence,observed=independent.observed(folder/'before-resume',revision)
            require(evidence['report']['verified_simulation_tick']==5 and evidence['report']['checkpoint_current'] is False,'Durable tick-five boundary')
            checkpoint=json.loads((folder/'before-resume/checkpoint.json').read_bytes())
            pending=json.loads((folder/'before-resume/checkpoint.pending').read_bytes())
            require(checkpoint['state']['simulation_tick']==4 and pending['state']['simulation_tick']==5,'Pending/committed boundary')
            require(sha(folder/'durable-prefix.jsonl')==row['prefix_sha256'] and (folder/'durable-prefix.jsonl').read_bytes()==(folder/'before-resume/frames.jsonl').read_bytes(),'Captured prefix')
        else:
            require(row['exit_code']==0 and 'error' not in row and row['elapsed_seconds']<10,'Reference/control/resume completion')
            evidence,observed=independent.observed(folder/'world',revision)
            report=evidence['report']
            require(len(evidence['states'])==33 and report['verified_simulation_tick']==32 and report['checkpoint_current'] is True and report['reported_status']=='stopped','Terminal finite history')
            require(evidence['manifest']['identity']['world_id']==f'isolation03-trial-{trial}','Identity')
            reference=references[trial]
            require(evidence['states']==reference['states'] and [f['event'] for f in evidence['frames'] if f['event'] is not None]==[f['event'] for f in reference['frames'] if f['event'] is not None],'Full identity/ancestry/ledger/RNG/cursor and events')
            if case.endswith('-control'):
                kind=case.split('-')[0]; amount={'cpu':0.05,'memory':32*1024**2,'wall':0.05}[kind]
                require(json.loads((folder/'pressure.json').read_bytes())==dict(case=case,tick=5,kind=kind,requested=amount,completed=True,memory_denied=False),'Matched completing control')
            if case.endswith('-resume'):
                require(row['prefix_preserved'] is True and row['request']['resume'] is True and row['request']['case']=='reference' and (folder/'world/frames.jsonl').read_bytes().startswith((folder/'durable-prefix.jsonl').read_bytes()),'Fresh recovery retained prefix')
        require(observed==row['observation'],'Read-only recorded observation')
    return dict(schema='isolation03-audit-v1',launch_cases=22,audited_world_histories=16,resource_stops=6,
        exact_resumes=6,matched_controls=6,states_per_completed_history=33,read_only_observations=True,
        evidence_sha256=sha(output/'evidence.json'),scientific_progress=False,physical_power_loss=False,
        memory_peak_bound=False,production_security_verified=False,unattended_runtime=False)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('output-dir','source-dir','source-revision'): p.add_argument('--'+name,required=True)
    a=p.parse_args()
    try: print(json.dumps(audit(a.output_dir,a.source_dir,a.source_revision),indent=2))
    except (ValueError,OSError,KeyError,TypeError) as error:
        print('Rejected:',error); raise SystemExit(2)
