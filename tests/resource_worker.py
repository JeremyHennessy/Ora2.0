"""Disposable RESOURCE-01 fixtures, launched only by a bounded supervisor."""
import json
from pathlib import Path
import subprocess
import sys
import time

kind = sys.argv[1]
if kind == 'success':
    print('finite-success', flush=True)
elif kind == 'cpu':
    value = 0
    while True:
        value = (value + 1) % 1000
elif kind == 'memory':
    try:
        block = bytearray(256 * 1024**2)
        print('allocation-succeeded', len(block), flush=True)
    except MemoryError:
        print('memory-denied', flush=True)
        raise SystemExit(42)
elif kind in ('process', 'timeout', 'orphan'):
    child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'])
    print(json.dumps({'child_pid': child.pid}), flush=True)
    if kind == 'process':
        try:
            extra = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'])
        except OSError as error:
            print(json.dumps({'fourth_denied': True, 'winerror': error.winerror}), flush=True)
        else:
            print(json.dumps({'fourth_denied': False, 'extra_pid': extra.pid}), flush=True)
            raise SystemExit(43)
    elif kind == 'timeout':
        time.sleep(30)
elif kind == 'output':
    sys.stdout.buffer.write(b'x' * (2 * 1024**2))
    sys.stdout.buffer.flush()
elif kind == 'marker':
    Path(sys.argv[2]).write_text('target started', encoding='utf-8')
else:
    raise SystemExit('Unknown fixture')

