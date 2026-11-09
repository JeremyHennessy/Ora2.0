"""One-claim campaign controller. Inactive source always refuses execution."""
from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess

from experiments import al02_campaign_admission as gate
from experiments import al02_one_pair_custody as custody
from tools.al02_campaign_evidence import analyze_committed_panel, next_unclaimed

# Downstream identity, outside the binding that the admission module embeds.
ADMISSION_SHA256 = '07b292f2a921b353d8dfe866442b024ebef8d73de307ddcd15c153c21b35a84c'


def run_next():
    # No writes, including lock creation, before authority is present.
    if gate.AUTHORIZATION_SHA256 is None:
        raise ValueError('Campaign scientific authorization absent')
    import msvcrt
    binding = gate.binding()
    ordered = gate.inventory()
    root = custody.pinned_path(gate.DESTINATION)
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
        msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
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
            report = analyze_committed_panel(root,ordered,admitted)
            accepted = [r['index'] for r in report['rows'] if r['status']=='accepted']
            row = next_unclaimed(root,ordered,accepted,stop=gate.STOP)
            if row is None:
                return None
            budget = binding['budget']
            remaining = len(ordered)-len(accepted)
            used = sum(path.stat().st_size for path in root.rglob('*') if path.is_file())
            reservation = remaining*budget['archive_bytes_per_pair']
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
    print(json.dumps(run_next()))
