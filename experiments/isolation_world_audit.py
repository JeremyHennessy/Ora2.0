"""Independent confined-world replay audit; imports no launcher/worker/driver."""
import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path

from experiments import heartbeat_template_audit as replay

POINTS=dict(pre_commit=77,post_journal=78,post_pending=79,post_checkpoint=80)
FILES=(*replay.FILES,'experiments/__init__.py','experiments/isolation_capability.py',
       'experiments/isolation_worker.py','experiments/isolation_capability_audit.py',
       'experiments/process_limits.py','docs/ISOLATION-01-CONTRACT.md',
       'experiments/isolation_world.py','experiments/isolation_world_worker.py',
       'experiments/isolation_world_audit.py','docs/ISOLATION-02-CONTRACT.md')


def require(value,message):
    if not value:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def tree(folder):
    return {p.relative_to(folder).as_posix():sha(p) for p in Path(folder).rglob('*') if p.is_file()}


def observed(folder, revision):
    before=tree(folder)
    evidence=replay.inspect(folder,revision)
    report=replay.inspect(folder,revision,current=datetime.fromisoformat(evidence['frames'][-1]['last_heartbeat']))['report']
    require(tree(folder)==before,'Observer modified world')
    return evidence,dict(recorded=True,report=report,world_tree_sha256=before,
        states_sha256=replay.digest(evidence['states']),
        events_sha256=replay.digest([f['event'] for f in evidence['frames'] if f['event'] is not None]))


def audit(output,source,revision):
    output,source=Path(output),Path(source)
    data=json.loads((output/'evidence.json').read_bytes())
    require(data['schema']=='isolation02-v1' and data['revision']==revision,'Exact source identity')
    require(set(data['source_sha256'])==set(FILES),'Complete source manifest')
    require(all(sha(source/p)==digest for p,digest in data['source_sha256'].items()),'Source hash mismatch')
    require(tree(output/'runtime')==data['runtime_sha256'],'Runtime copy mismatch')
    for name in (*replay.FILES,'experiments/__init__.py'):
        require(sha(output/'runtime'/name)==sha(source/name),'World source copy changed')
    require(sha(output/'runtime/world_worker.py')==sha(source/'experiments/isolation_world_worker.py'),'Wrapper changed')
    require(data['cleanup'] is True and data['cleanup_hresult']==0 and 0<data['elapsed_seconds']<300,'Cleanup / finite horizon')
    cases={'ordinary','confined','identity-rejection','setup-missing','setup-job','setup-token'}
    cases.update(point+suffix for point in POINTS for suffix in ('-interrupt','-resume'))
    require(len(data['rows'])==28 and {(r['trial'],r['case']) for r in data['rows']}==
            {(trial,case) for trial in range(2) for case in cases},'Frozen complete matrix')
    rows={(r['trial'],r['case']):r for r in data['rows']}
    def final(folder,trial):
        evidence,observation=observed(folder,revision)
        identity=evidence['manifest']['identity']
        require(identity['world_id']==f'isolation02-trial-{trial}','World identity replaced')
        require(len(evidence['states'])==33 and evidence['report']['verified_simulation_tick']==32 and
                evidence['report']['reported_status']=='stopped' and evidence['report']['checkpoint_current'] is True,'Finite terminal state')
        return evidence,observation
    references={trial:final(output/f'{trial}-ordinary/world',trial)[0] for trial in range(2)}
    def equivalent(evidence,trial):
        reference=references[trial]
        require(evidence['states']==reference['states'],'Full state / identity / ancestry / RNG / noise diverges')
        require([f['event'] for f in evidence['frames'] if f['event'] is not None]==
                [f['event'] for f in reference['frames'] if f['event'] is not None],'Reaction events diverge')
    for (trial,case),row in rows.items():
        require(row['stopped'] is True and row['elapsed_seconds']<10,'Process stop / time cap')
        folder=output/row['workspace']
        require(folder.resolve().is_relative_to(output.resolve()),'Workspace path escape')
        if case.startswith('setup-'):
            require(not row['resumed'] and not row['world_started'] and not row['world_exists'] and
                    not (folder/'world-started').exists() and not (folder/'world').exists() and 'error' in row,'Setup ran world')
            if case=='setup-missing':
                require(row['pid'] is None and row['winerror']==2,'Creation failure')
            else:
                require(row['pid'] is not None and row['exit_code']==125 and row['fault']==case[6:],'Suspended cleanup')
            continue
        require(row['resumed'] is True and row['world_started'] is True and row['world_exists'] is True and 'error' not in row,'World did not execute')
        expected=dict(is_appcontainer=False,capabilities=0,package_sid=None) if case=='ordinary' else dict(is_appcontainer=True,capabilities=0,package_sid=data['package_sid'])
        require(row['token']==expected,'Kernel token gate')
        for key in ('job_before','job_after'):
            usage=row[key]
            require(usage['configured_memory_bytes']==128*1024**2 and usage['configured_cpu_ticks']==50_000_000 and
                    usage['configured_processes']==(2 if case=='ordinary' else 1) and usage['flags'] & 0x220c==0x220c,'Kernel caps')
        if case=='identity-rejection':
            require(row['exit_code']==2 and row['world_before']==row['world_after']==tree(folder/'world'),'Rejected resume changed world')
            require((folder/'rejection.json').exists(),'Missing rejection reason')
            continue
        if case.endswith('-interrupt'):
            point=case[:-10]
            require(row['exit_code']==POINTS[point],'Wrong fault exit')
            evidence,observation=observed(folder/'before-resume',revision)
            require(observation==row['observation'],'Crash observation mismatch')
            require(evidence['report']['verified_simulation_tick']==(4 if point=='pre_commit' else 5),'Durable boundary')
            prefix=folder/'durable-prefix.jsonl'
            require(sha(prefix)==row['prefix_sha256'] and prefix.read_bytes()==(folder/'before-resume/frames.jsonl').read_bytes(),'Durable prefix capture')
        else:
            require(row['exit_code']==0,'Reference/resume failed')
            evidence,observation=final(folder/'world',trial)
            require(observation==row['observation'],'Terminal observation mismatch')
            equivalent(evidence,trial)
            if case.endswith('-resume'):
                require(row['request']['resume'] is True and row['prefix_preserved'] is True and
                        (folder/'world/frames.jsonl').read_bytes().startswith((folder/'durable-prefix.jsonl').read_bytes()),'Resume lost prefix')
    return dict(schema='isolation02-audit-v1',launch_cases=28,ordinary_references=2,confined_references=2,
        confined_interruptions=8,exact_resumes=8,identity_rejections=2,setup_refusals=6,
        audited_world_histories=12,states_per_completed_history=33,read_only_observations=True,
        evidence_sha256=sha(output/'evidence.json'),physical_power_loss=False,
        hostile_escape_assessment=False,unattended_runtime=False,scientific_progress=False)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',required=True)
    parser.add_argument('--source-dir',required=True)
    parser.add_argument('--source-revision',required=True)
    args=parser.parse_args()
    try:
        print(json.dumps(audit(args.output_dir,args.source_dir,args.source_revision),indent=2))
    except (ValueError,OSError,KeyError,TypeError) as error:
        print('Rejected:',error)
        raise SystemExit(2)
