"""Unexecuted whole-original-World selection replay source. No CLI or grant.

Selection is reconstructed from every source dispatch, never supplied lineage
flags or historical winners. Actual calls require separate native registration.
"""
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT_PINS = {'experiments/digital_eka1_derived_reconstruction_v1.py': 'ca8672080604a511e2133c427c4a06aa68200ed55ba61ea4c79ca9afec2af5b5', 'tools/eka1_prospective_opportunity.py': 'e49714d895183ce2931b1173829dfb07b1300cc910bb292792c00e7fd33d5b76'}
REQUEST_FIELDS = {'schema', 'original_raw_sha256', 'assignment_id',
                  'assigned_stop_tick', 'configuration'}
CONFIG_FIELDS = {'seed', 'mode', 'fuel_mode', 'inheritance_mode', 'dose'}


def integer(value, lo, hi):
    if type(value) is not int or not lo <= value <= hi:
        raise ValueError('Exact bounded integer')
    return value


def request_metadata(request):
    """Only source/request consistency; no World, seed lookup or acceptance."""
    if type(request) is not dict or set(request) != REQUEST_FIELDS or request['schema'] != 'ORA-EKA1-ORIGINAL-SELECTION-REPLAY-v1':
        raise ValueError('Exact selection replay request')
    digest = request['original_raw_sha256']
    if type(digest) is not str or len(digest) != 64 or any(c not in '0123456789abcdef' for c in digest):
        raise ValueError('Raw original SHA256')
    name = request['assignment_id']
    if type(name) is not str or not 0 < len(name) <= 128:
        raise ValueError('Prospectively assigned World identity')
    if type(request['assigned_stop_tick']) is not int or request['assigned_stop_tick'] != 4096:
        raise ValueError('Full assigned4096-dispatch horizon required')
    config = request['configuration']
    if type(config) is not dict or set(config) != CONFIG_FIELDS:
        raise ValueError('Exact source configuration')
    integer(config['seed'], 0, 2**63-1)
    if config['mode'] != 'mutating' or config['fuel_mode'] != 'renewed' or config['inheritance_mode'] != 'parent_copy':
        raise ValueError('Ordinary mutating parent-copy lineage only')
    if type(config['dose']) is not int or config['dose'] not in (1, 8):
        raise ValueError('Preserve both dose strata')
    return dict(config)


def extend_ancestry(registry, actor, child):
    """Check supplied birth metadata, not an authentication entrypoint."""
    if type(registry) is not dict or type(actor) is not int or actor not in registry or type(child) is not dict:
        raise ValueError('Recorded parent required')
    identity = integer(child.get('id'), 1, 2**31-1)
    generation = integer(child.get('generation'), 1, 4096)
    if identity in registry or type(child.get('parent')) is not int or child['parent'] != actor or generation != registry[actor][1]+1:
        raise ValueError('Source birth chain differs')
    registry[identity] = (actor, generation)


def earned_read(row):
    """Outcome-blind predicate; feedback bit and fitness never choose a row."""
    forage = row['forage']
    return (row['born'] and row['ordinary_mutating_ancestry'] and forage is not None
            and forage['packet'] is not None and forage['packet'] >= 64 and row['tick'] < 2048)


def metadata_inputs():
    for name, digest in INPUT_PINS.items():
        path = ROOT/name
        if path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError('Selection dependency changed: '+name)
    # Lazy: never imported or called by NEW metadata/source checks.
    from experiments import digital_eka1_derived_reconstruction_v1 as reconstruction
    if Path(reconstruction.__file__).resolve() != (ROOT/'experiments/digital_eka1_derived_reconstruction_v1.py').resolve():
        raise ValueError('Reconstruction module origin')
    path = ROOT/'tools/eka1_prospective_opportunity.py'
    spec = importlib.util.spec_from_file_location('_eka1_pinned_selection_metadata', path)
    selector = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(selector)
    return reconstruction, selector


def replay_original_selection(original_raw, request, *, reservations, genesis_index):
    """One paid genesis/full assigned replay; retain no-READ actual outcomes.

    Unchanged source law reconstructs all original fields/events. This is not a
    producer-free literal interpreter or physical/native authority validation.
    """
    config = request_metadata(request)
    # Mandatory whole-replay precharge precedes runtime imports and genesis.
    # No refund on invalid input, extinction, comparison failure or exception.
    from tools.eka1_cumulative_reservations import Reservations
    if type(reservations) is not Reservations:
        raise TypeError('Exact owner reservation ledger required')
    reservations.genesis(config['dose'], genesis_index)
    reservations.dispatches(config['dose'], genesis_index, request['assigned_stop_tick'])
    reconstruction, selector = metadata_inputs()
    original = reconstruction.parse_checkpoint(original_raw, request['original_raw_sha256'])
    for field, value in config.items():
        key = '_dose' if field == 'dose' else field
        if type(original.get(key)) is not type(value) or original[key] != value:
            raise ValueError('Original source configuration differs')
    World, unused_paid_read = reconstruction.runtime_sources()
    world = World(config['seed'], config['mode'], 'ancestor', config['fuel_mode'],
                  config['inheritance_mode'], dose=config['dose'])
    ancestry, latest_forage, rows = {0:(None, 0)}, {}, []
    selected_raw, selected_context = None, None
    while world.tick < request['assigned_stop_tick'] and world.entities:
        ids = sorted(world.entities)
        actor = next((i for i in ids if i > world.last), ids[0])
        entity = world.entities[actor]
        if actor not in ancestry or entity['id'] != actor or (entity['parent'], entity['generation']) != ancestry[actor]:
            raise ValueError('Actor ancestry not source-derived')
        decoded = [v[0] for v in entity['code'][3*entity['pc']:3*entity['pc']+3]]
        if decoded[0] == 1:
            feedback = integer(entity['feedback'], 0, 1)
            forage = latest_forage.get(actor)
            if feedback != (0 if forage is None else forage['success']):
                raise ValueError('Latest own FORAGE/feedback chain differs')
            frame_raw = reconstruction.canonical(world.snapshot())
            row = dict(tick=world.tick+1, actor=actor, born=actor != 0,
                       ordinary_mutating_ancestry=True, feedback=feedback,
                       forage=None if forage is None else dict(forage),
                       pre_state_sha256=hashlib.sha256(frame_raw).hexdigest())
            rows.append(row)
            if selected_context is None and earned_read(row):
                selected_raw = frame_raw
                selected_context = dict(row=len(rows)-1, tick=row['tick'], actor=actor,
                    pre_state_sha256=row['pre_state_sha256'],
                    own_turns=world.turns[actor], pc=entity['pc'], decoded=decoded[:])
        # Scalars captured before the ordinary transition mutates/removes actor.
        site = entity['pos']; port = entity['registers'][decoded[1]%2] % 2
        if not world.step():
            raise ValueError('Live source dispatch unexpectedly refused')
        event = world.events[-1]
        if event['tick'] != world.tick or event['actor'] != actor or event['decoded'] != decoded:
            raise ValueError('Original dispatch/event context differs')
        if decoded[0] == 6:
            attempt = event.get('attempt')
            latest_forage[actor] = dict(tick=world.tick,
                packet=None if attempt is None else attempt['packet'],
                site=site, port=port, success=event['feedback'])
            if attempt is not None and (attempt['position'] != site or attempt['port'] != port or attempt['success'] != event['feedback']):
                raise ValueError('FORAGE provenance differs')
        if 'birth' in event:
            extend_ancestry(ancestry, actor, event['birth']['child'])
    actual = world.snapshot()
    if reconstruction.canonical(actual) != reconstruction.canonical(original):
        raise ValueError('Complete original assigned-World replay inequality')
    # No partial original is accepted: an early endpoint is legal only if the
    # genuine source replay emptied the World; live Worlds run all4096 ticks.
    if world.tick != request['assigned_stop_tick'] and world.entities:
        raise ValueError('Live original ended before assigned horizon')
    selection = selector.select_first(rows)
    expected = None if selected_context is None else {k:selected_context[k] for k in ('row','tick','actor','pre_state_sha256')}
    if selection['selected'] != expected:
        raise ValueError('First eligible pre-treatment selector disagreement')
    context = None if selected_context is None else dict(
        actor=selected_context['actor'], tick=selected_context['tick']-1,
        own_turns=selected_context['own_turns'], pc=selected_context['pc'],
        decoded=selected_context['decoded'], common_pre_state_sha256=selected_context['pre_state_sha256'])
    return dict(schema='ORA-EKA1-REPLAY-DERIVED-SELECTION-v1',
        assignment_id=request['assignment_id'], request_sha256=hashlib.sha256(reconstruction.canonical(request)).hexdigest(),
        original_raw_sha256=hashlib.sha256(original_raw).hexdigest(),
        original_replay_equal=True, complete_read_ledger_reconstructed=True,
        selected=selection['selected'], selected_context=context,
        selected_pre_state_raw=selected_raw, read_rows=rows,
        opportunity_contrast_weight=selection['opportunity_contrast_weight'],
        actual_world_outcomes_zeroed=False, original_final_state=actual,
        replay_geneses=1, replay_dispatches=world.tick,
        requested_stop_tick=request['assigned_stop_tick'], actual_stop_tick=world.tick,
        extinct=not bool(world.entities), input_pins=INPUT_PINS.copy(),
        native_registration_authenticated=False, original_owner_authenticated=False,
        physical_raw_custody_authenticated=False, execution_authorized=False,
        scientific_admission=False)
