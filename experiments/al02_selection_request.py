"""Study-specific DATA admission only. No producer import, seed draw or launch."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
PROTOCOL = BASE / 'data/al02-selection-first-protocol-20261108.json'
PROTOCOL_PIN = '0ce1f514feb1519f7b820bcba7e5204ddd578606d53be1eb5719ca095d48a620'
FOUNDER = (0, 2, 3, 4)
LEGACY_PINS = {
    'experiments/executed_heredity.py': '03e3f1035233e8e1a078cd401ee10857de8ea20dc0249dd6c973675e8fc80342',
    'experiments/lineage_audit.py': '56ad759c0c4957e0f5110d13ae57450438eabccd0ff10dd3cbf4307771e86312',
    'experiments/causal_genealogy_audit.py': '18391a36b871e3a2a7d18c01a3a5b1520ae92f4e36a0c967e11ca1ef5c25e12c',
}
ARMS = {
    'mixed_mutating': ('mutating', 12, 18),
    'all_a_mutating': ('mutating', 30, 0),
    'mixed_faithful': ('faithful', 12, 18),
    'all_a_faithful': ('faithful', 30, 0),
}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON key')
        result[key] = value
    return result


def parse_request(raw):
    if type(raw) is not bytes or len(raw) > 4096:
        raise ValueError('bounded UTF-8 bytes required')
    return json.loads(raw.decode('utf-8'), object_pairs_hook=_unique,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))


def prepare_request(request):
    """Return an immutable-by-value plan; NEVER an execution grant."""
    if type(request) is not dict or set(request) != {
        'schema', 'protocol_sha256', 'context_commitment', 'founder', 'source_pins'
    }:
        raise ValueError('exact request fields required')
    if request['schema'] != 'AL02-SELECTION-REQUEST-v1':
        raise ValueError('wrong study')
    if type(request['founder']) is not list or any(type(x) is not int for x in request['founder']) or tuple(request['founder']) != FOUNDER:
        raise ValueError('only ordinary founder admitted')
    commitment = request['context_commitment']
    if type(commitment) is not str or len(commitment) != 64 or any(x not in '0123456789abcdef' for x in commitment):
        raise ValueError('opaque context commitment required; no seeds here')
    actual_protocol = hashlib.sha256(PROTOCOL.read_bytes()).hexdigest()
    if actual_protocol != PROTOCOL_PIN or request['protocol_sha256'] != PROTOCOL_PIN:
        raise ValueError('protocol pin mismatch')
    if request['source_pins'] != LEGACY_PINS:
        raise ValueError('wrong source declaration')
    for name, pin in LEGACY_PINS.items():
        if hashlib.sha256((BASE / name).read_bytes()).hexdigest() != pin:
            raise ValueError('legacy bytes changed')
    slots = []
    for role, (variant, food_a, food_b) in ARMS.items():
        for index in (range(16) if variant == 'mutating' else (0,)):
            slots.append(dict(role=role, context_index=index, variant=variant,
                              food_a=food_a, food_b=food_b, horizon=600))
    return dict(scope='DATA_ONLY_NOT_REGISTERED', execution_authorized=False,
                founder=list(FOUNDER), context_commitment=commitment,
                protocol_sha256=actual_protocol, slots=slots,
                maximum_instructions=20400, authenticated_execution=False)


def validate_opening(plan, manifest):
    if type(manifest) is not dict or set(manifest) != {'schema', 'seeds'} or manifest['schema'] != 'AL02-SELECTION-CONTEXTS-v1':
        raise ValueError('wrong context manifest')
    seeds = manifest['seeds']
    if type(seeds) is not list or len(seeds) != 16:
        raise ValueError('all16 contexts required')
    if any(type(s) is not int or not 0 <= s < 2**64 or s < 8 or 5000 <= s <= 5063 or s == 771177 for s in seeds):
        raise ValueError('unregistered domain or historical context')
    if digest(manifest) != plan['context_commitment']:
        raise ValueError('context preimage mismatch')
    return tuple(seeds)
