"""Disclosed authored apparatus factory; no primary emerged candidate or teacher."""
from .digital_informative_exposure23_interpret import h,clone

SOURCE_HASH='98a8221ab2f988d69406ff41129afb86350ae24bb093c0c575f3aeb3efec4095'
ARMS=('intact','cache-cleared','cache-disrupted','feedback-disabled','fixed-exploration','fixed0','fixed1')
SEEDS=tuple(range(60000,60008))+tuple(range(60200,60208))
VERSION='DIGITAL-LEARNING-CAPACITY-60-authored-apparatus-v1'


def bank(source):
    assert h(source)==SOURCE_HASH and source['world_calls']==0 and source['formation_words']==46
    assert set(source['programs'])==set(ARMS)
    for p in source['programs'].values():
        assert len(p)==10 and all(type(t) is list and len(t)==3 and all(type(v) is int and 0<=v<32 for v in t) for t in p)
    return source['programs']


def generate(seed,arm,source):
    assert type(seed) is int and seed in SEEDS and arm in ARMS
    program=clone(bank(source)[arm])
    from . import digital_informative_exposure23 as substrate
    alias='learning-capacity60';assert alias not in substrate.PROGRAMS
    before=h(substrate.PROGRAMS);matches=[name for name,p in substrate.PROGRAMS.items() if p==program]
    assert len(matches)<=1;route=matches[0] if matches else alias
    if not matches:substrate.PROGRAMS[alias]=clone(program)
    try:return dict(version=VERSION,arm=arm,source_hash=SOURCE_HASH,authored_apparatus=True,history=substrate.history(seed,route,'faithful'))
    finally:
        if not matches:del substrate.PROGRAMS[alias]
        assert h(substrate.PROGRAMS)==before
