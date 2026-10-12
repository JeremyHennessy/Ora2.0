"""Authenticate whole closed batches before four-row History46 interpretation.

The expected envelope is assembled from separately sealed published metrics and
the original source inventory. This is custody validation, not another VM proof.
No World, sampling, endpoint scoring or successful policy is installed here.
"""
import hashlib
import json
from pathlib import Path

CONTRACT = 'DIGITAL-HISTORY-44-FRESH-v1'
ARMS = ('intact', 'retained_disabled', 'own_disrupted')
REFERENCES = tuple('affine'+str(i) for i in range(8)) + ('alternating', 'fixed0', 'fixed1')


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def file_sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        while block := stream.read(1024**2):
            h.update(block)
    return h.hexdigest()


def roles(chunk):
    if type(chunk) is not int or not 0 <= chunk < 34:
        raise ValueError('Closed chunk identity')
    if chunk < 32:
        return ['candidate'+str(i) for i in range(chunk*8, chunk*8+8)]
    return list(REFERENCES[:8] if chunk == 32 else REFERENCES[8:])


def authenticate(batch, expected, offset):
    """Validate every member, including members outside the selected slice."""
    chunk = expected['chunk']; seed = expected['seed']; arm = expected['control']
    if type(seed) is not int or seed not in range(44200, 44208) or arm not in ARMS:
        raise ValueError('Closed context identity')
    ordered = roles(chunk)
    if (batch.get('contract') != CONTRACT or type(batch.get('chunk')) is not int
            or batch['chunk'] != chunk or type(batch.get('seed')) is not int
            or batch['seed'] != seed or batch.get('control') != arm):
        raise ValueError('Batch metadata')
    histories = batch['histories']; identities = expected['histories']
    if ([x['role'] for x in histories] != ordered
            or [x['role'] for x in identities] != ordered):
        raise ValueError('Complete ordered membership')
    if type(offset) is not int or offset not in (0, 4) or offset >= len(ordered):
        raise ValueError('Four-row slice')
    for item, identity in zip(histories, identities):
        row = item['row']
        if item['source_descriptor_is_static'] is not True:
            raise ValueError('Static source disclosure')
        if digest(item['ancestry']) != digest(identity['ancestry']):
            raise ValueError('Complete ancestry')
        if digest(row) != identity['input_sha256']:
            raise ValueError('Canonical raw row hash')
        if (type(row['seed']) is not int or row['seed'] != seed
                or row['control_mode'] != arm or row['experiment'] != CONTRACT
                or digest(row['genesis_program']) != digest(identity['program'])):
            raise ValueError('Row source or context')
    return histories[offset:offset+4]


def main():
    import sys
    # Expected-envelope hash is supplied by the capped parent, not trusted from
    # the envelope itself. Raw file hash is a seal admitted independently in49.
    raw, expectation, seal, offset, interpreter = sys.argv[1:]
    if file_sha(expectation) != seal:
        raise ValueError('Expected-envelope seal')
    expected = json.loads(Path(expectation).read_bytes())
    if file_sha(raw) != expected['batch_sha256']:
        raise ValueError('Original batch-file seal')
    batch = json.loads(Path(raw).read_bytes())
    selected = authenticate(batch, expected, int(offset))
    if interpreter == 'producer':
        from .digital_history46_diagnose import diagnose
    elif interpreter == 'referee':
        from .digital_history46_independent import diagnose
    else:
        raise ValueError('Registered interpreter')
    result = [dict(role=x['role'], diagnosis=diagnose(x['row'])) for x in selected]
    if file_sha(raw) != expected['batch_sha256'] or file_sha(expectation) != seal:
        raise ValueError('Input changed during diagnosis')
    print(json.dumps(result, sort_keys=True, separators=(',', ':')))


if __name__ == '__main__':
    main()
