"""One-claim campaign controller. Inactive source always refuses execution."""
import json
from pathlib import Path
import shutil
import subprocess

from experiments import al02_campaign_admission as gate
from experiments import al02_one_pair_custody as custody
from tools.al02_campaign_evidence import analyze_committed_panel, next_unclaimed

# Downstream identity, outside the binding that the admission module embeds.
ADMISSION_SHA256 = '536ec33a2a2901e5dc226ad8146781caf6a4a45921867897988b9e90acf9cd98'


def pilot_admissions(root, ordered, binding, checkout, pins, *, review=False, continuation=False):
    """Derive lower-assurance admission inputs from custody, with no review ledger."""
    admitted = {}
    for item in (ordered[8:] if continuation else ordered[:8]):
        directory = root/item['attempt']
        terminal = directory/'04-terminal.json'
        if not terminal.exists():
            continue
        command = [binding['python'],'-I','-S','-B',binding['worker'],
                   str(directory/'00-pending.json'),gate.TOKEN]
        identity = ((gate.continuation_identity(item) if continuation else gate.pilot_identity(item)) if review else
                    gate.admitted(directory,checkout,command,gate.OWNER,
                                  item['context_sha256'],gate.LIMITS,pins))
        source_path = str(checkout/'experiments/al02_one_pair.py')
        identity.update(referee_entry='experiments.al02_one_pair.verify_context',
                        referee_sha256=pins[source_path])
        admitted[item['index']] = dict(command=command,pins=pins,identities=identity,
                                      terminal_pin=custody.digest(terminal))
    return admitted


def review_pilot(*, continuation=False):
    """Read-only batch reanalysis, with missing outcomes retained."""
    from statistics import mean, stdev
    binding = gate.continuation_binding() if continuation else gate.pilot_binding()
    ordered = gate.inventory()
    root = custody.pinned_path(gate.CONTINUATION_DESTINATION if continuation else gate.PILOT_DESTINATION)
    checkout = custody.pinned_path(gate.CHECKOUT)
    source = str(checkout/'experiments/al02_campaign_admission.py')
    pins = dict(binding['pins'], **{source: ADMISSION_SHA256})
    for path, expected in pins.items():
        if custody.digest(path) != expected:
            raise ValueError(f'Pilot review source differs: {path}')
    admissions = pilot_admissions(root, ordered, binding, checkout, pins, review=True, continuation=continuation)
    rows = analyze_committed_panel(root, ordered, admissions)['rows']
    rows = rows[8:] if continuation else rows[:8]
    differences = [row['result']['contrast'] for row in rows if row['status']=='accepted']
    count = 120 if continuation else 8
    complete = len(differences)==count
    return dict(scope='supervised lower assurance; batch review required', rows=rows,
                batch_review_proposals=[
                    batch_review(admissions,start)
                    for start in range(8,128,8)
                    if continuation and all(row['status']=='accepted'
                                            for row in rows[start-8:start])
                ],
                committed=count, accepted=len(differences), distribution=differences,
                all_context_mean=mean(differences) if complete else None,
                all_context_se=stdev(differences)/count**0.5 if complete else None,
                observed_only_mean=mean(differences) if differences else None)


def batch_review(admissions, start):
    return dict(schema='al02-continuation-batch-review-v1', start=start,
                evidence=[dict(admissions[i]['identities'],
                               terminal_sha256=admissions[i]['terminal_pin'])
                          for i in range(start,start+8)])


def run_next(*, pilot=False, continuation=False):
    if pilot and continuation:
        raise ValueError('Conflicting supervised scopes')
    # No writes, including lock creation, before authority is present.
    authority_pin = (gate.CONTINUATION_AUTHORIZATION_SHA256 if continuation else
                     gate.PILOT_AUTHORIZATION_SHA256 if pilot else gate.AUTHORIZATION_SHA256)
    if authority_pin is None:
        raise ValueError('Campaign scientific authorization absent')
    import msvcrt
    binding = gate.continuation_binding() if continuation else gate.pilot_binding() if pilot else gate.binding()
    ordered = gate.inventory()
    root = custody.pinned_path(gate.CONTINUATION_DESTINATION if continuation else gate.PILOT_DESTINATION if pilot else gate.DESTINATION)
    checkout = custody.pinned_path(gate.CHECKOUT)
    source = str(checkout/'experiments/al02_campaign_admission.py')
    if Path(gate.__file__) != Path(source) or custody.digest(source) != ADMISSION_SHA256:
        raise ValueError('Campaign admission executable identity differs')
    if subprocess.check_output(['git','-C',str(checkout),'rev-parse','HEAD'],
                               text=True,timeout=2).strip() != binding['production_head']:
        raise ValueError('Campaign production HEAD differs')
    pins = dict(binding['pins'], **{source: ADMISSION_SHA256})
    with (root/'campaign.lock').open('a+b') as lock:
        lock.seek(0)
        try:
            msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        except OSError as exc:
            raise ValueError('Campaign ownership lock unavailable') from exc
        try:
            if gate.STOP.exists():
                return None
            supervisor = json.loads((gate.ROOT/'automation/ora-codex/status.json').read_bytes())
            if supervisor['status'] != 'parked':
                raise ValueError('Supervisor must remain PARKED')
            # Independent admission receipts are external inputs and must be
            # installed by the authorized reviewer before advancement.
            admitted_path = root/'reviewed-admissions.json'
            admitted = ({int(key):value for key,value in
                         json.loads(admitted_path.read_bytes()).items()} if admitted_path.exists() else {})
            if pilot or continuation:
                if admitted_path.exists():
                    raise ValueError('Strict review ledger is outside pilot scope')
                admitted = pilot_admissions(root, ordered, binding, checkout, pins, continuation=continuation)
            for index, review in admitted.items():
                if index not in range(128):
                    raise ValueError('Reviewed index outside commitment')
                committed = ordered[index]
                expected_command = [binding['python'],'-I','-S','-B',binding['worker'],
                                    str(root/committed['attempt']/'00-pending.json'),gate.TOKEN]
                identity = review['identities']
                if (review['command'] != expected_command or review['pins'] != pins
                        or identity['binding_sha256'] != (gate.CONTINUATION_BINDING_SHA256 if continuation else gate.BINDING_SHA256)
                        or identity['package_sha256'] != (gate.CONTINUATION_PACKAGE_SHA256 if continuation else gate.PACKAGE_SHA256)
                        or identity['contexts_sha256'] != gate.CONTEXTS_SHA256
                        or identity['authorization_sha256'] != authority_pin):
                    raise ValueError('Reviewed campaign release identity differs')
            report = analyze_committed_panel(root,ordered,admitted)
            accepted = [r['index'] for r in report['rows'] if r['status']=='accepted']
            row = next_unclaimed(root,ordered,accepted,stop=gate.STOP,start=8 if continuation else 0)
            if row is None or (pilot and row['index'] >= 8):
                return None
            if continuation:
                for start in range(8,row['index']-7,8):
                    path = root/f'batch-{start:03d}-review.json'
                    if not path.is_file():
                        raise ValueError('Independent batch review absent')
                    if json.loads(path.read_bytes()) != batch_review(admitted,start):
                        raise ValueError('Independent batch review evidence differs')
            budget = binding['budget']
            if continuation:
                start = row['index'] // 8 * 8
                batch = [r for r in report['rows'][start:row['index']]
                         if r['status']=='accepted']
                unclaimed = 8-len(batch)
                batch_cpu = sum(r['job_accounting']['cpu_ticks'] for r in batch)
                batch_wall = sum(r['job_accounting']['wall_seconds'] for r in batch)
                batch_archive = sum(path.stat().st_size for r in batch
                                    for path in (root/ordered[r['index']]['attempt']).rglob('*')
                                    if path.is_file())
                if (batch_cpu + unclaimed*50_000_000 > 400_000_000
                        or batch_wall + unclaimed*10 > 80
                        or batch_archive + unclaimed*budget['archive_bytes_per_pair'] > 64*1048576):
                    raise ValueError('Continuation batch reservation exhausted')
            remaining = binding['budget']['pairs']-len(accepted)
            # The 1 GiB cap is for attempt archives. Control files already
            # occupy disk and are reflected in the physical free-space check.
            used = sum(path.stat().st_size
                       for index in accepted
                       for path in (root/ordered[index]['attempt']).rglob('*')
                       if path.is_file())
            reservation = remaining*budget['archive_bytes_per_pair']
            cpu = sum(r['job_accounting']['cpu_ticks'] for r in report['rows'] if r['status']=='accepted')
            wall = sum(r['job_accounting']['wall_seconds'] for r in report['rows'] if r['status']=='accepted')
            if (cpu + remaining*50_000_000 > budget['cpu_seconds']*10_000_000
                    or wall + remaining*10 > budget['job_wall_seconds']):
                raise ValueError('Campaign aggregate Job reservation exhausted')
            if (used + reservation > budget['archive_bytes'] or
                    shutil.disk_usage(root).free < reservation + custody.FREE_MIN):
                raise ValueError('Campaign archive or disk reservation exhausted')
            directory = root/row['attempt']
            command = [binding['python'],'-I','-S','-B',binding['worker'],
                       str(directory/'00-pending.json'),gate.TOKEN]
            gate.admitted(directory,checkout,command,gate.OWNER,row['context_sha256'],
                          gate.LIMITS,pins)
            return custody.transaction(directory,command=command,cwd=checkout,pins=pins,
                expected_account=gate.OWNER,context=row['context_sha256'],referee=None,
                consent=gate.TOKEN)
        finally:
            lock.seek(0)
            msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--supervised-eight', action='store_true')
    mode.add_argument('--review-supervised-eight', action='store_true')
    mode.add_argument('--continuation', action='store_true')
    mode.add_argument('--review-continuation', action='store_true')
    args = parser.parse_args()
    print(json.dumps(review_pilot(continuation=args.review_continuation)
                     if args.review_supervised_eight or args.review_continuation
                     else run_next(pilot=args.supervised_eight, continuation=args.continuation)))
