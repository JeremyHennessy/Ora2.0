"""One-claim campaign controller. Inactive source always refuses execution."""
import json
from pathlib import Path
import shutil
import subprocess

from experiments import al02_campaign_admission as gate
from experiments import al02_one_pair_custody as custody
from tools.al02_campaign_evidence import analyze_committed_panel, next_unclaimed

# Downstream identity, outside the binding that the admission module embeds.
ADMISSION_SHA256 = '8c924e5b4a5a84d8c1901f137136d402668f188c3f3bc84e70a66a1a20e55711'


def pilot_admissions(root, ordered, binding, checkout, pins):
    """Derive lower-assurance admission inputs from custody, with no review ledger."""
    admitted = {}
    for item in ordered[:8]:
        directory = root/item['attempt']
        terminal = directory/'04-terminal.json'
        if not terminal.exists():
            continue
        command = [binding['python'],'-I','-S','-B',binding['worker'],
                   str(directory/'00-pending.json'),gate.TOKEN]
        identity = gate.admitted(directory,checkout,command,gate.OWNER,
                                 item['context_sha256'],gate.LIMITS,pins)
        source_path = str(checkout/'experiments/al02_one_pair.py')
        identity.update(referee_entry='experiments.al02_one_pair.verify_context',
                        referee_sha256=pins[source_path])
        admitted[item['index']] = dict(command=command,pins=pins,identities=identity,
                                      terminal_pin=custody.digest(terminal))
    return admitted


def review_pilot():
    """Read-only batch reanalysis, with missing outcomes retained."""
    from statistics import mean, stdev
    binding = gate.pilot_binding()
    ordered = gate.inventory()
    root = custody.pinned_path(gate.PILOT_DESTINATION)
    checkout = custody.pinned_path(gate.CHECKOUT)
    source = str(checkout/'experiments/al02_campaign_admission.py')
    pins = dict(binding['pins'], **{source: ADMISSION_SHA256})
    for path, expected in pins.items():
        if custody.digest(path) != expected:
            raise ValueError(f'Pilot review source differs: {path}')
    admissions = pilot_admissions(root, ordered, binding, checkout, pins)
    rows = analyze_committed_panel(root, ordered, admissions)['rows'][:8]
    differences = [row['result']['contrast'] for row in rows if row['status']=='accepted']
    complete = len(differences)==8
    return dict(scope='supervised lower assurance; batch review required', rows=rows,
                committed=8, accepted=len(differences), distribution=differences,
                all_context_mean=mean(differences) if complete else None,
                all_context_se=stdev(differences)/8**0.5 if complete else None,
                observed_only_mean=mean(differences) if differences else None)


def run_next(*, pilot=False):
    # No writes, including lock creation, before authority is present.
    authority_pin = gate.PILOT_AUTHORIZATION_SHA256 if pilot else gate.AUTHORIZATION_SHA256
    if authority_pin is None:
        raise ValueError('Campaign scientific authorization absent')
    import msvcrt
    binding = gate.pilot_binding() if pilot else gate.binding()
    ordered = gate.inventory()
    root = custody.pinned_path(gate.PILOT_DESTINATION if pilot else gate.DESTINATION)
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
            if pilot:
                if admitted_path.exists():
                    raise ValueError('Strict review ledger is outside pilot scope')
                admitted = pilot_admissions(root, ordered, binding, checkout, pins)
            for index, review in admitted.items():
                if index not in range(128):
                    raise ValueError('Reviewed index outside commitment')
                committed = ordered[index]
                expected_command = [binding['python'],'-I','-S','-B',binding['worker'],
                                    str(root/committed['attempt']/'00-pending.json'),gate.TOKEN]
                identity = review['identities']
                if (review['command'] != expected_command or review['pins'] != pins
                        or identity['binding_sha256'] != gate.BINDING_SHA256
                        or identity['package_sha256'] != gate.PACKAGE_SHA256
                        or identity['contexts_sha256'] != gate.CONTEXTS_SHA256
                        or identity['authorization_sha256'] != authority_pin):
                    raise ValueError('Reviewed campaign release identity differs')
            report = analyze_committed_panel(root,ordered,admitted)
            accepted = [r['index'] for r in report['rows'] if r['status']=='accepted']
            row = next_unclaimed(root,ordered,accepted,stop=gate.STOP)
            if row is None or (pilot and row['index'] >= 8):
                return None
            budget = binding['budget']
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
    args = parser.parse_args()
    print(json.dumps(review_pilot() if args.review_supervised_eight
                     else run_next(pilot=args.supervised_eight)))
