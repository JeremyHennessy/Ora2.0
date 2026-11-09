"""Lower-assurance Job transport for one AL02 worker or inert smoke worker."""
import ctypes
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time

from experiments.process_limits import (
    Accounting, Job, Limits, OUTPUT_LIMIT, checked, process_exited,
)

LIMITS = Limits(wall_seconds=10)
FLAGS = 0x4 | 0x8 | 0x200 | 0x2000

# The relay receives one bounded frame after assignment, then forwards it on
# a new anonymous stdin pipe. EOF is part of the protocol.
RELAY = """import json, subprocess, sys
frame = sys.stdin.buffer.read(513)
if not frame or len(frame) > 512:
    raise SystemExit(125)
raise SystemExit(subprocess.run(json.loads(sys.argv[1]), input=frame,
                               shell=False, close_fds=True).returncode)
"""


class PairJob(Job):
    def usage(self):
        result = super().usage()
        counters = Accounting()
        checked(self.k.QueryInformationJobObject(
            self.handle, 1, ctypes.byref(counters), ctypes.sizeof(counters), None))
        return dict(result, user_ticks=counters.user, kernel_ticks=counters.kernel,
                    started_processes=counters.total_processes,
                    active_before_close=counters.active_processes)


def relay_argv(python, command):
    return [python, '-I', '-S', '-B', '-c', RELAY, json.dumps(command)]



def run(command, cwd, *, before_go=None, capture=None, environment=None, relay=False):
    """Return raw bounded stdout and lower-assurance receipts. Never retries."""
    if os.name != 'nt' or not command or any(type(x) is not str or not x for x in command):
        raise ValueError('Explicit Windows worker command required')
    if relay and before_go is None:
        raise ValueError('Relay requires pre-go admission')
    job = PairJob(LIMITS)
    process = reader = None
    overflow, eof = threading.Event(), threading.Event()
    data = bytearray()
    capture_failed = threading.Event()
    reason = None
    start = time.monotonic()

    def drain():
        while True:
            chunk = process.stdout.read1(16384)
            if not chunk:
                eof.set()
                return
            remaining = OUTPUT_LIMIT - len(data)
            kept = chunk[:remaining]
            data.extend(kept)
            if capture is not None and kept:
                try:
                    capture(kept)
                except OSError:
                    capture_failed.set()
            if len(chunk) > remaining:
                overflow.set()

    try:
        initial = job.usage()
        if initial['flags'] != FLAGS or initial['started_processes']:
            raise ValueError('Fresh Job flags or initial census mismatch')
        python = getattr(sys, '_base_executable', sys.executable)
        bootstrap = Path(__file__).with_name('process_limits.py').resolve(strict=True)
        argv = (relay_argv(python, command) if relay else
                [python, '-I', '-S', '-B', str(bootstrap), '--bootstrap', json.dumps(command)])
        process = subprocess.Popen(
            argv,
            cwd=cwd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, close_fds=True, shell=False, env=environment)
        job.assign(process)
        reader = threading.Thread(target=drain, daemon=True)
        reader.start()
        binding = None
        if before_go is not None:
            binding = before_go(python, tuple(argv) if relay else bootstrap, process, job.usage())
        if before_go is not None:
            settled = job.usage()
            if (settled['started_processes'] != 1 or settled['active_before_close'] != 1
                    or settled['user_ticks'] + settled['kernel_ticks'] >= 50_000_000):
                raise RuntimeError('Job census or CPU budget failed before go')
        if time.monotonic() - start >= LIMITS.wall_seconds:
            raise TimeoutError('Job deadline reached before go')
        if relay:
            if not isinstance(binding, str) or len(binding) != 64 or any(
                    char not in '0123456789abcdef' for char in binding):
                raise ValueError('Invalid pre-go release binding')
            frame = json.dumps(dict(version=1, journal=binding, relay_pid=process.pid,
                                    expires=start + LIMITS.wall_seconds)).encode('ascii')
            process.stdin.write(frame)
        else:
            process.stdin.write(b'go\n')
        process.stdin.close()
        while True:
            usage = job.usage()
            if capture_failed.is_set():
                reason = 'raw_capture_failed'
            elif overflow.is_set():
                reason = 'output_overflow'
            elif time.monotonic() - start >= LIMITS.wall_seconds:
                reason = 'wall_timeout'
            elif usage['user_ticks'] + usage['kernel_ticks'] >= 50_000_000:
                reason = 'combined_cpu_observed'
            elif usage['started_processes'] > 2:
                reason = 'unexpected_process_birth'
            if reason:
                job.terminate()
                break
            if process.poll() is not None and not usage['active_before_close'] and eof.is_set():
                break
            overflow.wait(0.005)
        process.wait(timeout=5)
        reader.join(timeout=5)
        final = job.usage()
        if reason is None and capture_failed.is_set():
            reason = 'raw_capture_failed'
        if reason is None and overflow.is_set():
            reason = 'output_overflow'
        owned = sorted(set(job.pids() + [process.pid]))
        job.close()
        closed = all(process_exited(pid) for pid in owned)
        accepted = (not reason and not overflow.is_set() and process.returncode == 0
                    and eof.is_set() and closed and final['active_before_close'] == 0
                    and final['started_processes'] == 2
                    and final['user_ticks'] + final['kernel_ticks'] < 50_000_000
                    and final['windows_reported_peak_job_memory_bytes'] <= LIMITS.memory_bytes
                    and time.monotonic() - start < LIMITS.wall_seconds)
        return bytes(data), dict(accepted=accepted, reason=reason, initial=initial,
                                 final=final, exit_code=process.returncode, eof=eof.is_set(),
                                 observed_pids=owned, observed_closed=closed,
                                 elapsed_seconds=time.monotonic()-start,
                                 output_overflow=overflow.is_set(),
                                 retained_bytes=len(data), limits=vars(LIMITS))
    finally:
        job.close()
        if process is not None:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=5)
            if reader is not None:
                reader.join(timeout=5)
            for stream in (process.stdin, process.stdout):
                stream.close()
