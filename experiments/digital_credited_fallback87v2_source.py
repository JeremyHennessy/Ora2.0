"""Frozen neutral source registry; no labels or Worlds evaluated at import."""
import hashlib
import json
from experiments import digital_credited_fallback86_source as source86
from experiments import digital_revision84_source as references84

VERSION='DIGITAL-CREDITED-FALLBACK87-v2'
ADMISSION='CREDITED-FALLBACK87-v2'
PRIMARY=tuple(range(1009700,1009708))
UNSEEN=tuple(range(1009900,1009908))
SOFTWARE=tuple(range(2100380,2100384))
RESERVED=tuple(range(1009800,1009808))+tuple(range(1010000,1010008))
SEEDS=SOFTWARE+PRIMARY+UNSEEN
DESCRIPTORS=source86.DESCRIPTORS
ARMS=source86.CONTROLS
FIXED=references84.FIXED
WARM=48;DECISIONS=60;HORIZON=1024
CONTRACT_SHA256='8342c880706e5254c045995e3ca79ba09dbb4d0cca0717008214359aceb7e154'

def admit(seed, admission=None):
    assert type(seed) is int and (seed in SOFTWARE or
        admission==ADMISSION and seed in PRIMARY+UNSEEN), 'Unregistered fresh context'

def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def target_mask(seed, packet, admission=None):
    admit(seed,admission)
    assert type(packet) is int and packet>=0
    phase=int(packet>=48)
    if seed in SOFTWARE:
        return ((0,255,90,165),(0,255,165,90))[phase][SOFTWARE.index(seed)]
    bank=PRIMARY if seed in PRIMARY else UNSEEN
    offset=bank.index(seed)
    return (0,255)[offset] if offset<2 else int(digest(['CREDITED-FALLBACK87-LABELS-v1',seed,phase])[:2],16)

def programme(descriptor):
    if type(descriptor) is str:
        assert descriptor in FIXED
        return references84.programme(descriptor)
    assert type(descriptor) in (tuple,list) and len(descriptor)==2
    return source86.programme(*descriptor)

def is_reference(descriptor):
    return type(descriptor) is str and descriptor in FIXED

def roster():
    return [(list(d),arm) for arm in ARMS for d in DESCRIPTORS]+[(r,'intact') for r in FIXED]

def manifest():
    return dict(version=VERSION,contract_sha256=CONTRACT_SHA256,
        descriptors=[dict(descriptor=list(d),programme=programme(d),formation=71+d[0],
                          capacity=d[0],blank_models=[0]*d[0],supplied=True) for d in DESCRIPTORS],
        references={r:dict(programme=programme(r),formation=3*len(programme(r))+10,capacity=2) for r in FIXED},
        arms=list(ARMS),primary=list(PRIMARY),unseen=list(UNSEEN),reserves=list(RESERVED),
        warm=WARM,decisions=DECISIONS,horizon=HORIZON,worlds=0,targets_queried=0,
        scientific_execution_admitted=False,architecture_supplied=True,stage_credit=False)
