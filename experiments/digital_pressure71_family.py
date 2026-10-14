"""Prospective71 data-only family binding; not a history referee or admission.

The caller owes independent complete natural-history authentication. A supplied
summary/flag, matching hash, or valid certificate is not proof of paid ancestry.
No World, seed draw, continuation, policy or scientific acceptance lives here.
"""
import hashlib
import json
from experiments.digital_functional69_contract import ANCESTOR, integer

VERSION = 'DIGITAL-PRESSURE-SELECTION-71-FAMILY-v2'


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def clone(value):
    return json.loads(json.dumps(value))


def family_from_audited(row, summary):
    """First g2 newborn, then THAT actor's first paid child, including NULL.

    Never substitute an unrelated g3 newborn or a later, successful child.
    This projection checks bindings, not the physical truth of the input audit.
    The independent71 referee must derive this roster without this helper.
    """
    assert type(row) is dict and type(summary) is dict
    assert summary['verified'] is True
    dose = integer(row['dose'], 1, 8); assert dose in (1, 8)
    assert summary['dose'] == dose and type(summary['dose']) is int
    assert row['mode'] == summary['mode'] == 'mutating'
    assert row['inheritance_mode'] == summary['inheritance_mode'] == 'parent_copy'
    assert row['fuel_mode'] == summary['fuel_mode'] == 'renewed'
    assert row['route'] == summary['route'] == 'ancestor'
    integer(row['seed']); integer(summary['seed'])
    assert row['seed'] == summary['seed']
    assert digest(row['final']) == row['hash']
    events = row['final']['events']
    assert type(events) is list and len(events) == integer(summary['ticks'], 0, 4096)
    certificates = {}; consumed = set(); born = {0: (None, 0)}; edges = []
    parent = child = None
    for ordinal, event in enumerate(events, 1):
        assert type(event) is dict and integer(event['tick'], 1, 4096) == ordinal
        actor = integer(event['actor']); assert actor in born
        for word in event.get('writes', []):
            identity = integer(word['write_id'])
            assert identity not in certificates and word['tick'] == ordinal
            certificates[identity] = dict(word, actor=actor)
        if 'birth' not in event:
            continue
        birth = event['birth']; newborn = birth['child']
        target = integer(newborn['id'], 1); generation = integer(newborn['generation'], 1)
        integer(newborn['parent']); assert target not in born and newborn['parent'] == actor
        assert generation == born[actor][1] + 1
        identities = birth['write_ids']
        assert type(identities) is list and len(identities) == 27
        assert all(type(i) is int for i in identities) and len(set(identities)) == 27
        assert consumed.isdisjoint(identities); consumed.update(identities)
        words = [certificates[i] for i in identities]
        assert all(w['actor'] == actor and w['tick'] < ordinal for w in words)
        counterfactual = child_source_values(words, dose)
        assert newborn['code'] == [[w['value'], w['unit']] for w in words]
        state_hash = event['state_hash']
        assert type(state_hash) is str and len(state_hash) == 64
        assert all(c in '0123456789abcdef' for c in state_hash)
        edge = dict(parent=actor, child=target, generation=generation, tick=ordinal,
                    write_ids=clone(identities))
        edges.append(edge); born[target] = (actor, generation)
        slot = dict(target=target, parent=actor, generation=generation, tick=ordinal,
                    certificates=clone(words), born_code=clone(newborn['code']),
                    post_step_hash=state_hash,
                    inherited_source_code=counterfactual)
        if parent is None and generation == 2:
            parent = slot
        elif parent is not None and child is None and actor == parent['target']:
            child = slot
    # Match every edge, not just the two selected slots. Personal-food accounting
    # and full VM replay remain responsibilities of the independent referee.
    audited_edges = summary['birth_edges']
    assert type(audited_edges) is list and len(audited_edges) == len(edges)
    for observed, audited in zip(edges, audited_edges):
        assert all(audited[k] == v for k, v in observed.items())
    return dict(version=VERSION, natural_history_hash=row['hash'], dose=dose, parent=parent,
                child=child, stage_credit=False, requires_authenticated_full_history=True)


def child_source_values(certificates, dose):
    """Prepared/full-audited certificates only; preserve own draws,not their truth.

    This partial validator cannot authenticate a history or prove paid ancestry.
    The future literal referee must independently derive every certificate/mask.
    """
    integer(dose, 1, 8); assert dose in (1, 8)
    assert type(certificates) is list and len(certificates)==27
    writes=set();units=set();sources=set();parent=None;last_tick=0;code=[]
    for index,w in enumerate(certificates):
        assert type(w) is dict and w['index']==integer(w['index'],0,26)==index
        actor=integer(w['actor']);parent=actor if parent is None else parent;assert actor==parent
        identity=integer(w['write_id']);unit=integer(w['unit'],0,511);source=integer(w['source_unit'],0,511)
        assert identity not in writes and unit not in units and source not in sources
        writes.add(identity);units.add(unit);sources.add(source)
        tick=integer(w['tick'],1,4096);assert tick>=last_tick;last_tick=tick
        src=integer(w['source_value'],0,31);effective=integer(w['effective_source_value'],0,31)
        assert w['effective_source']=='parent_copy' and effective==src
        draw=integer(w['mutation_draw'],0,2**64-1);value=integer(w['value'],0,31)
        changed=draw%100<dose
        expected=(src+1+(draw//100)%31)%32 if changed else src
        assert value==expected and type(w['mutated']) is bool and w['mutated']==changed
        baseline=(ANCESTOR[index]+1+(draw//100)%31)%32 if changed else ANCESTOR[index]
        code.append([baseline,unit])
    assert units.isdisjoint(sources)
    return code
