"""Exact native-bound qualification lock scope; production default unchanged."""
import os
from pathlib import Path
from experiments import digital_pilot74_publication_reader_v2 as physical

def allowed(spec):
    path=Path(spec['path'])
    if path==Path('D:/OraLab/state/operator.lock'):return True
    # Native G clears all three variables in production and sets them only for
    # its exact qualification pair. They select immutable registration bytes,
    # never arbitrary modules/commands or an independent grant of authority.
    names=('PILOT74_QREG_PATH','PILOT74_QREG_EXTENT','PILOT74_QREG_SHA256')
    values=[os.environ.get(n) for n in names]
    if not all(values):return False
    try:
        pin=dict(path=values[0],extent=int(values[1]),sha256=values[2])
        r=physical.parse(physical.external(pin,65536),65536)
        assert r['schema']=='PILOT74-WHOLE-WORKLOAD-QUALIFICATION-v1'
        assert r['mode']=='new_software_resource_recovery_qualification'
        assert r['operator_lock']==spec
        assert path==Path(r['root']).parent/'qualification-owner.lock'
        assert path.resolve().is_relative_to(Path('D:/OraLab/runs').resolve())
        # The helper itself must be among the exact source bytes endorsed by G.
        name='experiments/digital_pilot74_lock_scope_v1.py'
        assert physical.digest(Path(__file__).read_bytes())==r['source_files'][name]
        return True
    except (AssertionError,KeyError,TypeError,ValueError,OSError):return False
