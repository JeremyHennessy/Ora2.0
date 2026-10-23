"""Fixed contained qualification caller; authenticated registration only."""
import sys
from pathlib import Path
from experiments import digital_pilot74_qualification_controller_v1 as controller
from experiments.digital_pilot74_durable_supervisor_v1 import Attempt

def main():
    assert len(sys.argv)==4 and not sys.flags.optimize
    spec=dict(path=sys.argv[1],extent=int(sys.argv[2]),sha256=sys.argv[3])
    r=controller.validate_guardian(spec,spec['sha256'])
    assert Path(__file__).resolve()==Path(r['source_root'])/'experiments/digital_pilot74_qualification_caller_v1.py'
    attempt=Attempt(Path(r['root']).parent/'caller',spec['sha256'])
    try:
        def admit(s,h):
            controller.validate_guardian(s,h)
            return True
        result=attempt.run_qualification(spec,spec['sha256'],admit)
        assert result['exit_code']==0 and result['post_close_processes_exited'] is True
    finally:
        attempt.close()
    if attempt.cleanup_errors:raise RuntimeError('Caller cleanup errors retained: '+repr(attempt.cleanup_errors))
if __name__=='__main__':main()
