"""Performance-blind static source data. Never imports or executes a World."""
import base64
import hashlib
import json
import zlib
from .digital_neutral_catalogue25 import PARENT

VERSION = 'DIGITAL-NEUTRAL-TAIL-42-v1'
OPS = (1, 2, 3, 4, 5, 6, 7, 8, 18)


def digest(x):
    return hashlib.sha256(json.dumps(x, separators=(',', ':')).encode()).hexdigest()


class DrawStop(ValueError):
    def __init__(self, reason, draws):
        super().__init__(reason)
        self.draws = draws[:]


def word(identity, slot, index, draws, raw=None):
    """raw is an abstract refusal fixture hook, never a source selection input."""
    if type(identity) is not int or not 0 <= identity < 256 or type(slot) is not int or not 5 <= slot <= 12 or type(index) is not int or not 0 <= index <= 2:
        raise ValueError('Registered sample/slot/word identity required')
    radix = 9 if index == 0 else 32
    threshold = (2**32 // radix) * radix
    for counter in range(64):
        if len(draws) >= 7000:
            raise DrawStop('Global 7000 draw limit', draws)
        payload = [VERSION, 0, identity, slot, index, counter]
        u = int(digest(payload)[:8], 16) if raw is None else raw(payload)
        if type(u) is not int or not 0 <= u < 2**32:
            raise ValueError('Prepared raw draw must be uint32')
        accepted = u < threshold
        draws.append(dict(payload=payload, raw=u, radix=radix, threshold=threshold,
                          disposition='accepted' if accepted else 'range_rejected'))
        if accepted:
            residue = u % radix
            return OPS[residue] if index == 0 else residue
    raise DrawStop('Per-word 64 draw limit', draws)


def cold_prefix():
    """Prepared warm orientations, not seeds or a complete organism history."""
    rows = []
    for orientation in (0, 1):
        r = [0, 0]; memory = [0]*8; energy = 12; food = 64; heat = 55
        steps = []
        for tick, (op, a, b) in enumerate(PARENT[:5], 1):
            energy -= 1; heat += 1
            if op == 4: r[a % 2] = b % 16
            elif op == 5: r[a % 2] ^= r[b % 2]
            elif op == 3: memory[a % 8] = r[b % 2]
            elif op == 6:
                if r[a % 2] % 2 == orientation:
                    food -= 1; gain = min(20, 64-energy); energy += gain; heat += 20-gain
            else: raise ValueError('Frozen prefix contract changed')
            assert energy+73+food*20+heat == 1420
            steps.append(dict(tick=tick, energy=energy, heat=heat, food=food))
        rows.append(dict(orientation=orientation, steps=steps, registers=r,
                         memory=memory, constructor=73, prepared=True, world=False))
    return rows


def manifest():
    root = [list(t) for t in PARENT]; root_hash = digest(root)
    candidates = []; draws = []; current = []
    try:
        for identity in range(256):
            code = [t[:] for t in root]; current = []
            for slot in range(5, 13):
                for index in range(3):
                    before = digest(code); value = word(identity, slot, index, draws)
                    old = code[slot][index]; code[slot][index] = value
                    current.append(dict(flat_address=3*slot+index, old=old, new=value,
                                        changed=old != value, before_sha256=before,
                                        after_sha256=digest(code)))
            candidates.append(dict(sample_id=identity, root_program_sha256=root_hash,
                program=code, program_sha256=digest(code), assignments=current,
                formation_cost=55, state_units=16, free_material=457,
                constructor_after_formation=73, startup_energy=12,
                natural_birth=False, viability_verified=False))
    except DrawStop as exc:
        exc.partial = dict(candidates=candidates, draws=draws, current_assignments=current)
        raise
    return dict(contract=VERSION, nonce=0, declared_samples=256, raw_tail_space=(9*32*32)**8,
        root_program=root, root_program_sha256=root_hash, candidates=candidates, draws=draws,
        accepted_assignments=sum(d['disposition']=='accepted' for d in draws),
        rejected_draws=sum(d['disposition']=='range_rejected' for d in draws),
        aliases=dict(register=[16]*2, memory=[4]*8, constant=[2]*16, jump=[3]*6+[2]*7),
        cold_prefix=cold_prefix(), formation_cost=55, performance_selection=False,
        semantic_deduplication=False, world_histories=0, seeds_queried=[],
        organism_actions=0, births=0, deaths=0, learning=False, evolution=False, stage_credit=False)


if __name__ == '__main__':
    try:
        result = manifest()
    except DrawStop as exc:
        result = dict(failure=str(exc), partial=exc.partial)
        print(base64.b64encode(zlib.compress(json.dumps(result, sort_keys=True, separators=(',', ':')).encode())).decode())
        raise SystemExit(1)
    print(base64.b64encode(zlib.compress(json.dumps(result, sort_keys=True, separators=(',', ':')).encode())).decode())
