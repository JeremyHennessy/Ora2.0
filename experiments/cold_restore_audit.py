"""Independent RESTORE-01 acceptance; no driver, worker or launcher imports."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile
from experiments import heartbeat_template_audit as replay

ARCHIVE_SHA='d1956130ee5c359561e948870b5288f352615ed63edb0118b5861758d2bdc564'
OLD_REVISION='b5d3104087b397d07c62a45592dde4bc13d58e51'
CORRUPTION=b'\n# RESTORE01 registered source-corruption control\n'


def require(value,message):
    if not value: raise ValueError(message)


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def tree(folder): return {p.relative_to(folder).as_posix():sha(p) for p in Path(folder).rglob('*') if p.is_file()}


def audit(output,source,revision):
    output,source=Path(output),Path(source); data=json.loads((output/'evidence.json').read_text(encoding='utf-8'))
    require(data['schema']=='restore01-v1' and data['revision']==revision and data['world_revision']==OLD_REVISION,'Source revisions')
    backup=Path(data['backup']); require(backup==Path('C:/ora/isolation04-20261009/isolation04-integrated-20261009-evidence.zip'),'Registered independent backup')
    require(sha(backup)==data['backup_sha256']==ARCHIVE_SHA,'Independent archive hash')
    names={'experiments/isolation_capability.py','experiments/isolation_worker.py','experiments/isolation_capability_audit.py','experiments/process_limits.py','docs/ISOLATION-01-CONTRACT.md',*replay.FILES,'experiments/__init__.py','experiments/cold_restore.py','experiments/cold_restore_worker.py','experiments/cold_restore_audit.py','docs/RESTORE-01-CONTRACT.md'}
    require(set(data['source_sha256'])==names and all(sha(source/p)==v for p,v in data['source_sha256'].items()),'Complete new adapter source')
    with zipfile.ZipFile(backup) as z:
        old=json.loads(z.read('panel/evidence.json')); archived={n[len('panel/runtime/'):]:hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist() if n.startswith('panel/runtime/') and not n.endswith('/')}
        require(archived==old['runtime_sha256']==data['archived_runtime_sha256'],'Original restored dependency manifest')
        expected=dict(archived,**{'restore_worker.py':sha(source/'experiments/cold_restore_worker.py')})
        require(tree(output/'runtime')==data['runtime_sha256']==expected,'Complete restored runtime')
        changed=dict(expected); changed['experiments/heartbeat_template.py']=hashlib.sha256(z.read('panel/runtime/experiments/heartbeat_template.py')+CORRUPTION).hexdigest()
        require(tree(output/'corrupt-runtime')==data['corrupt_runtime_sha256']==changed,'Exact registered corruption only')
        for trial in range(2):
            for target,prefix in ((output/f'input-{trial}',f'panel/{trial}-cpu/trusted-snapshot/'),(output/f'reference-{trial}',f'panel/{trial}-confined/world/')):
                hashes={n[len(prefix):]:hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist() if n.startswith(prefix) and not n.endswith('/')}
                require(tree(target)==hashes,'Exact cold input/reference')
    profiles=data['profiles']; require(set(profiles)=={'0','1'} and len({p['sid'] for p in profiles.values()})==2,'Two fresh identities')
    require(all(p['deleted'] and p['cleanup_hresult']==0 and p['sid'] not in data['original_profiles'].values() for p in profiles.values()),'Fresh profiles cleaned')
    require(data['original_profiles']=={k:p['sid'] for k,p in old['profiles'].items()},'Original profiles preserved')
    require(0<data['elapsed_seconds']<280,'Finite panel')
    cases={'missing-runtime','ungranted','corrupt-source','restore'}
    require(len(data['rows'])==8 and {(r['trial'],r['case']) for r in data['rows']}=={(t,k) for t in range(2) for k in cases},'Complete frozen matrix')
    for row in data['rows']:
        trial,case=row['trial'],row['case']; require(row['stopped'] and row['confined'] and row['elapsed_seconds']<10,'Stopped confined launch')
        require(row['workspace']==f'world-{trial}' and row['runtime']==('corrupt-runtime' if case=='corrupt-source' else 'runtime'),'Fixed restored paths')
        initial=replay.inspect(output/f'input-{trial}',OLD_REVISION); require(initial['report']['verified_simulation_tick']==7,'Trusted input tick')
        initial_tree=tree(output/f'input-{trial}'); require(row['world_before']==initial_tree,'Single original world input')
        if case=='missing-runtime':
            require(not row['resumed'] and row['pid'] is None and row['winerror']==2 and not row['marker'] and row['world_after']==initial_tree,'Missing runtime fail-closed'); continue
        require(row['resumed'] and row['token']==dict(is_appcontainer=True,capabilities=0,package_sid=profiles[str(trial)]['sid']),'Native confinement token')
        for key in ('job_before','job_after'):
            u=row[key]; require(u['configured_memory_bytes']==128*1024**2 and u['configured_processes']==1 and u['configured_cpu_ticks']==50_000_000 and u['flags'] & 0x220c==0x220c,'Unchanged suspended caps')
        if case=='ungranted':
            require(row['exit_code']==2 and not row['marker'] and 'runtime_report' not in row and row['world_after']==initial_tree,'Ungrant refusal without mutation'); continue
        report=row['runtime_report']; root=(output/row['runtime']).resolve()
        require(report['pid']==row['pid'] and report['isolated'] and row['marker'],'Restored child identity')
        require(Path(report['executable']).resolve()==root/'python.exe' and Path(report['prefix']).resolve()==root,'Restored executable/prefix')
        require(report['sys_path']==[str(root/'python312.zip'),str(root/'DLLs'),str(root)],'Isolated restored path only')
        require(report['module_files'] and all(Path(p).resolve().is_relative_to(root) for p in report['module_files'].values()),'External module provenance')
        for module in ('experiments.heartbeat_template','experiments.heartbeat_template_audit'):
            require(Path(report['module_files'][module]).resolve()==root/(module.replace('.','/')+'.py'),'Restored critical module origin')
        source_hashes={p:sha(root/p) for p in replay.FILES}; require(report['source_sha256']==source_hashes,'Loaded source binding')
        if case=='corrupt-source':
            require(row['exit_code']==2 and report['phase']=='before_resume' and row['world_after']==initial_tree and row['rejection']['reason']=='Source/Python mismatch','Corrupt source refusal'); continue
        require(row['exit_code']==0 and 'error' not in row and report['phase']=='complete','Successful cold restore')
        final=replay.inspect(output/row['workspace']/'world',OLD_REVISION); reference=replay.inspect(output/f'reference-{trial}',OLD_REVISION)
        require(final['states']==reference['states'] and len(final['states'])==33,'Exact full history/ancestry/RNG/noise continuation')
        require(final['manifest']==initial['manifest']==reference['manifest'],'World identity continuity')
        require((output/row['workspace']/'world/frames.jsonl').read_bytes().startswith((output/f'input-{trial}'/'frames.jsonl').read_bytes()),'Exact raw prefix')
        require(tree(output/row['workspace']/'world')==row['world_after'],'Final world checksum')
        observed=row['recorded_observation']; require(observed['recorded'] is True and observed['report']['process_health']=='unverified' and observed['report']['reported_status']=='stopped' and observed['states_sha256']==replay.digest(final['states']),'Read-only recorded observation')
    return dict(schema='restore01-audit-v1',launches=8,exact_cold_restorations=2,rejections=6,full_states_each=33,events_each=32,
        independent_drive_application_restore=True,child_application_dependencies_restored=True,full_host_recovery=False,physical_power_loss=False,production_isolation=False,continuous_world=False,scientific_progress=False)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--output-dir',required=True); parser.add_argument('--source-dir',required=True); parser.add_argument('--source-revision',required=True)
    args=parser.parse_args()
    try: result=audit(args.output_dir,args.source_dir,args.source_revision)
    except (ValueError,OSError,KeyError,TypeError) as error: print('Rejected:',error); raise SystemExit(2)
    print(json.dumps(result,indent=2))
