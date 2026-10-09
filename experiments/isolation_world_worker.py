"""Fixed finite HEARTBEAT-04 fixture entry; no arbitrary command or service."""
import json
from pathlib import Path
import sys

from experiments.heartbeat_template import run


def main(workspace):
    workspace = Path(workspace)
    config = json.loads((workspace/'request.json').read_text(encoding='utf-8'))
    if set(config) != {'world_id', 'revision', 'resume', 'point'} or type(config['resume']) is not bool:
        raise ValueError('Fixed isolation-world request')
    (workspace/'world-started').write_text('bounded-fixture', encoding='utf-8')
    run(workspace/'world', config['world_id'], config['revision'], work=2,
        max_ticks=32, seed=1, resume=config['resume'],
        fault_tick=5 if config['point'] else None, fault_point=config['point'])


if __name__ == '__main__':
    try:
        main(sys.argv[1])
    except (ValueError, OSError, KeyError, TypeError) as error:
        # Capability launcher deliberately inherits no output handles.
        (Path(sys.argv[1])/'rejection.json').write_text(json.dumps(dict(error=str(error)))+'\n')
        raise SystemExit(2)
