"""Abstract necessary bounds only. No World, seed lookup or candidate policy."""
import hashlib
import json
from pathlib import Path


def integer(value, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError('Abstract integer outside registered domain')
    return value


def target_identity(port, feedback, real):
    integer(port, 0, 1); integer(feedback, 0, 1)
    if type(real) is not bool:
        raise ValueError('Prepared provenance must be boolean')
    return port ^ (1 ^ feedback) if real else None


def formation(triples):
    return 3 * integer(triples, 1, 32) + 16


def state_ceiling(triples):
    return integer(triples, 1, 32) * 16**10 * 2


def earliest_fresh_completion(release, packets):
    integer(release, 1, 512); integer(packets, 1, 32)
    return release + packets - 1


def strict_tick_bound(comparator_formation, comparator_tick):
    integer(comparator_formation, 19, 112)
    if (comparator_formation - 16) % 3:
        raise ValueError('Formation must be paid triples plus state')
    integer(comparator_tick, 64, 512)
    return min(comparator_tick - 1, comparator_formation + comparator_tick - 56)


def gap_energy(energy, distance):
    integer(energy, 1, 64); integer(distance, 1, 65)
    return None if distance > energy else min(64, energy - distance + 20)


def certificate():
    truth = []
    for p in range(2):
        for t in range(2):
            f = int(p == t)
            assert target_identity(p, f, True) == t
            truth.append([p, f, t])
    assert target_identity(0, 0, False) is None
    for n in range(1, 33):
        assert formation(n) == len([0] * (3*n) + [0] * 16)
        assert 128 - formation(n) >= 16
    for e in range(1, 65):
        for d in range(1, 66):
            # Independent explicit paid-step path to one abstract success.
            live = e
            for tick in range(1, d+1):
                live -= 1
                if tick == d:
                    live = min(64, live+20)
                elif live == 0:
                    live = None; break
            assert live == gap_energy(e, d)
    count = 0
    for n in range(1, 33):
        c = formation(n)
        for t in range(64, 513):
            bound = strict_tick_bound(c, t)
            for candidate_t in (0, bound-1, bound, bound+1, 512):
                assert (candidate_t <= bound) == (candidate_t < t and 55+candidate_t < c+t)
                count += 1
    return dict(contract='DIGITAL-INFORMATION-41-v1',
        classification='abstract_necessary_bounds_only',
        real_attempt_truth_table=truth, formation_sizes=32,
        energy_gap_cases=4160, strict_comparison_cases=count,
        fixed_genotype_state_ceiling=state_ceiling(13),
        earliest_fresh_completion=earliest_fresh_completion(64, 16),
        minimum_thirteen_triple_work=formation(13)+earliest_fresh_completion(64,16),
        reachable_capacity_verified=False, viability_verified=False,
        predictive_gain_verified=False, probability_model_verified=False,
        world_histories=0, organism_actions=0, seeds_queried=[],
        candidate_policies_created=0, learning=False, stage_credit=False)


def verify_source_pins(filename):
    pins = json.loads(Path(filename).read_bytes())
    for name, expected in pins['source_sha256'].items():
        # Fixed review paths only; never import or execute fetched source.
        p = Path(name)
        if p.is_absolute() or '..' in p.parts or p.suffix != '.py' or p.parts[0] != 'experiments':
            raise ValueError('Source pin path outside exported experiment tree')
        assert hashlib.sha256(p.read_bytes()).hexdigest() == expected
    return pins['source_sha256']


if __name__ == '__main__':
    import sys
    result = certificate(); result['reviewed_source_sha256'] = verify_source_pins(sys.argv[1])
    print(json.dumps(result, sort_keys=True, separators=(',', ':')))
