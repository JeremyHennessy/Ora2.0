"""Data comparisons after independent full replay; no admission or stage credit.

Proof-shaped dictionaries are not truth. The pinned operator must authenticate
the literal referee, raw/proof custody and complete histories before using these
projections. This module never executes a World or selects a starting genome.
"""
from experiments.digital_functional69_contract import contrast, integer


def validate_pair(sham,control,kind,provenance):
    assert kind in ('parent','child')
    assert type(provenance) is dict and set(provenance)=={'source_sha256','configuration_sha256'}
    for value in provenance.values():
        assert type(value) is str and len(value)==64 and set(value)<=set('0123456789abcdef')
    for proof,role in [(sham,'sham'),(control,'ancestor_value_control' if kind=='parent' else 'inherited_source_control')]:
        assert type(proof) is dict and proof['verified'] is True
        assert proof['slot_kind']==kind and proof['role']==role and proof['provenance']==provenance
        assert type(proof['null']) is bool and proof['stage_credit'] is False
        integer(proof['seed'])
        identity=proof['natural_history_hash']
        assert type(identity) is str and len(identity)==64 and set(identity)<=set('0123456789abcdef')
        if not proof['null']:
            slot=proof['slot'];integer(slot['target'],1);integer(slot['parent'])
            integer(slot['tick'],1,4096);integer(slot['generation'],1,2)
            assert slot['generation']==(1 if kind=='parent' else 2)
    assert sham['seed']==control['seed'] and sham['natural_history_hash']==control['natural_history_hash']
    assert sham['slot']==control['slot'] and sham['null']==control['null']
    assert sham['transition_mask']==control['transition_mask']
    if sham['null']:
        assert sham['target'] is None and control['target'] is None and sham['slot'] is None
        return dict(null=True,stage_credit=False,requires_authenticated_full_history=True)
    changed=bool(control['transition_mask'])
    assert type(control['transition_mask']) is list
    assert all(type(i) is int and 0<=i<27 for i in control['transition_mask'])
    assert control['transition_mask']==sorted(set(control['transition_mask']))
    result=contrast(sham['target'],control['target'],changed)
    return dict(result,null=False,changed=changed)


def family_comparison(parent_sham,parent_control,child_sham,child_control,provenance):
    parent=validate_pair(parent_sham,parent_control,'parent',provenance)
    child=validate_pair(child_sham,child_control,'child',provenance)
    assert parent_sham['seed']==child_sham['seed']
    assert parent_sham['natural_history_hash']==child_sham['natural_history_hash']
    edge=False
    if not child['null']:
        assert not parent['null']
        assert child_sham['slot']['parent']==parent_sham['slot']['target']
        assert child_sham['slot']['generation']==2 and parent_sham['slot']['generation']==1
        assert child_sham['slot']['tick']>parent_sham['slot']['tick']
        edge=True
    qualifies=(edge and parent['new_strategy'] and child['new_strategy'] and
               child_sham['target']['food']>0 and child_sham['target']['births']>0)
    return dict(parent=parent,child=child,bound_actual_family=edge,
                conditional_functional_contribution=qualifies,stage_credit=False,
                requires_authenticated_full_history=True)
