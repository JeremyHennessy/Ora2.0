"""Literal static-source referee, no producer, catalogue or World imports."""
import base64
import hashlib
import json
import zlib

ROOT = [[4,1,1],[6,0,0],[5,0,1],[6,0,0],[3,1,0],[2,0,1],[18,0,0],
        [18,0,0],[4,1,1],[5,0,1],[3,1,0],[6,0,0],[7,0,5]]


def sha(value):
    return hashlib.sha256(json.dumps(value, separators=(',', ':')).encode()).hexdigest()


def manifest():
    draws = []; candidates = []; root_hash = sha(ROOT)
    choices = [1,2,3,4,5,6,7,8,18]
    for sample in range(256):
        flat = sum(ROOT, []); changes = []
        for address in range(15, 39):
            slot, word = divmod(address, 3); radix = len(choices) if word == 0 else 32
            maximum = 2**32 - (2**32 % radix)
            for retry in range(64):
                assert len(draws) < 7000
                payload = ['DIGITAL-NEUTRAL-TAIL-42-v1', 0, sample, slot, word, retry]
                number = int(sha(payload)[0:8], 16)
                rejected = number >= maximum
                draws.append(dict(payload=payload, raw=number, radix=radix, threshold=maximum,
                                  disposition='range_rejected' if rejected else 'accepted'))
                if not rejected: break
            else: raise ValueError('Literal per-word source exhaustion')
            before = sha([flat[j:j+3] for j in range(0,39,3)])
            old = flat[address]; residue = number % radix
            value = choices[residue] if word == 0 else residue
            flat[address] = value; code = [flat[j:j+3] for j in range(0,39,3)]
            changes.append(dict(flat_address=address, old=old, new=value, changed=value!=old,
                                before_sha256=before, after_sha256=sha(code)))
        candidates.append(dict(sample_id=sample, root_program_sha256=root_hash, program=code,
            program_sha256=sha(code), assignments=changes, formation_cost=len(flat)+16,
            state_units=16, free_material=512-len(flat)-16,
            constructor_after_formation=128-len(flat)-16, startup_energy=12,
            natural_birth=False, viability_verified=False))
    # Enumerate equality outcomes and use cumulative paid bills, not a VM.
    prefix = []
    for target in (0,1):
        energies = [11, 10+20*int(target==0), 9+20*int(target==0), 28, 27]
        food = 64; rows = []
        for i, e in enumerate(energies,1):
            if i in (2,4) and (i==2) == (target==0): food -= 1
            heat = 55+i
            assert e+73+food*20+heat == 1420
            rows.append(dict(tick=i, energy=e, heat=heat, food=food))
        prefix.append(dict(orientation=target, steps=rows, registers=[1,1],
            memory=[0,1,0,0,0,0,0,0], constructor=73, prepared=True, world=False))
    aliases = {}
    for name, modulus in [('register',2),('memory',8),('constant',16),('jump',13)]:
        aliases[name] = [sum(v%modulus==j for v in range(32)) for j in range(modulus)]
    return dict(contract='DIGITAL-NEUTRAL-TAIL-42-v1', nonce=0, declared_samples=256,
        raw_tail_space=(9*32*32)**8, root_program=ROOT, root_program_sha256=root_hash,
        candidates=candidates, draws=draws,
        accepted_assignments=len(candidates)*24,
        rejected_draws=len(draws)-len(candidates)*24,
        aliases=aliases, cold_prefix=prefix, formation_cost=55,
        performance_selection=False, semantic_deduplication=False,
        world_histories=0, seeds_queried=[], organism_actions=0, births=0, deaths=0,
        learning=False, evolution=False, stage_credit=False)


if __name__ == '__main__':
    print(base64.b64encode(zlib.compress(json.dumps(manifest(),sort_keys=True,separators=(',', ':')).encode())).decode())
