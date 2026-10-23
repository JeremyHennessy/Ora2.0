"""One registered no-World deadline caller. No arbitrary command execution."""
import hashlib,json,os,sys,time
from pathlib import Path

def main():
    path,seal,case_path=sys.argv[1:]
    raw=Path(path).read_bytes()
    if len(raw)>131072 or hashlib.sha256(raw).hexdigest()!=seal: raise ValueError('registration pin')
    reg=json.loads(raw);root=Path(reg['source_root']);case=Path(case_path)
    if Path(__file__).resolve()!=root/'experiments/digital_pilot74_reserved_closure_probe_v1.py': raise ValueError('source origin')
    if reg['cases']!=['reserved-closure-deadline'] or case!=Path(reg['root'])/'reserved-closure-deadline': raise ValueError('case authority')
    for name,pin in reg['source_files'].items():
        if hashlib.sha256((root/name).read_bytes()).hexdigest()!=pin: raise ValueError('source changed')
    sys.path.insert(0,str(root))
    from experiments.digital_pilot74_durable_supervisor_v1 import Attempt
    from experiments.digital_pilot74_guardian_boundary_qualifier_v2 import kernel,birth
    attempt=Attempt(case/'durable',seal)
    k=kernel();handle=k.OpenProcess(0x1000|0x100000,False,os.getpid())
    if not handle: raise OSError('original identity unavailable')
    try:
        value=dict(pid=os.getpid(),creation_filetime_decimal=str(birth(k,handle)),expected_intervention='original-owner-soft-stop-1750-hard-deadline-2000',wait_seconds=60)
        data=json.dumps(value,sort_keys=True,separators=(',',':')).encode()
        with (case/'before-wait.json').open('xb') as f:
            f.write(data);f.flush();os.fsync(f.fileno())
    finally:k.CloseHandle(handle)
    time.sleep(60)
    raise AssertionError('Owner deadline did not terminate caller')

if __name__=='__main__':main()
