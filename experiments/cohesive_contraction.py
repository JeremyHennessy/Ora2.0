"""COHESION-01: common finite cohesive Hamiltonian, authored geometries only."""
import itertools
import math

SITES = (-1.1, 0.0, 4.4, 5.5)
LAYOUTS = tuple(itertools.combinations(range(4), 2))
MASS = (1., 1., 1., 1., 1., 4.)
LABELS = ('a0', 'a1', 's0', 's1', 's2', 'load')
PAIRS = tuple(itertools.combinations(range(6), 2))
HORIZON = 96
PULSES = (32, 64)
BOUND_EPS = 1e-6

def initial(layout):
    if layout not in LAYOUTS:
        raise ValueError('Unregistered geometry')
    return [SITES[layout[0]], SITES[layout[1]], -4., -12., -20., 1.1], [0., 0., .25, .25, .25, 0.]

def field(x, variant='ordinary'):
    force = [0.] * 6
    potential = 0.
    edges = []
    for i, j in PAIRS:
        if variant == 'cohesion_disabled': continue
        r = x[i] - x[j]
        if abs(r) < 1:
            z = 1 - r*r
            potential -= z*z
            f = -4*r*z
            force[i] += f
            force[j] -= f
            edges.append((i, j, f))
    return force, potential, edges

def kinetic(v):
    return sum(m*u*u/2 for m, u in zip(MASS, v))

def components(x, v, variant='ordinary'):
    parent = list(range(6))
    bound = []
    def find(i):
        while parent[i] != i:
            i = parent[i]
        return i
    for i, j in PAIRS:
        if variant == 'cohesion_disabled': continue
        r = x[i] - x[j]
        if abs(r) < 1:
            mu = MASS[i]*MASS[j]/(MASS[i]+MASS[j])
            relative = mu*(v[i]-v[j])**2/2 - (1-r*r)**2
            if relative < -BOUND_EPS:
                parent[find(j)] = find(i)
                bound.append((i, j))
    groups = {}
    for i in range(6):
        groups.setdefault(find(i), []).append(i)
    return tuple(sorted(tuple(g) for g in groups.values())), tuple(bound)

def simulate(layout, denominator, variant='ordinary'):
    if denominator not in (256, 512):
        raise ValueError('Frozen resolutions only')
    if variant not in ('ordinary','cohesion_disabled') or (variant != 'ordinary' and layout != (0,1)):
        raise ValueError('Frozen diagnostics only')
    x, v = initial(layout)
    dt = 1/denominator
    capital = kinetic(v)  # All initial pair potentials are exactly zero.
    bank = 64.
    initial_total = capital + bank
    source_touch = {}
    groups, _ = components(x, v, variant)
    identities = {g: i for i, g in enumerate(groups)}
    fingerprints = {g: () for g in groups}
    serial = len(groups)
    births = []
    events = []
    traces = []
    positive_input = 0.
    interval_input = 0.
    loss_load = 0.
    max_error = 0.
    pair_work = [[0.]*6 for _ in range(6)]
    origins = [{name} for name in LABELS]
    opportunities = []
    renewal_work = [0., 0.]
    qualified = [set(), set()]
    service = {}
    for step in range(HORIZON*denominator + 1):
        t = step/denominator
        if t in PULSES:
            before_groups, before_edges = components(x, v, variant)
            old = kinetic(v)
            struck = []
            for i in range(5):
                if -3 <= x[i] <= 3:
                    v[i] += -2 if x[i] < 0 else 2
                    origins[i].add('pulse'+str(int(t)))
                    struck.append(i)
            debit = kinetic(v)-old
            if bank-debit < 0:
                raise ValueError('Finite intervention bank exhausted')
            bank -= debit
            positive_input += max(0., debit)
            interval_input = 0.
            loss_load = MASS[-1]*v[-1]**2/2
            _, after_edges = components(x, v, variant)
            destroyed = [g for g in before_groups if len(g) >= 2 and
                         any(i in struck for i in g) and
                         not any(i in g and j in g for i, j in after_edges)]
            functional = [g for g in destroyed if g in identities and
                          fingerprints[g] == tuple(e for e in before_edges if e[0] in g and e[1] in g) and
                          service.get(identities[g],0.) > .02]
            fresh = [i for i in (2, 3, 4) if i not in source_touch]
            opportunities.append(dict(time=t, struck=struck, pre_groups=before_groups,
                                      pre_bound=before_edges, post_bound=after_edges,
                                      all_edges_lost=destroyed, functional_lost=functional,
                                      fresh_sources=fresh))
            events.append(dict(kind='external_pulse', time=t, debit=debit, bank=bank))
        groups, edges = components(x, v, variant)
        new_ids = {}
        new_fingerprints = {}
        for g in groups:
            signature = tuple(e for e in edges if e[0] in g and e[1] in g)
            new_fingerprints[g] = signature
            if g in identities and fingerprints[g] == signature:
                new_ids[g] = identities[g]
            else:
                parents = sorted(identities[h] for h in identities if set(g)&set(h))
                new_ids[g] = serial
                births.append(dict(id=serial, time=t, members=g, parents=parents))
                serial += 1
        identities = new_ids
        fingerprints = new_fingerprints
        load = MASS[-1]*v[-1]**2/2
        phase = (0 if 32 < t < 64 else 1 if t > 64 else None)
        renewal_group = ()
        if phase is not None and opportunities[phase]['functional_lost']:
            loss_t = PULSES[phase]
            for g in groups:
                if 5 in g and len(g) >= 3 and any(source_touch.get(i, -1) >= loss_t for i in (2, 3, 4) if i in g):
                    born = next((b['time'] for b in reversed(births) if b['id'] == identities[g]), -1)
                    if born > loss_t:
                        renewal_group = g
                        qualified[phase].add(identities[g])
        force, potential, contacts = field(x, variant)
        total = kinetic(v)+potential+bank
        max_error = max(max_error, abs(total-initial_total))
        for i, j, f in contacts:
            for k in (i, j):
                if k in (2, 3, 4):
                    source_touch.setdefault(k, t)
            merged = origins[i] | origins[j] | {'well:'+LABELS[i]+':'+LABELS[j]}
            origins[i] = merged.copy()
            origins[j] = merged.copy()
        if step % denominator == 0:
            traces.append(dict(time=t, x=x.copy(), v=v.copy(), potential=potential,
                               kinetic=kinetic(v), bank=bank, load=load,
                               components=[dict(id=identities[g], members=g) for g in groups]))
        if step == HORIZON*denominator:
            break
        old_x = x.copy()
        half_v = [v[i]+dt*force[i]/(2*MASS[i]) for i in range(6)]
        x = [x[i]+dt*half_v[i] for i in range(6)]
        next_force, _, next_contacts = field(x, variant)
        v = [half_v[i]+dt*next_force[i]/(2*MASS[i]) for i in range(6)]
        f0 = {(i,j): f for i,j,f in contacts}
        f1 = {(i,j): f for i,j,f in next_contacts}
        for i,j in PAIRS:
            avg = (f0.get((i,j),0.)+f1.get((i,j),0.))/2
            pair_work[i][j] += avg*(x[i]-old_x[i])
            pair_work[j][i] -= avg*(x[j]-old_x[j])
            if j == 5:
                delivered = -avg*(x[5]-old_x[5])
                for g in groups:
                    if len(g)>=3 and i in g and 5 in g:
                        service[identities[g]] = service.get(identities[g],0.)+delivered
                if phase is not None and i in renewal_group:
                    renewal_work[phase] += delivered
    whole = load-positive_input
    post = load-loss_load-interval_input
    # The t64 pulse occurs BEFORE the post-loss baseline; its possible input
    # is conservatively debited as well. No output is credited to that pulse.
    last_positive = max(0., events[-1]['debit'])
    post -= last_positive
    return dict(layout=list(layout), denominator=denominator, variant=variant, initial_source_kinetic=capital,
                initial_cohesive_exergy_bound=15. if variant == 'ordinary' else 0., initial_total_with_bank=initial_total,
                final_load=load, whole_net=whole, post_net=post, operator_positive_input=positive_input,
                final_bank=bank, final_potential=potential, final_kinetic=kinetic(v),
                max_energy_error=max_error, births=births, pulses=events, exposure=opportunities,
                source_first_contact=source_touch, renewal_signed_work=renewal_work,
                renewed_components=[sorted(q) for q in qualified], load_ancestry=sorted(origins[5]),
                pair_work=pair_work, traces=traces)

def panel():
    return dict(schema='cohesion01-authored-v1', natural_worlds=0,
                records=[simulate(layout, d) for layout in LAYOUTS for d in (256,512)]+
                        [simulate((0,1),d,'cohesion_disabled') for d in (256,512)])

if __name__ == '__main__':
    import json
    print(json.dumps(panel(), sort_keys=True, allow_nan=False))
