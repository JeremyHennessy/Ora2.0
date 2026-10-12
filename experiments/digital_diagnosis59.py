"""Strict read-only source admission and integrity-before-projection wrapper."""
from .digital_informative_exposure23_interpret import audit,h
from .digital_diagnosis59_project import project as chronological
from .digital_diagnosis59_project_independent import project as joined

SOURCE_HASH='ee718c93d4ebdfb569f535c23febb626490cf99e533e7a08ab7c290261450cd3'
ROSTER=((55020,1),(55020,4),(55025,5),(55009,3),(55000,2),(55018,1),(55029,2),(55008,4))
REFERENCE=[[4,1,1],[6,0,0],[5,0,1],[6,0,0],[10,0,0],[12,0,0],[13,1,0],[13,1,0],[7,0,1]]


def bank(manifest):
    assert h(manifest)==SOURCE_HASH and manifest['eligible']==151 and manifest['enrolled']==8
    entries=manifest['roster'];assert tuple((r['seed'],r['child']) for r in entries)==ROSTER
    return entries


def origin(manifest,arm,source):return admitted_origin(bank(manifest),arm,source)


def admitted_origin(entries,arm,source):
    if arm=='withheld':assert source is None;return REFERENCE
    assert arm=='retained' and type(source) is dict
    assert all(type(source[k]) is int for k in ('seed','child'))
    key=(source['seed'],source['child']);assert key in ROSTER;r=entries[ROSTER.index(key)]
    assert source==dict(seed=r['seed'],child=r['child'],program_hash=r['program_hash'],source_row_hash=r['source_row_hash'])
    assert h(sum(r['program'],[]))==r['program_hash'];return r['program']


def interpret(envelope,manifest,method='chronological'):
    assert method in ('chronological','joined')
    assert envelope['version']=='DIGITAL-REPLICATION-58-assisted-v1' and envelope['source_manifest_hash']==SOURCE_HASH
    program=origin(manifest,envelope['arm'],envelope['source']);row=envelope['history']
    assert type(row['seed']) is int and row['seed'] in range(58000,58016) and row['mode']=='faithful' and row['genesis_program']==program
    # No projection or kernel call precedes the full independent raw VM audit.
    checked=audit(row);assert checked['verified'] is True and checked['formation_cost']==43 and checked['mutations']==0
    result=(chronological if method=='chronological' else joined)(row);s=result['summary']
    assert (s['ticks'],s['births'],s['deaths'],s['food'],s['copy_words'],s['free_material'],s['live_energy'])==tuple(checked[k] for k in ('ticks','births','deaths','successful_food','paid_copy_words','free_material','live_energy'))
    assert s['actors']==1+s['births'] and sum(a['alive'] for a in result['actors'].values())==s['actors']-s['deaths']
    return dict(verified=True,identity=dict(seed=row['seed'],arm=envelope['arm'],source=envelope['source']),source_manifest_hash=SOURCE_HASH,
                raw_hash=h(row),summary=s,semantic_hash=h(result),diagnosis=result,stage_credit=False,learning=False,causal_inheritance=False)


def panel(summaries,manifest):
    """Reduced authenticated summaries only; full ledgers stay bounded on disk."""
    assert len(summaries)==144;entries=bank(manifest);seen=set();totals={k:0 for k in ('ticks','actors','births','deaths','food','copy_words','free_material','live_energy')}
    for p in summaries:
        assert p['verified'] is True and p['source_manifest_hash']==SOURCE_HASH and p['stage_credit'] is False
        identity=p['identity'];admitted_origin(entries,identity['arm'],identity['source']);seed=identity['seed']
        assert type(seed) is int and seed in range(58000,58016)
        key=(seed,None if identity['source'] is None else (identity['source']['seed'],identity['source']['child']))
        assert key not in seen;seen.add(key)
        for hash_key in ('raw_hash','semantic_hash'):
            v=p[hash_key];assert type(v) is str and len(v)==64 and all(c in '0123456789abcdef' for c in v)
        s=p['summary'];assert s['actors']==s['births']+1 and s['deaths']<=s['actors'] and s['ticks']<=512 and s['food']<=64
        for k in totals:assert type(s[k]) is int and s[k]>=0;totals[k]+=s[k]
    assert seen=={(seed,key) for seed in range(58000,58016) for key in (None,)+ROSTER}
    return dict(verified=True,histories=144,shared_references=16,source_groups=8,totals=totals,
                stage_credit=False,learning=False,causal_inheritance=False,selection=False)
