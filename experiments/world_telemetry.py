"""Read-only authoritative telemetry; no service, UI or simulation execution."""
import ctypes as c
from ctypes import wintypes as w
from datetime import datetime,timezone
import hashlib
import os
from pathlib import Path
from experiments import heartbeat_template_audit as replay


def process_sample(pid):
    if type(pid) is not int or pid<=0: raise ValueError('Positive PID')
    if os.name!='nt': return dict(verified=False,pid=pid,reason='native_windows_probe_unavailable')
    kernel=c.WinDLL('kernel32',use_last_error=True)
    kernel.OpenProcess.argtypes=[w.DWORD,w.BOOL,w.DWORD]; kernel.OpenProcess.restype=w.HANDLE
    kernel.GetProcessTimes.argtypes=[w.HANDLE,*([c.POINTER(w.FILETIME)]*4)]; kernel.GetProcessTimes.restype=w.BOOL
    kernel.WaitForSingleObject.argtypes=[w.HANDLE,w.DWORD]; kernel.WaitForSingleObject.restype=w.DWORD
    kernel.CloseHandle.argtypes=[w.HANDLE]; kernel.CloseHandle.restype=w.BOOL
    handle=kernel.OpenProcess(0x101000,False,pid)  # QueryLimitedInformation + SYNCHRONIZE only.
    if not handle:
        error=c.get_last_error()
        return dict(verified=error==87,pid=pid,alive=False if error==87 else None,birth_filetime=None,reason='pid_absent' if error==87 else 'query_denied',winerror=error)
    try:
        times=[w.FILETIME() for _ in range(4)]
        if not kernel.GetProcessTimes(handle,*(c.byref(v) for v in times)):
            return dict(verified=False,pid=pid,reason='times_query_failed')
        wait=kernel.WaitForSingleObject(handle,0)
        if wait not in {0,258}: return dict(verified=False,pid=pid,reason='wait_query_failed')
        return dict(verified=True,pid=pid,alive=wait==258,birth_filetime=(times[0].dwHighDateTime<<32)|times[0].dwLowDateTime)
    finally: kernel.CloseHandle(handle)


def hashes(folder):
    return {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in Path(folder).iterdir() if p.is_file() and p.name!='writer.lock'}


def sample(folder,revision,binding=None,previous=None,current=None):
    """Binding is explicit operator provenance, never inferred from receipts/PIDs.

    Cache the returned previous sample locally. Live requires matching native
    process birth AND authoritative advancing, prefix-consistent state samples.
    """
    mode='recorded' if binding is None else 'live'
    moment=current or datetime.now(timezone.utc).isoformat()
    result=dict(schema='world-telemetry01-v1',mode=mode,validated=False,status='unknown',active=False,observed_utc=moment)
    try:
        before=hashes(folder)
        evidence=replay.inspect(folder,revision,current=moment)
        if before!=hashes(folder): raise ValueError('World changed during observation; retry')
        identity=evidence['manifest']['identity']; frame=evidence['frames'][-1]; report=evidence['report']
        result.update(validated=True,identity=identity,simulation_tick=report['verified_simulation_tick'],
            noise_cursor=frame['state']['noise_cursor'],frame_sha256=frame['frame_sha256'],
            state_sha256=frame['state_sha256'],world=frame['state']['world'],
            recorded_status=report['reported_status'],last_heartbeat_utc=frame['last_heartbeat'],world_hashes=before,process_health='unverified',
            last_event=next((f['event'] for f in reversed(evidence['frames']) if f['event'] is not None),None))
        if mode=='recorded': result['status']='recorded'; return result
        if set(binding)!={'pid','birth_filetime','world_id','run_id','source_revision'} or type(binding['birth_filetime']) is not int or binding['birth_filetime']<=0:
            raise ValueError('Complete explicit launch binding')
        if any(binding[k]!=identity[k] for k in ('world_id','run_id','source_revision')):
            raise ValueError('Launch/world identity mismatch')
        probe=process_sample(binding['pid']); result.update(process=probe,binding=dict(binding))
        if not probe['verified']: result['status']='process_unknown'; return result
        if probe.get('reason')=='pid_absent': result.update(status='stopped',process_health='stopped'); return result
        if probe['birth_filetime']!=binding['birth_filetime']:
            result['status']='process_identity_mismatch'; return result
        result['process_health']='running' if probe['alive'] else 'stopped'
        if not probe['alive'] or report['reported_status']=='stopped': result['status']='stopped'; return result
        if report['reported_status']=='paused': result['status']='paused'; return result
        if report['observed_status'] in {'stale','stopped'}: result['status']='stale'; return result
        result['status']='awaiting_advance'
        if previous is None: return result
        if not previous.get('validated') or previous.get('mode')!='live' or previous.get('binding')!=binding or previous.get('identity')!=identity:
            return result
        prior_frame=next((f for f in evidence['frames'] if f['frame_sha256']==previous.get('frame_sha256')),None)
        if (prior_frame is None
                or type(previous.get('simulation_tick')) is not int
                or type(previous.get('noise_cursor')) is not int
                or previous['simulation_tick']!=prior_frame['state']['simulation_tick']
                or previous['noise_cursor']!=prior_frame['state']['noise_cursor']
                or previous.get('state_sha256')!=prior_frame['state_sha256']):
            result['status']='history_mismatch'; return result
        if result['simulation_tick']>previous['simulation_tick']:
            result.update(status='active',active=True)
        return result
    except (ValueError,OSError,KeyError,TypeError) as error:
        result.update(validated=False,status='unknown',active=False,reason=str(error)); return result
