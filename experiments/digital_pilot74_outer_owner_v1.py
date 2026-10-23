"""Prospective handle-only original-owner boundary; no CLI or task writer.

No grant issuer. A separately authenticated original owner supplies admission.
Four CONTAINED processes permit caller/G/W/C; the trusted owner is a fifth
physical process outside that Job. No machine-wide confinement is claimed.
"""
import ctypes
import os
import subprocess
from ctypes import wintypes as wt
from pathlib import Path
from experiments import process_limits as caps
from experiments import digital_pilot74_guardian_boundary_qualifier_v2 as win
from experiments.digital_pilot74_guardian_v1 import failure_observation, attach_failure_evidence, failure_note
from experiments.digital_pilot74_guardian_preresume_v1 import observe_job_live

MIB = 1024**2


def launch(request, admission_check):
    """No writes, pipes, bootstrap, polling, extra deadline or automatic retry.

    admission_check must authenticate live original owner/birth/lock/expiry,
    source, executable/command, native/caller pins, grants and independent gates.
    This callable cannot supply that authority. Never call on a template grant.
    """
    if os.name != 'nt':
        raise OSError('Windows only')
    k = win.kernel()
    started = int(k.GetTickCount64())
    wall_ms = request.get('wall_ms', 3600000)
    if type(wall_ms) is not int or not 1 <= wall_ms <= 3600000:
        raise ValueError('Only a shorter finite outer deadline may be registered')
    deadline = started + wall_ms  # before admission, allocation or caller setup
    job = None
    pi = win.PI()
    initialized = False
    attrs = None
    birth = None
    result = None
    caller_exit_code = None
    first = None
    phase = 'admission'
    evidence = None
    try:
        if admission_check(request) is not True:
            raise ValueError('Independent original-owner admission refused')
        command = request['command']
        if (type(command) is not list or not command or
                not all(type(x) is str and x and '\0' not in x for x in command)
                or len(subprocess.list2cmdline(command)) > 12000
                or not Path(command[0]).is_absolute() or not Path(request['cwd']).is_absolute()):
            raise ValueError('Pinned bounded absolute caller command required')
        if int(k.GetTickCount64()) >= deadline:
            raise TimeoutError('Original outer deadline exhausted before creation')
        phase = 'create'
        job = caps.Job(caps.Limits(memory_bytes=2048*MIB, cpu_seconds=2400, processes=4, wall_seconds=3600))
        size = ctypes.c_size_t()
        k.InitializeProcThreadAttributeList(None, 1, 0, ctypes.byref(size))
        attrs = ctypes.create_string_buffer(size.value)
        win.checked(k.InitializeProcThreadAttributeList(attrs, 1, 0, ctypes.byref(size)))
        initialized = True
        jobs = (wt.HANDLE * 1)(job.handle)
        win.checked(k.UpdateProcThreadAttribute(attrs, 0, 0x2000D, jobs, ctypes.sizeof(jobs), None, None))
        start = win.STARTEX()
        start.startup.cb = ctypes.sizeof(start)
        start.attributes = ctypes.cast(attrs, ctypes.c_void_p)
        line = ctypes.create_unicode_buffer(subprocess.list2cmdline(command))
        if int(k.GetTickCount64()) >= deadline:
            raise TimeoutError('Original outer deadline exhausted during setup')
        # Atomically assigned while suspended; no inherited owner/Job handles.
        win.checked(k.CreateProcessW(None, line, None, None, False, 0x80000 | 0x4 | 0x8,
            None, request['cwd'], ctypes.byref(start), ctypes.byref(pi)))
        phase = 'identity'
        birth = win.birth(k, pi.process)
        member = wt.BOOL()
        win.checked(k.IsProcessInJob(pi.process, job.handle, ctypes.byref(member)))
        if not member.value or int(k.GetProcessId(pi.process)) != pi.pid:
            raise ValueError('Original caller handle/PID/Job mismatch')
        image = ctypes.create_unicode_buffer(32768)
        length = wt.DWORD(len(image))
        win.checked(k.QueryFullProcessImageNameW(pi.process, 0, image, ctypes.byref(length)))
        if Path(image.value).resolve() != Path(command[0]).resolve():
            raise ValueError('Caller image mismatch')
        usage = job.usage()
        if (usage['configured_memory_bytes'] != 2048*MIB or usage['configured_processes'] != 4
                or usage['configured_cpu_ticks'] != 2400*10_000_000
                or usage['flags'] & 0x220c != 0x220c or usage['flags'] & 0x1800):
            raise ValueError('Outer Job readback mismatch/breakaway')
        if int(k.GetTickCount64()) >= deadline:
            raise TimeoutError('Original outer deadline exhausted before resume')
        phase = 'wait'
        if k.ResumeThread(pi.thread) != 1:
            raise OSError('Caller suspended resume failed')
        remaining = max(0, deadline - int(k.GetTickCount64()))
        if k.WaitForSingleObject(pi.process, remaining) != 0:
            raise TimeoutError('Outer absolute deadline/unknown wait; never extend')
        code = wt.DWORD()
        win.checked(k.GetExitCodeProcess(pi.process, ctypes.byref(code)))
        caller_exit_code = int(code.value)
        usage = job.usage()
        pids = job.pids()
        if usage['active_before_close'] != 0 or pids != []:
            raise RuntimeError('Caller exit is not whole outer Job closure')
        elapsed = int(k.GetTickCount64()) - started
        if elapsed > wall_ms:
            raise TimeoutError('Outer elapsed ceiling exceeded')
        result = dict(schema='PILOT74-OUTER-OWNER-OBSERVATION-v1', command=command, pid=pi.pid,
            creation_filetime_decimal=str(birth), image=image.value, exit_code=int(code.value),
            elapsed_ms=elapsed, wall_limit_ms=wall_ms, usage=usage, pids=pids, process_handle_signaled=True,
            closure_observed=True, owner_outside_job=True, physical_process_count_can_be_five=True,
            publication_accepted=False, live_attachment=False)
        return result
    except BaseException as error:
        first = error
        # Evidence collection can fail; it must never prevent owned termination.
        try:
            evidence = dict(schema='PILOT74-OUTER-OWNER-FAILURE-v1', phase=phase,
                command=request.get('command'), caller_exit_code=caller_exit_code,
                before_termination=failure_observation(job, k, pi.process, pi.pid, birth, phase),
                termination_requested=False, after_termination=None, closure_observed=False,
                original_deadline_ms=deadline, publication_accepted=False, live_attachment=False)
        except BaseException as diagnostic:
            failure_note(error, 'Outer diagnostic unavailable: ', diagnostic)
        if evidence is not None and job is not None:
            try:
                if int(k.GetTickCount64()) < deadline:
                    evidence['owned_identity_snapshot_before_termination'] = observe_job_live(job,pi.process,pi.pid,birth)
                else:
                    evidence['owned_identity_snapshot_before_termination'] = None
                    evidence['owned_identity_snapshot_skipped'] = 'absolute deadline exhausted;termination takes precedence'
            except BaseException as diagnostic:
                failure_note(error, 'Outer owned-image snapshot unavailable: ', diagnostic)
        if job is not None:
            try:
                job.terminate()
                if evidence is not None:
                    evidence['termination_requested'] = True
            except BaseException as termination:
                failure_note(error, 'Outer Job termination failed;UNKNOWN: ', termination)
        if evidence is not None:
            try:
                evidence['after_termination'] = failure_observation(job, k, pi.process, pi.pid, birth, phase)
                attach_failure_evidence(error, evidence)
            except BaseException as diagnostic:
                failure_note(error, 'Outer terminal diagnostic unavailable: ', diagnostic)
        raise
    finally:
        cleanup = []
        if job is not None:
            cleanup.append(job.close)
        if pi.thread:
            cleanup.append(lambda: win.checked(k.CloseHandle(pi.thread)))
        if pi.process:
            cleanup.append(lambda: win.checked(k.CloseHandle(pi.process)))
        if initialized:
            cleanup.append(lambda: k.DeleteProcThreadAttributeList(attrs))
        errors = []
        for close in cleanup:
            try:
                close()
            except BaseException as error:
                try:
                    errors.append(repr(error))
                except BaseException:
                    errors.append('<cleanup diagnostic unavailable>')
        if errors:
            if first is not None:
                failure_note(first, 'Outer cleanup UNKNOWN: ', errors)
            else:
                error = OSError('Outer cleanup UNKNOWN: ' + repr(errors))
                attach_failure_evidence(error, dict(last_completed_observation=result,
                    cleanup_errors=errors, closure_observed=False))
                raise error
