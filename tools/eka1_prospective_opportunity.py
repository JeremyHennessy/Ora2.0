"""Prospective metadata checks only. No World, replay, seeds, policy or grant.

Supplied rows must later be authenticated against complete original history.
This selector does not establish completeness, ancestry or checkpoint authority.
"""
FIELDS={'tick','actor','born','ordinary_mutating_ancestry','feedback','forage','pre_state_sha256'}
FORAGE={'tick','packet','site','port','success'}

def integer(x,lo,hi):
    if type(x) is not int or not lo<=x<=hi: raise ValueError('bounded integer')
    return x

def forage(value,read_tick):
    if type(value) is not dict or set(value)!=FORAGE: raise ValueError('exact latest FORAGE')
    integer(value['tick'],1,read_tick-1)
    integer(value['site'],0,3);integer(value['port'],0,1);integer(value['success'],0,1)
    if value['packet'] is None:
        if value['success']!=0: raise ValueError('empty FORAGE cannot succeed')
    else: integer(value['packet'],0,2**31-1)
    return value

def select_first(rows):
    """Choose first pre-treatment eligible READ; tick is actual dispatch, pre-tick+1."""
    if type(rows) is not list or len(rows)>4096: raise ValueError('finite READ ledger')
    previous=0; selected=None;eligible=0
    for index,row in enumerate(rows):
        if type(row) is not dict or set(row)!=FIELDS: raise ValueError('exact pre-READ fields only')
        tick=integer(row['tick'],1,4096)
        if tick<=previous: raise ValueError('strict global READ ordering')
        previous=tick;integer(row['actor'],0,2**31-1);integer(row['feedback'],0,1)
        if type(row['born']) is not bool or type(row['ordinary_mutating_ancestry']) is not bool: raise ValueError('exact ancestry flags')
        pin=row['pre_state_sha256']
        if type(pin) is not str or len(pin)!=64 or any(c not in '0123456789abcdef' for c in pin): raise ValueError('checkpoint hash format')
        f=None if row['forage'] is None else forage(row['forage'],tick)
        if f is not None and row['feedback']!=f['success']: raise ValueError('latest FORAGE provenance disagrees')
        if f is None and row['feedback']!=0: raise ValueError('no FORAGE initial feedback must be zero')
        if row['born'] and row['ordinary_mutating_ancestry'] and f is not None and f['packet'] is not None and f['packet']>=64 and tick<2048:
            eligible+=1
            if selected is None:selected={'row':index,'tick':tick,'actor':row['actor'],'pre_state_sha256':pin}
    return {'selected':selected,'eligible_reads_in_supplied_ledger':eligible,
            'opportunity_contrast_weight':int(selected is not None),
            'actual_world_outcomes_zeroed':False,
            'original_history_authenticated':False,'complete_ledger_verified':False,
            'execution_authorized':False}

def observer_target(attempted_port,feedback):
    """Observer algebra for an actual NONEMPTY FORAGE only; no policy oracle."""
    return integer(attempted_port,0,1) ^ (1-integer(feedback,0,1))

def conditional_relation(exposure,probe):
    """Sufficient source identity only; mismatches are UNKNOWN, not discarded."""
    f=forage(exposure,4097)
    if type(probe) is not dict or set(probe)!={'tick','packet','site'}:raise ValueError('exact probe fields')
    integer(probe['tick'],f['tick']+1,4096);integer(probe['site'],0,3)
    if probe['packet'] is not None:integer(probe['packet'],0,2**31-1)
    same=(f['packet'] is not None and probe['packet'] is not None
          and f['packet']>=64 and probe['packet']>=64 and f['site']==probe['site']
          and (f['tick']>=2048)==(probe['tick']>=2048))
    return {'target_identity':'EQUAL_IF_COMMON_WORLD' if same else 'UNKNOWN',
            'common_world_authenticated':False,
            'discard_outcome':False,'paid_path_verified':False,
            'delayed_memory_use_verified':False,'fitness_advantage_verified':False}
