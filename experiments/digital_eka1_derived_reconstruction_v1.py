"""Unexecuted original-replay/paid-READ/derived-continuation source.

No CLI, native grant, sampler or World import on module load. Only call the
reconstruction function within separately admitted finite native execution.
Format/hash/source consistency cannot authenticate an external registration.
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Prospective parser extent only, NOT a RAM/CPU/native fit qualification.
MAX_CHECKPOINT_BYTES = 32 * 1024**2
SOURCE_PINS = {'tools/eka1_native_owner_candidate.py': '23d51193052ab97d5c9576afa3c72e49ab6ea52a4a0647c18cbc5fd0118f9b0c', 'tools/eka1_cumulative_reservations.py': '735c7fbd9564e04e715e8125df315eba47e36a8dc66c3d1a24dc23ef7c33b73d', 'experiments/__init__.py': 'd1b4e4db64becb173467ca4fc66c8770e14411b895ea5305a8fe6d2d359a15ab', 'experiments/digital_eka1_paid_read_source_v1.py': '5e50d7cdb7a1bbf44fd1255e0c51924ce6504c35062040ebbc4707b261a4a17a', 'experiments/digital_informative_exposure23_interpret.py': '66b041685abfdd5081c35a022faba68491a36df4a52cc620875ebab0e1e84aaa', 'experiments/digital_mobile54.py': '245647ae7681a57b37d5d6e939c25d76a5df1365ccbdd98de3e4bd3cbb5ae1a3', 'experiments/digital_pressure71_population.py': 'cf22e109878bae6ac6b22e0563c8593f1c93e8ac03296a9ed9cd0cd43e1400de', 'experiments/digital_sharedlineage68_population.py': '624e861387ceac70e4c2413ed852228db08f6b1ebd774e442732650ae2103609'}
REQUEST_FIELDS = {'schema', 'original_raw_sha256', 'derived_raw_sha256',
                  'binding', 'arm', 'stop_tick', 'configuration'}
CONFIG_FIELDS = {'seed', 'mode', 'fuel_mode', 'inheritance_mode', 'dose'}
ARMS = ('true', 'identity_sham', 'xor1')


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=True, allow_nan=False).encode('ascii')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def exact_hash(value):
    if type(value) is not str or len(value) != 64 or any(c not in '0123456789abcdef' for c in value):
        raise ValueError('Exact SHA256')
    return value


def integer(value, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError('Exact bounded integer')
    return value


def parse_checkpoint(raw, expected):
    if type(raw) is not bytes or not 0 < len(raw) <= MAX_CHECKPOINT_BYTES:
        raise ValueError('Checkpoint extent/type')
    if sha(raw) != exact_hash(expected):
        raise ValueError('Original/derived file bytes changed')
    def pairs(rows):
        out = {}
        for key, value in rows:
            if key in out:
                raise ValueError('Duplicate JSON key')
            out[key] = value
        return out
    def no_float(unused):
        raise ValueError('Integer source state only')
    def number(text):
        if len(text) > 32:
            raise ValueError('Integer token extent')
        return int(text)
    try:
        state = json.loads(raw, object_pairs_hook=pairs, parse_float=no_float,
                           parse_constant=no_float, parse_int=number)
    except (RecursionError, UnicodeError) as exc:
        raise ValueError('Invalid source JSON') from exc
    if type(state) is not dict:
        raise ValueError('Complete state object required')
    return state


def prepare(original_raw, derived_raw, request):
    """Metadata rejection only; does not authenticate history or call a World."""
    if type(request) is not dict or set(request) != REQUEST_FIELDS or request['schema'] != 'ORA-EKA1-RECONSTRUCT-DERIVED-v1':
        raise ValueError('Exact prospective reconstruction request')
    if type(request['arm']) is not str or request['arm'] not in ARMS:
        raise ValueError('Role')
    binding = request['binding']
    fields = {'schema', 'source_sha256', 'common_pre_state_sha256', 'actor',
              'tick', 'own_turns', 'pc', 'decoded', 'original_world_id', 'branch_ids'}
    if type(binding) is not dict or set(binding) != fields or binding['schema'] != 'ORA-EKA1-COMMON-PRE-READ-v1':
        raise ValueError('Exact pre-READ binding')
    if binding['source_sha256'] != SOURCE_PINS['experiments/digital_pressure71_population.py']:
        raise ValueError('Original source version')
    exact_hash(binding['common_pre_state_sha256'])
    pre_tick = integer(binding['tick'], 0, 4095)
    integer(binding['actor'], 0, 2**31-1); integer(binding['own_turns'], 0, 255); integer(binding['pc'], 0, 8)
    decoded = binding['decoded']
    if type(decoded) is not list or len(decoded) != 3 or any(type(x) is not int or not 0 <= x < 32 for x in decoded) or decoded[0] != 1:
        raise ValueError('Exact READ triple')
    ids = binding['branch_ids']; origin = binding['original_world_id']
    if (type(origin) is not str or not 0 < len(origin) <= 128 or type(ids) is not dict or set(ids) != set(ARMS)
            or any(type(x) is not str or not 0 < len(x) <= 128 for x in ids.values())
            or len(set(ids.values())) != 3 or origin in ids.values()):
        raise ValueError('Prospective branch identities')
    integer(request['stop_tick'], pre_tick+1, 4096)
    config = request['configuration']
    if type(config) is not dict or set(config) != CONFIG_FIELDS:
        raise ValueError('Exact registered source configuration')
    integer(config['seed'], 0, 2**63-1)
    if config['mode'] not in ('faithful', 'mutating') or config['fuel_mode'] not in ('renewed', 'no_inflow') or config['inheritance_mode'] not in ('parent_copy', 'ancestor_copy'):
        raise ValueError('Source configuration')
    if config['inheritance_mode'] == 'ancestor_copy' and config['mode'] != 'mutating':
        raise ValueError('Source inheritance law')
    if type(config['dose']) is not int or config['dose'] not in (1, 8):
        raise ValueError('Source dose')
    original = parse_checkpoint(original_raw, request['original_raw_sha256'])
    derived = parse_checkpoint(derived_raw, request['derived_raw_sha256'])
    if type(original.get('tick')) is not int or original['tick'] != pre_tick:
        raise ValueError('Pre-dispatch tick mismatch')
    integer(derived.get('tick'), pre_tick+1, request['stop_tick'])
    for field, value in config.items():
        key = '_dose' if field == 'dose' else field
        if type(original.get(key)) is not type(value) or original[key] != value:
            raise ValueError('Original configuration differs')
    if sha(canonical(original)) != binding['common_pre_state_sha256']:
        raise ValueError('Complete canonical pre-state differs')
    # This is only format/byte consistency. Full schema and law are proved below
    # by the unchanged original restore and an entire derived reconstruction.
    return original, derived


def reservation_class():
    """Reject unreviewed ledger files/origins; not loaded-code authentication."""
    name = 'tools/eka1_cumulative_reservations.py'
    path = ROOT/name
    if path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest() != SOURCE_PINS[name]:
        raise ValueError('Pinned reservation source changed')
    from tools import eka1_cumulative_reservations as budget_source
    if Path(budget_source.__file__).resolve() != path.resolve():
        raise ValueError('Reservation module origin differs')
    return budget_source.Reservations


def owner_class():
    """Preparation-path source/origin check; never native authority."""
    name = 'tools/eka1_native_owner_candidate.py'
    path = ROOT/name
    if path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest() != SOURCE_PINS[name]:
        raise ValueError('Pinned owner source changed')
    from tools import eka1_native_owner_candidate as owner_source
    if Path(owner_source.__file__).resolve() != path.resolve():
        raise ValueError('Owner module origin differs')
    return owner_source.NativeOwnerCandidate


def runtime_sources():
    if sys.flags.optimize:
        raise RuntimeError('Original source assertions must remain enabled')
    for name, digest in SOURCE_PINS.items():
        path = ROOT/name
        if path.is_symlink() or sha(path.read_bytes()) != digest:
            raise ValueError('Pinned runtime source changed: '+name)
    # These imports and all subsequent calls are UNEXECUTED in source checks.
    from experiments.digital_pressure71_population import World
    from experiments.digital_eka1_paid_read_source_v1 import paid_read_dispatch
    for name in SOURCE_PINS:
        module_name = name[:-3].replace('/', '.') if name != 'experiments/__init__.py' else 'experiments'
        module = sys.modules.get(module_name)
        if module is None or Path(module.__file__).resolve() != (ROOT/name).resolve():
            raise ValueError('Runtime module origin differs: '+name)
    return World, paid_read_dispatch


def reconstruct_and_verify(original_raw, derived_raw, request, *, reservations, genesis_index, owner):
    """One original-prefix replay, one paid READ, ordinary suffix; no raw load.

    The original World.restore performs genesis, paid replay and exact original
    snapshot equality. Never assign a supplied derived dictionary to __dict__.
    This function supplies no native/physical registration authentication.
    """
    Reservations = reservation_class()
    if type(reservations) is not Reservations:
        raise TypeError('Exact owner reservation ledger required')
    if type(owner) is not owner_class():
        raise TypeError('Exact canonical owner required')
    # The canonical owner derives the complete prefix+READ+suffix bound from
    # the fixed request, consumes it on the physical ledger, then holds native
    # execution before runtime imports. No caller-supplied smaller tail bound.
    owner.replay(reservations, assignment_id=request['binding']['original_world_id'],
                 dose=request['configuration']['dose'], role=request['arm'],
                 request=request, genesis_index=genesis_index)
    original, claimed = prepare(original_raw, derived_raw, request)
    World, paid_read = runtime_sources()
    world = World.restore(original)
    if canonical(world.snapshot()) != canonical(original):
        raise ValueError('Original full replay inequality')
    pre_tick = world.tick
    if paid_read(world, request['binding'], request['arm']) is not True or world.tick != pre_tick+1:
        raise ValueError('One paid READ dispatch required')
    paid_event = world.events[-1]
    if paid_event['tick'] != pre_tick+1 or paid_event['decoded'] != request['binding']['decoded'] or paid_event['actor'] != request['binding']['actor']:
        raise ValueError('Actual paid READ context differs')
    paid_event_sha256 = sha(canonical(paid_event))
    while world.tick < request['stop_tick']:
        if not world.step():
            break  # Genuine extinction keeps its actual terminal tick/outcome.
    actual = world.snapshot()
    if canonical(actual) != canonical(claimed):
        raise ValueError('Derived checkpoint not exactly reconstructed')
    # An external native/physical receipt must still bind all these inputs and
    # this module's exact source bytes to the real registered original owner.
    return actual, dict(schema='ORA-EKA1-RECONSTRUCTED-DERIVED-v1',
        original_raw_sha256=sha(original_raw), derived_raw_sha256=sha(derived_raw),
        request_sha256=sha(canonical(request)), source_pins=SOURCE_PINS.copy(),
        original_replay_equal=True, complete_derived_reconstruction_equal=True,
        original_prefix_dispatches=pre_tick, paid_read_dispatches=1,
        suffix_dispatches=world.tick-pre_tick-1, requested_stop_tick=request['stop_tick'],
        actual_stop_tick=world.tick, extinct=not bool(world.entities),
        paid_read_event_sha256=paid_event_sha256,
        derived_is_original_history=False, native_registration_authenticated=False,
        original_owner_authenticated=False, selection_ledger_authenticated=False,
        execution_authorized=False, scientific_admission=False)
