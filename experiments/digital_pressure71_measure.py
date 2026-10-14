"""Dose-bound projections after full literal replay; never admission authority.

The controller owes raw/proof custody and authenticated natural context, including
NULL cases whose literal verdict has no summary. Flags and prepared dictionaries
cannot prove paid ancestry, organism novelty, selection or a scientific stage.
"""
from experiments.digital_functional69_contract import contrast, integer
from experiments.digital_pressure71_admission import hash_string, SEEDS
from experiments.digital_pressure71_contract import cohort


def roster(context):
    assert type(context) is dict
    integer(context['seed']); assert context['seed'] in SEEDS
    integer(context['dose']); assert context['dose'] in (1, 8)
    assert type(context['horizon']) is int and context['horizon'] == 4096
    assert context['software_only'] is False
    hash_string(context['natural_history_hash'])
    parents = {0: None}; generations = {0: 0}; root = child = None; last = 0
    assert type(context['birth_edges']) is list
    for edge in context['birth_edges']:
        actor = integer(edge['parent']); target = integer(edge['child'], 1)
        tick = integer(edge['tick'], 1, 4096)
        generation = integer(edge['generation'], 1)
        assert actor in parents and target not in parents and tick > last
        assert generation == generations[actor] + 1
        parents[target] = actor; generations[target] = generation; last = tick
        if root is None and generation == 2: root = edge
        if root is not None and child is None and actor == root['child']: child = edge
    return root, child


def pair(sham, control, kind, provenance, context):
    assert kind in ('parent', 'child')
    assert type(provenance) is dict and set(provenance) == {'source_sha256', 'configuration_sha256'}
    for value in provenance.values(): hash_string(value)
    edge = roster(context)[kind == 'child']
    for proof, role in ((sham, 'sham'), (control, 'ancestor_value_control' if kind == 'parent' else 'inherited_source_control')):
        assert proof['verified'] is True and proof['stage_credit'] is False
        assert proof['scientific_admission'] is False
        assert proof['slot_kind'] == kind and proof['role'] == role and proof['provenance'] == provenance
        assert type(proof['seed']) is int and proof['seed'] == context['seed']
        assert proof['natural_history_hash'] == context['natural_history_hash']
        assert type(proof['null']) is bool and proof['null'] == (edge is None)
        if edge is None:
            assert all(proof[key] is None for key in ('slot', 'target', 'branch_hash', 'transition_mask'))
        else:
            slot = proof['slot']
            for key, value in dict(target=edge['child'], parent=edge['parent'], tick=edge['tick'], generation=edge['generation']).items():
                assert type(slot[key]) is int and slot[key] == value
            hash_string(proof['branch_hash'])
            summary = proof['summary']
            assert summary['verified'] is True and summary['software_only'] is False
            for key in ('seed', 'dose', 'horizon'):
                assert type(summary[key]) is int and summary[key] == context[key]
    assert sham['slot'] == control['slot'] and sham['transition_mask'] == control['transition_mask']
    if edge is None: return dict(null=True, new_strategy=False, complete=False)
    mask = control['transition_mask']
    assert type(mask) is list and all(type(i) is int and 0 <= i < 27 for i in mask)
    assert mask == sorted(set(mask))
    assert sham['branch_hash'] == context['natural_history_hash']
    return dict(contrast(sham['target'], control['target'], bool(mask)), null=False, changed=bool(mask))


def census(proof):
    """Recompute all-birth denominators from the replayed summary; no survivor filter."""
    c = proof['census']; summary = proof['summary']; root = proof['slot']['target']
    assert c['history_hash'] == proof['branch_hash'] and c['root'] == root
    assert c['stage_credit'] is False and c['scientific_admission'] is False
    edges = summary['birth_edges']
    assert len(edges) == integer(summary['births'])
    assert len(c['death_records']) == integer(summary['deaths'])
    projected = [{k: e[k] for k in ('parent', 'child', 'generation', 'tick')} for e in edges]
    assert projected == c['birth_edges']
    # Same validation of all identities, chronology and generation accounting.
    ctx = dict(seed=summary['seed'], dose=summary['dose'], horizon=4096,
               software_only=False, natural_history_hash=proof['branch_hash'], birth_edges=edges)
    first, _ = roster(ctx); assert first is not None and first['child'] == root
    lineage = {root}; totals = {3: 0, 4: 0}; counts = {3: 0, 4: 0}
    for e in edges:
        if e['parent'] in lineage: lineage.add(e['child'])
        if e['generation'] in totals:
            totals[e['generation']] += 1
            counts[e['generation']] += e['child'] in lineage
    frame = dict(root=root, early_total=totals[3], early_lineage=counts[3], late_total=totals[4], late_lineage=counts[4])
    assert c['frame'] == frame and c['lineage_birth_ids'] == sorted(lineage - {root})
    eligible, growth, births = cohort(frame)
    assert c['cohort_opportunity'] is eligible
    assert c['growth'] == (None if growth is None else [growth.numerator, growth.denominator])
    return frame, eligible, growth, births


def family_comparison(parent_sham, parent_control, child_sham, child_control, provenance, context):
    p = pair(parent_sham, parent_control, 'parent', provenance, context)
    c = pair(child_sham, child_control, 'child', provenance, context)
    functional = (not p['null'] and not c['null'] and p['new_strategy'] and c['new_strategy'] and
                  child_sham['target']['births'] > 0 and child_sham['target']['food'] > 0)
    opportunity = selected = False; a = b = None; difference = None
    if not p['null']:
        frame, ae, a, births_a = census(parent_sham)
        _, be, b, births_b = census(parent_control)
        difference = births_a - births_b
        opportunity = ae and be and frame['late_lineage'] >= 2
        selected = bool(functional and opportunity and a > 0 and a > b and difference > 0)
    rational = lambda x: None if x is None else [x.numerator, x.denominator]
    return dict(seed=context['seed'], dose=context['dose'], provenance=dict(provenance),
                natural_history_hash=context['natural_history_hash'], parent=p, child=c,
                conditional_functional_contribution=bool(functional), conditional_selection=selected,
                cohort_opportunity=opportunity, sham_growth=rational(a), control_growth=rational(b),
                descendant_birth_difference=difference, scientific_acceptance=False, stage_credit=False,
                requires_authenticated_full_history=True)


def panel(families, populations, provenance):
    """All 16 unscreened families, separate doses/banks; projection, not acceptance."""
    assert type(families) is list and type(populations) is list
    expected = {(seed, dose) for seed in SEEDS for dose in (1, 8)}
    fm = {}; pm = {}
    for result in families:
        key = (integer(result['seed']), integer(result['dose']))
        assert key in expected and key not in fm
        assert result['provenance'] == provenance and result['scientific_acceptance'] is False
        assert result['stage_credit'] is False
        for name in ('conditional_functional_contribution', 'conditional_selection'):
            assert type(result[name]) is bool
        hash_string(result['natural_history_hash']); fm[key] = result
    for proof in populations:
        assert proof['verified'] is True and proof['provenance'] == provenance
        assert proof['stage_credit'] is False
        s = proof['summary']; key = (integer(s['seed']), integer(s['dose']))
        assert key in expected and key not in pm
        assert s['verified'] is True and s['software_only'] is False
        assert type(s['horizon']) is int and s['horizon'] == 4096
        assert s['mode'] == 'mutating' and s['inheritance_mode'] == 'parent_copy'
        integer(s['births']); integer(s['renewed_food'])
        pm[key] = proof
    assert set(fm) == set(pm) == expected
    assert all(fm[key]['natural_history_hash'] == pm[key]['natural_history_hash'] for key in expected)
    banks = {}
    for name, seeds in (('primary', SEEDS[:4]), ('unseen', SEEDS[4:])):
        doses = {}
        for dose in (1, 8):
            rows = [fm[(seed, dose)] for seed in seeds]
            summaries = [pm[(seed, dose)]['summary'] for seed in seeds]
            doses[dose] = dict(denominator=len(rows), useful_families=sum(r['conditional_functional_contribution'] for r in rows),
                               selection_cases=sum(r['conditional_selection'] for r in rows),
                               unconditional_births=sum(s['births'] for s in summaries),
                               unconditional_renewed_food=sum(s['renewed_food'] for s in summaries))
        a, b = doses[1], doses[8]
        db = a['unconditional_births'] - b['unconditional_births']
        df = a['unconditional_renewed_food'] - b['unconditional_renewed_food']
        banks[name] = dict(doses=doses, pressure_alleviation=(a['useful_families'] > b['useful_families'] and
                                                            ((db > 0 and df >= 0) or (df > 0 and db >= 0))))
    return dict(banks=banks, replicated_functional={d: all(banks[n]['doses'][d]['useful_families'] >= 1 for n in banks) for d in (1, 8)},
                replicated_selection={d: all(banks[n]['doses'][d]['selection_cases'] >= 1 for n in banks) for d in (1, 8)},
                pressure_alleviation=all(banks[n]['pressure_alleviation'] for n in banks),
                scientific_acceptance=False, stage_credit=False, requires_authenticated_full_history=True)
