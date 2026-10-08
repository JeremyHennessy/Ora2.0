"""Offline local receipt display; reported results are not independent audits."""
from datetime import datetime, timezone
import hashlib
import html
import json
from pathlib import Path
import platform
import stat

MAX_RECEIPT = 1024*1024
MAX_RUNS = 1024


def unique(pairs):
    values = {}
    for key, value in pairs:
        if key in values:
            raise ValueError('Duplicate receipt key')
        values[key] = value
    return values


def regular(path):
    info = path.lstat()
    if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0):
        raise ValueError('Linked/reparse path rejected')
    return info


def revision(value):
    return isinstance(value, str) and len(value) == 40 and all(c in '0123456789abcdef' for c in value)


def collect(root):
    root = Path(root)
    runs = root/'runs'
    regular(runs)
    entries = []
    for entry in runs.iterdir():
        entries.append(entry)
        if len(entries) > MAX_RUNS:
            raise ValueError('Bounded local run inventory exceeded')
    entries.sort(key=lambda p: p.name, reverse=True)
    rows = []
    for folder in entries:
        path = folder/'manifest.json'
        try:
            info = regular(folder)
            if not stat.S_ISDIR(info.st_mode):
                continue
            try:
                info = regular(path)
            except FileNotFoundError:
                continue
            if not stat.S_ISREG(info.st_mode):
                raise ValueError('Regular manifest required')
            with path.open('rb') as stream:
                raw = stream.read(MAX_RECEIPT+1)
            if len(raw) > MAX_RECEIPT:
                raise ValueError('Bounded receipt size exceeded')
            r = json.loads(raw.decode('utf-8-sig'), object_pairs_hook=unique)
            if not isinstance(r, dict):
                raise ValueError('Object receipt required')
            issues = []
            run_id = r.get('run_id')
            label_source = 'run_id'
            if not isinstance(run_id, str) or not 1 <= len(run_id) <= 200:
                run_id, label_source = folder.name, 'directory'
            candidates = {k: r[k] for k in ('source_revision', 'revision') if k in r}
            valid = bool(candidates) and all(revision(v) for v in candidates.values()) and len(set(candidates.values())) == 1
            source = next(iter(candidates.values())) if valid else None
            if not valid:
                issues.append('Source revision unavailable or ambiguous')
            status = r.get('status')
            if not isinstance(status, str) or not 1 <= len(status) <= 200:
                status = 'unknown'
                issues.append('Reported status unavailable')
            tests = r.get('passed_tests')
            tests = tests if type(tests) is int and 0 <= tests <= 1000000 else None
            rows.append(dict(run_id=run_id, label_source=label_source, reported_status=status, source_revision=source,
                             source_fields=list(candidates), reported_passed_tests=tests, issues=issues,
                             receipt_path=str(path), receipt_sha256=hashlib.sha256(raw).hexdigest(), receipt=r,
                             independently_audited=False, process_health='unverified'))
        except (ValueError, OSError, UnicodeError, json.JSONDecodeError) as exc:
            rows.append(dict(run_id=folder.name, label_source='directory', reported_status='unreadable_receipt', source_revision=None,
                             source_fields=[], reported_passed_tests=None, issues=[str(exc)], receipt_path=str(path), receipt=None,
                             receipt_sha256=None, independently_audited=False, process_health='unverified'))
    return rows


def report(root, repositories, generated_utc=None):
    return dict(schema='oralab-status-v2', generated_utc=generated_utc or datetime.now(timezone.utc).isoformat(), root=str(Path(root)),
                python=platform.python_version(), repositories=repositories, runs=collect(root), continuous_runtime='Not configured',
                checkpoint_evidence='Bounded recovery receipts exist; inspect their source-pinned independent audits',
                independent_backup='Unverified; current evidence restoration is on D:',
                power_loss_recovery='Unverified', hardened_isolation='Unverified', process_health='unverified')


def render(r):
    esc = lambda v: html.escape(str(v), quote=True)
    rows = []
    for row in r['runs']:
        status = row['reported_status']
        if row['reported_passed_tests'] is not None:
            status += f"; {row['reported_passed_tests']} tests reported"
        if row['issues']:
            status += '; '+ '; '.join(row['issues'])
        source = row['source_revision'][:12] if row['source_revision'] else 'unknown'
        rows.append('<tr><td>'+esc(row['run_id'])+'</td><td>'+esc(status)+'</td><td>'+esc(source)+'</td></tr>')
    return '<!doctype html><meta charset="utf-8"><title>Ora 2.0 Laboratory</title><style>body{font:16px Segoe UI,sans-serif;max-width:1100px;margin:40px auto;padding:20px;background:#101827;color:#e5edf5}h1{color:#8cddd0}td,th{text-align:left;padding:12px;border-bottom:1px solid #39485c}table{width:100%}code{color:#8cddd0}</style><h1>Ora 2.0 · Local Laboratory</h1><p>Bounded, reproducible experiments on this computer. No hosting subscription or API required.</p><p>Updated: '+esc(r['generated_utc'])+'</p><table><tr><th>Run</th><th>Reported result</th><th>Code revision</th></tr>'+''.join(rows)+'</table><p>Receipt display is read-only; reported results are not independently verified by this page. A heartbeat or running label does not establish process health, learning or self-maintenance.</p><p>Bounded checkpoint recovery has source-pinned receipts. Continuous operation is not configured. Independent off-drive backup, physical power-loss recovery and hardened isolation remain unverified.</p><p>Local checkout versions are preserved separately from each run\'s source version: '+esc(json.dumps(r['repositories'],sort_keys=True))+'</p><p>Run <b>Lab Status.cmd</b> to refresh this report.</p>'


def refresh(root, repositories, generated_utc=None):
    root = Path(root)
    value = report(root, repositories, generated_utc)
    page = render(value)
    output = root/'observer'
    output.mkdir(exist_ok=True)
    regular(output)
    for name, text in [('status.json', json.dumps(value,indent=2)+'\n'), ('index.html', page)]:
        path = output/name
        pending = output/(name+'.tmp')
        for candidate in (path, pending):
            if candidate.exists() or candidate.is_symlink():
                regular(candidate)
        pending.write_text(text,encoding='utf-8')
        pending.replace(path)
    return value
