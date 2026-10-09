"""Read-only STORAGE-02 byte reconstruction; no worker/injector/panel imports."""
import argparse
import hashlib
import json
from pathlib import Path
from experiments import heartbeat_template_audit as heartbeat
from experiments import world_snapshot_audit as snapshot

ROOT = Path(__file__).resolve().parents[1]
CASES = tuple(f'{where}-{how}' for where in ('journal','pending') for how in
              ('short-return','zero-return','short-error','flush-error','fsync-before','fsync-after','kill')) + ('replace-before','replace-after')
FILES = (*snapshot.FILES, 'docs/STORAGE-02-CONTRACT.md', 'experiments/world_io_fault.py',
         'experiments/world_io_panel.py', 'experiments/world_io_audit.py')

def sources():
    return {p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in FILES}

def blobs(directory):
    return {p.name:p.read_bytes() for p in Path(directory).iterdir() if p.is_file()}

def hashes(directory):
    return {k:hashlib.sha256(v).hexdigest() for k,v in blobs(directory).items()}

def expected(case):
    code = 81 if case == 'journal-kill' else 82 if case == 'pending-kill' else 2
    resume = 2 if case in ('journal-short-return','journal-short-error','journal-kill') else 0
    return code, resume

def inspect(output, revision):
    output = Path(output)
    evidence = heartbeat.decode(heartbeat.read_small(output/'panel.json'))
    if set(evidence) != {'schema','revision','sources','records','commands'} or evidence['schema'] != 'storage02-panel-v1' or evidence['revision'] != revision or evidence['sources'] != sources():
        raise ValueError('Panel/source binding')
    if [r.get('case') for r in evidence['records']] != list(CASES):
        raise ValueError('Complete ordered16-case denominator')
    ref = heartbeat.inspect(output/'reference', revision)
    paused = heartbeat.inspect(output/'paused', revision)
    if ref['manifest']['config'] != {'seed':1,'work':2,'max_ticks':32} or ref['report']['world_id'] != 'storage02-reference' or ref['report']['reported_status'] != 'stopped' or paused['report']['reported_status'] != 'paused' or paused['report']['verified_simulation_tick'] != 3 or paused['manifest'] != ref['manifest']:
        raise ValueError('Frozen fixture')
    metadata, package = snapshot.read_package(output/'snapshot.zip', revision)
    snapshot.compare_capture(metadata, paused)
    if package != blobs(output/'paused'):
        raise ValueError('Snapshot byte identity')
    def args(path):
        return ['--output-dir',str(path),'--world-id','storage02-reference','--source-revision',revision,'--work','2','--max-ticks','32','--seed','1']
    commands = [('experiments.heartbeat_template',args(output/'reference'),'reference.log',0),
                ('experiments.heartbeat_template',[*args(output/'paused'),'--pause-after','3'],'paused.log',0),
                ('experiments.world_snapshot',['pack','--world-dir',str(output/'paused'),'--archive',str(output/'snapshot.zip'),'--source-revision',revision],'snapshot.log',0)]
    direct = rejected = 0
    for case, row in zip(CASES,evidence['records']):
        directory = output/case
        before = blobs(directory/'before')
        target = (directory/'target-frame.json').read_bytes()
        value = heartbeat.decode(target)
        trace = heartbeat.decode((directory/'injection.json').read_bytes())
        if heartbeat.canonical(trace) != heartbeat.canonical(dict(case=case, tick=5, injections=1, payload_size=len(target), payload_sha256=hashlib.sha256(target).hexdigest())):
            raise ValueError('Exactly one targeted injection')
        raw = before['frames.jsonl']
        # Reconstruct the entire undamaged chain through the proposed advancing5.
        prefix = raw if case == 'journal-zero-return' else raw[:-(len(target)//2)] if case in ('journal-short-return','journal-short-error','journal-kill') else raw[:-len(target)]
        frames = [heartbeat.decode(x) for x in prefix.splitlines()]+[value]
        if len(frames) != 6 or not prefix.endswith(b'\n'):
            raise ValueError('Exact advancing5 boundary')
        chain = '0'*64
        previous_time = None
        for tick, frame in enumerate(frames):
            model = ref['frames'][tick]
            stable = {k:v for k,v in frame.items() if k not in ('last_heartbeat','frame_sha256','previous_sha256')}
            expected_stable = {k:v for k,v in model.items() if k not in ('last_heartbeat','frame_sha256','previous_sha256')}
            moment = heartbeat.utc(frame['last_heartbeat'])
            if heartbeat.canonical(stable) != heartbeat.canonical(expected_stable) or frame['previous_sha256'] != chain or frame['frame_sha256'] != heartbeat.digest({k:v for k,v in frame.items() if k != 'frame_sha256'}) or previous_time is not None and moment < previous_time:
                raise ValueError('Injected payload/reference state or chain')
            chain, previous_time = frame['frame_sha256'], moment
        old_checkpoint = prefix.splitlines(keepends=True)[-1]
        journal = prefix + (b'' if case == 'journal-zero-return' else target[:len(target)//2] if case in ('journal-short-return','journal-short-error','journal-kill') else target)
        expected_bytes = {'manifest.json':blobs(output/'reference')['manifest.json'],'writer.lock':b'L','frames.jsonl':journal,'checkpoint.json':old_checkpoint}
        if case.startswith('pending-') or case == 'replace-before':
            expected_bytes['checkpoint.pending'] = b'' if case == 'pending-zero-return' else target[:len(target)//2] if case in ('pending-short-return','pending-short-error','pending-kill') else target
        elif case == 'replace-after':
            expected_bytes['checkpoint.json'] = target
        if before != expected_bytes:
            raise ValueError('Interrupted file bytes differ: '+case)
        fault_exit, resume_exit = expected(case)
        if heartbeat.canonical(row) != heartbeat.canonical(dict(case=case, fault_exit=fault_exit, resume_exit=resume_exit,
                       before_sha256=hashes(directory/'before'), after_sha256=hashes(directory/'world'),
                       restored_sha256=hashes(directory/'restored'), observer_read_only=True)):
            raise ValueError('Exit/hash/read-only evidence')
        if resume_exit:
            rejected += 1
            if before != blobs(directory/'world'):
                raise ValueError('Rejected input was mutated')
            try:
                heartbeat.inspect(directory/'world',revision)
            except (ValueError,OSError,KeyError,TypeError):
                pass
            else:
                raise ValueError('Partial journal independently accepted')
        else:
            direct += 1
            recovered = heartbeat.inspect(directory/'world',revision)
            if heartbeat.canonical(recovered['states']) != heartbeat.canonical(ref['states']) or not (directory/'world/frames.jsonl').read_bytes().startswith(before['frames.jsonl']):
                raise ValueError('Direct identity/state/history/prefix continuity')
        if blobs(directory/'restored-before') != package:
            raise ValueError('Snapshot restoration differs')
        recovered = heartbeat.inspect(directory/'restored',revision)
        if heartbeat.canonical(recovered['states']) != heartbeat.canonical(ref['states']) or recovered['manifest'] != ref['manifest'] or not (directory/'restored/frames.jsonl').read_bytes().startswith(package['frames.jsonl']):
            raise ValueError('Backup complete state continuity')
        observer = heartbeat.decode((directory/'observer.json').read_bytes())
        for key in ('run_id','verified_simulation_tick','noise_cursor','verified_state_sha256','work','heat','historic_objects','process_health','reported_status'):
            if observer[key] != recovered['report'][key]:
                raise ValueError('Observer disagrees with independent state')
        commands.extend([
            ('experiments.world_io_fault',['--case',case,'--trace-dir',str(directory),*args(directory/'world')],case+'/fault.log',fault_exit),
            ('experiments.heartbeat_template',[*args(directory/'world'),'--resume'],case+'/resume.log',resume_exit),
            ('experiments.world_snapshot',['restore','--world-dir',str(directory/'restored'),'--archive',str(output/'snapshot.zip'),'--source-revision',revision],case+'/restore.log',0),
            ('experiments.heartbeat_template',[*args(directory/'restored'),'--resume'],case+'/continued.log',0),
            ('experiments.heartbeat_template_audit',['--input-dir',str(directory/'restored'),'--source-revision',revision],case+'/observer.json',0)])
    if heartbeat.canonical(evidence['commands']) != heartbeat.canonical([dict(module=m,args=a,log=l,exit_code=c) for m,a,l,c in commands]) or any(not (output/l).is_file() for _,_,l,_ in commands):
        raise ValueError('Exact complete process/exit denominator')
    return dict(schema='storage02-audit-v1',cases=16,direct_continuations=direct,preserved_rejections=rejected,
                backup_continuations=16,states_per_continuation=33,canonical_state_sequence_sha256=heartbeat.digest(ref['states']),
                observer_checks=16,physical_power_loss=False,filesystem_crash_consistency=False,
                isolation_verified=False,scientific_progress=False)

if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--input-dir',required=True); p.add_argument('--source-revision',required=True)
    a=p.parse_args()
    try:
        print(json.dumps(inspect(a.input_dir,a.source_revision),indent=2,sort_keys=True))
    except (ValueError,OSError,KeyError,TypeError) as e:
        p.exit(2,f'Rejected I/O evidence: {e}\n')
