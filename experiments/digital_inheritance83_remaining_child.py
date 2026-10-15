"""Remaining-only native entry. Never retries a cached primary role."""
import json
import sys
from pathlib import Path

from experiments import digital_cognitive76_child as boundary
from experiments import digital_inheritance83_primary_child as primary
from experiments import digital_inheritance83_remaining as remaining

SCOPE = dict(version='INHERITANCE83-REMAINING-CONTROLLER-v1',
             cache_manifest_sha256='581e19ac5722dae13afee00ff064587703418f65f95735f6890e4a778fa2a87d',
             cache_archive_sha256='d860d6252457a9e924db50136723a744c6e6bc7cfd82fa9e28c230226d6287e8',
             cached=list(remaining.CACHED), roles=remaining.plan())


def admit(request):
    assert set(request) == {'configuration','source_files','source_sha','config_sha',
                            'role','kind','input','grant','seal'}, 'request'
    remaining.guard(request)
    assert {'experiments/digital_inheritance83_remaining_child.py',
            'experiments/digital_inheritance83_remaining.py',
            'experiments/digital_inheritance83_remaining_cache.py'} <= set(request['source_files']), 'remaining source'
    # The exact new source digest binds this immutable remaining/cache scope.
    assert request['source_sha'] == remaining.old.digest(request['source_files']), 'source/config'
    assert boundary.verify_source(Path.cwd(), request['source_files']) == request['source_sha']


def main():
    request = json.loads(boundary.bounded_bytes(Path(sys.argv[1]), 65536), object_pairs_hook=boundary.pairs)
    admit(request)
    # Reuse the exact qualified generator loop/audit/metric/final implementation.
    # Its source/config/grant/seal checks still precede the first World import.
    primary.main()


if __name__ == '__main__': main()
