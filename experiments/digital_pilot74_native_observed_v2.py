"""Unqualified finite observed-job runner derivative; no automatic execution.

Retained capped Job/bootstrap/closure helpers unchanged. Missing while-alive
producer birth is UNKNOWN and cannot authenticate stopped publication.
"""
import json,os,sys,subprocess,threading,time
from pathlib import Path
from experiments.process_limits import Limits,Job,process_exited,OUTPUT_LIMIT
from experiments.digital_pilot74_journal import birth

def run(command, limits=Limits(), cwd=None):
    limits.validate()
    if not isinstance(command, (list, tuple)) or not command or any(not isinstance(s, str) or not s or '\x00' in s for s in command):
        raise ValueError('Explicit nonempty argument vector required')
    if os.name != 'nt':
        raise OSError('Windows only; command was not started')
    job, process, reader = Job(limits), None, None
    kept, counts = bytearray(), {'bytes': 0}
    observed = {}
    def capture_owned():
        for pid in job.pids():
            creation = birth(pid)
            if creation is None:continue  # UNKNOWN is never fabricated identity.
            if pid in observed and observed[pid] != creation:raise RuntimeError('Job PID birth changed')
            observed[pid] = creation
    def drain():
        while True:
            block = process.stdout.read(65536)
            if not block:
                return
            counts['bytes'] += len(block)
            kept.extend(block[:max(0, OUTPUT_LIMIT - len(kept))])
    started = time.monotonic()
    timed_out = False
    supervisor_cpu_stop = False
    try:
        # The known stdlib bootstrap uses the existing base interpreter directly.
        # Windows venv redirectors consume additional job process slots.
        bootstrap_python = getattr(sys, '_base_executable', sys.executable)
        bootstrap = [bootstrap_python, '-B', '-m', 'experiments.process_limits', '--bootstrap', json.dumps(list(command))]
        process = subprocess.Popen(bootstrap, cwd=cwd or Path(__file__).resolve().parents[1],
                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   close_fds=True, shell=False)
        # Known bootstrap cannot start command before this assignment succeeds.
        job.assign(process)
        capture_owned()
        reader = threading.Thread(target=drain, daemon=True)
        reader.start()
        process.stdin.write(b'go\n')
        process.stdin.close()
        while process.poll() is None:
            capture_owned()
            if job.usage()['user_cpu_seconds'] >= limits.cpu_seconds:
                supervisor_cpu_stop = True
                job.terminate()
                process.wait(timeout=5)
                break
            remaining = limits.wall_seconds - (time.monotonic() - started)
            if remaining <= 0:
                timed_out = True
                job.terminate()
                process.wait(timeout=5)
                break
            try:
                process.wait(timeout=min(0.01, remaining))
            except subprocess.TimeoutExpired:
                pass
        capture_owned()
        usage = job.usage()
        owned_pids = sorted(set(job.pids() + [process.pid] + list(observed)))
        job.close()  # Kill residual descendants on normal exits too.
        if not all(process_exited(pid) for pid in owned_pids):
            raise RuntimeError('Owned process still active after whole-job closure')
        reader.join(timeout=5)
        if reader.is_alive():
            raise RuntimeError('Output pipe stayed open after whole-job closure')
        return dict(schema='resource01-result-v1', platform='Windows', command=list(command),
                    bootstrap_python=bootstrap_python,
                    limits=vars(limits), exit_code=process.returncode, timed_out=timed_out,
                    supervisor_cpu_stop=supervisor_cpu_stop,
                    owned_pids_before_close=owned_pids, post_close_processes_exited=True,
                    observed_job_processes=[dict(pid=pid,creation_filetime_decimal=str(creation)) for pid,creation in sorted(observed.items())],
                    elapsed_seconds=time.monotonic()-started, usage=usage,
                    output=kept.decode('utf-8', errors='replace'),
                    output_bytes=counts['bytes'], retained_bytes=len(kept),
                    output_truncated=counts['bytes'] > len(kept), isolation_verified=False)
    finally:
        job.close()
        if process is not None:
            if process.poll() is None:
                process.terminate()  # Also covers an unassigned waiting bootstrap.
                process.wait(timeout=5)
            if reader is not None:
                reader.join(timeout=5)
            for stream in (process.stdin, process.stdout):
                if stream is not None:
                    stream.close()
