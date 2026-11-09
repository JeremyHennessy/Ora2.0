"""Verify a retained lower-assurance pair against independently admitted identities."""
from hashlib import sha256
import json

from experiments.al02_depletion_checkpoint import _canonical
from tools.al02_natural_b_analysis import analyze_pair, contexts, summarize

RECEIPTS = ('00-pending.json', '01-verified.json', '02-release-intent.json', '03-transport.json')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def bounded(path, limit):
    with path.open('rb') as stream:
        raw = stream.read(limit + 1)
    require(0 < len(raw) <= limit, f'Invalid extent: {path.name}')
    return raw


def digest(raw):
    return sha256(raw).hexdigest()


def verify_attempt(directory, context, *, command, pins, identities, terminal_pin):
    """Read-only join. terminal_pin and launch inputs must come from trusted review.

    This does not authenticate an owner, approve execution, or promote the
    lower-assurance evidence tier. A self-computed terminal pin is insufficient.
    """
    require(directory.name == context['attempt'], 'Attempt directory differs')
    require(not (directory/'99-failed.json').exists(), 'Failure and terminal conflict')
    require(command[5] == str(directory/'00-pending.json'), 'Attempt command differs')
    label = context['context'].encode('ascii')
    require(digest(label) == context['context_sha256']
            and int(context['context_sha256'][:16],16) == context['seed'], 'Context seed differs')
    terminal_raw = bounded(directory/'04-terminal.json', 1048576)
    require(digest(terminal_raw) == terminal_pin, 'Terminal pin differs')
    terminal = json.loads(terminal_raw)
    require(set(terminal['receipt_sha256']) == set(RECEIPTS), 'Receipt set differs')
    receipts = [bounded(directory/name, 1048576) for name in RECEIPTS]
    require(all(digest(raw) == terminal['receipt_sha256'][name]
                for name,raw in zip(RECEIPTS,receipts)), 'Receipt digest differs')
    pending, verified, intent, transport = map(json.loads,receipts)
    require(all(row['release_identities'] == identities
                for row in (pending, verified, intent, transport, terminal)), 'Release identity differs')
    require(pending['context'] == context['context_sha256']
            and pending['command'] == command and pending['pins'] == pins
            and pending['evidence_tier'] == 'LOW_ASSURANCE_EXPLORATORY', 'Pending admission differs')
    require(verified['pending_sha256'] == digest(receipts[0])
            and intent['verified_sha256'] == digest(receipts[1]), 'Release journal linkage differs')
    job = transport['receipt']
    limits = dict(cpu_seconds=5, wall_seconds=10, memory_bytes=134217728, processes=3)
    final = job['final']
    require(pending['limits'] == job['limits'] == limits
            and job['accepted'] is True and job['observed_closed'] is True and job['eof'] is True
            and job['exit_code'] == 0 and not job['output_overflow']
            and final['active_before_close'] == 0 and final['started_processes'] == 2
            and verified['bootstrap_pid'] in job['observed_pids']
            and 0 <= final['user_ticks'] + final['kernel_ticks'] < 50000000
            and 0 <= job['elapsed_seconds'] <= 10
            and 0 <= final['windows_reported_peak_job_memory_bytes'] <= 134217728,
            'Job closure or resource limits differ')
    raw = bounded(directory/'raw.bin',1048576)
    require(digest(raw) == terminal['raw_sha256'] == transport['raw_sha256']
            and len(raw) == job['retained_bytes'], 'Raw identity differs')
    payload = json.loads(raw)
    require(_canonical(payload) == raw and set(payload) == {
        'context_sha256','checkpoint','checkpoint_sha256','branches'}
        and payload['context_sha256'] == context['context_sha256'], 'Raw context or format differs')
    checkpoint = payload['checkpoint'].encode('ascii')
    prefix = json.loads(checkpoint)['state']['events']
    expected = [dict(phase='prefix',event=event) for event in prefix]
    for role in ('accessible','sequestered'):
        expected.extend(dict(phase=role,event=event) for event in payload['branches'][role]['events'])
    journal = bounded(directory/'partial.jsonl',1048576)
    require(transport['partial'] == dict(bytes=len(journal),sha256=digest(journal))
            and journal == b''.join(_canonical(row)+b'\n' for row in expected),
            'Journal differs')
    analysis = analyze_pair(context['seed'],checkpoint,payload['checkpoint_sha256'],payload['branches'])
    require(analysis['result'] == terminal['result']
            and analysis['result']['authenticated_execution'] is False, 'Referee verdict differs')
    return dict(index=context['index'],status='accepted',terminal_sha256=terminal_pin,
                raw_sha256=digest(raw),journal_sha256=digest(journal),
                job_accounting=dict(cpu_ticks=final['user_ticks']+final['kernel_ticks'],
                                    wall_seconds=job['elapsed_seconds']),**analysis)


def next_unclaimed(root, ordered, accepted_indices, *, stop):
    """Plan only. Existing failed, incomplete or unreviewed claims halt."""
    require(len(ordered) == 128 and [r['index'] for r in ordered] == list(range(128)),
            'Invalid ordered campaign inventory')
    names = [f'attempt-{index:03d}' for index in range(128)]
    require([r['attempt'] for r in ordered] == names, 'Invalid attempt names')
    if stop.exists():
        return None
    existing = {path.name for path in root.iterdir() if path.name.startswith('attempt-')}
    accepted = set(accepted_indices)
    require(len(accepted) == len(accepted_indices), 'Duplicate accepted index')
    require(accepted <= set(range(128)), 'Invalid accepted index')
    require(existing == {names[i] for i in accepted}, 'Unreconciled attempt claim')
    require(accepted == set(range(len(accepted))), 'Noncontiguous campaign progress')
    return ordered[len(accepted)] if len(accepted) < 128 else None


def analyze_committed_panel(root, ordered, admissions):
    """Summarize only rows verified against independently admitted receipts.

    Admission records supply reviewed launch identities and terminal digests,
    never derived scientific outcomes. Unadmitted terminal directories halt.
    """
    require(ordered == contexts(), 'Frozen context mapping differs')
    require(set(admissions) <= set(range(128)), 'Unknown admission index')
    terminal_pins = [row['terminal_pin'] for row in admissions.values()]
    require(len(set(terminal_pins)) == len(terminal_pins), 'Duplicate evidence ownership')
    rows = []
    for context in ordered:
        index = context['index']
        attempt = root/context['attempt']
        if index in admissions:
            identities = admissions[index]['identities']
            require(not identities.get('inert_execution') and
                    identities.get('context_index') == index and
                    identities.get('seed') == context['seed'],
                    'Campaign scientific identity differs')
            rows.append(verify_attempt(attempt, context, **admissions[index]))
        elif (attempt/'04-terminal.json').exists():
            raise ValueError('Terminal receipt lacks independent admission')
        else:
            status = ('failed' if (attempt/'99-failed.json').exists() else
                      'missing' if attempt.exists() else 'not_run')
            rows.append(dict(index=index,status=status))
    return dict(rows=rows,summary=summarize(rows))
