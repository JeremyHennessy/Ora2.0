"""DISSIPATIVE-CAPTURE-01: finite energy-conserving encounter heat channel, authored geometries only."""
import itertools
import math

SITES = (-1.25, 0., 2.5, -100., -103.)
LAYOUTS = ((0,1),(1,0),(0,2),(2,0),(1,2),(2,1),(3,4),(1,4),(3,1))
CHARGE = (1,-1,1,-1,1,1)
MASS = (1., 1., 1., 1., 1., 4.)
LABELS = ('a0', 'a1', 's0', 's1', 's2', 'load')
PAIRS = tuple(itertools.combinations(range(6), 2))
HORIZON = 32
PULSES = (8, 16)
BOUND_EPS = 1e-6

def initial(layout):
    if layout not in LAYOUTS:
        raise ValueError('Unregistered geometry')
    return [SITES[layout[0]], SITES[layout[1]], -4., -12., -20., 1.25], [0., 0., 1., 1., 1., 0.]

def field(x, variant='ordinary'):
    force = [0.] * 6
    potential = 0.
    edges = []
    for i, j in PAIRS:
        if variant == 'force_disabled': continue
        r = x[i] - x[j]
        if abs(r) < 1:
            z = 1 - r*r
            potential += CHARGE[i]*CHARGE[j]*z*z
            f = 4*CHARGE[i]*CHARGE[j]*r*z
            force[i] += f
            force[j] -= f
            edges.append((i, j, f))
    return force, potential, edges

def kinetic(v):
    return sum(m*u*u/2 for m, u in zip(MASS, v))

def capture(x, v, heat, duration, order=PAIRS, disabled=False):
    """Reciprocal damping; actual lost translation goes into finite raw stores."""
    work = [[0.]*6 for _ in range(6)]
    paid = [[0.]*6 for _ in range(6)]
    if disabled: return work, paid
    for i,j in order:
        r=x[i]-x[j]
        if CHARGE[i]*CHARGE[j] != -1 or abs(r)>=1: continue
        relative=v[i]-v[j]
        mu=MASS[i]*MASS[j]/(MASS[i]+MASS[j])
        energy=mu*relative*relative/2
        if energy<=0: continue
        room=max(0.,min(MASS[i]-heat[i],MASS[j]-heat[j]))
        requested=energy*(-math.expm1(-2*(1-r*r)**2*(1/MASS[i]+1/MASS[j])*duration))
        transfer=min(requested,2*room)
        if transfer<=1e-16: continue
        delta=relative*(math.sqrt(max(0.,1-transfer/energy))-1)
        old_i=MASS[i]*v[i]*v[i]/2;old_j=MASS[j]*v[j]*v[j]/2
        v[i]+=MASS[j]/(MASS[i]+MASS[j])*delta
        v[j]-=MASS[i]/(MASS[i]+MASS[j])*delta
        wi=MASS[i]*v[i]*v[i]/2-old_i;wj=MASS[j]*v[j]*v[j]/2-old_j
        actual=max(0.,-wi-wj)
        heat[i]+=actual/2;heat[j]+=actual/2
        work[i][j]+=wi;work[j][i]+=wj;paid[i][j]+=actual
    return work,paid

def components(x, v, variant='ordinary'):
    parent = list(range(6))
    bound = []
    def find(i):
        while parent[i] != i:
            i = parent[i]
        return i
    for i, j in PAIRS:
        if variant == 'force_disabled': continue
        r = x[i] - x[j]
        if abs(r) < 1:
            mu = MASS[i]*MASS[j]/(MASS[i]+MASS[j])
            relative = mu*(v[i]-v[j])**2/2 + CHARGE[i]*CHARGE[j]*(1-r*r)**2
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
    if variant not in ('ordinary','force_disabled','capture_disabled','reference') or (variant in ('force_disabled','capture_disabled') and layout != (0,1)) or (variant == 'reference' and layout != (3,4)):
        raise ValueError('Frozen diagnostics only')
    x, v = initial(layout)
    if variant == 'reference':
        x = [-100.,-103.,-4.,-203.,-206.,0.]
        v = [0.,0.,1.,0.,0.,0.]
    heat = [0.]*6
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
    dissipative_work = [[0.]*6 for _ in range(6)]
    captured_by_pair = [[0.]*6 for _ in range(6)]
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
            for i in range(2):
                if -3 <= x[i] <= 3:
                    v[i] += -1 if x[i] < 0 else 1
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
                          service.get(identities[g],0.) > .02 and
                          {CHARGE[k] for k in g if k!=5} == {-1,1} and
                          all(heat[k]<MASS[k]-1e-6 for k in g if k!=5)]
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
                births.append(dict(id=serial, time=t, members=g, parents=parents, heat=[heat[k] for k in g]))
                serial += 1
        identities = new_ids
        fingerprints = new_fingerprints
        load = MASS[-1]*v[-1]**2/2
        phase = (0 if 8 < t < 16 else 1 if t > 16 else None)
        renewal_group = ()
        if phase is not None and opportunities[phase]['functional_lost']:
            loss_t = PULSES[phase]
            for g in groups:
                if 5 in g and {CHARGE[k] for k in g if k != 5} == {-1, 1} and all(heat[k]<MASS[k]-1e-6 for k in g if k != 5) and sum(captured_by_pair[i][j] for i,j in PAIRS if i in g and j in g)>1e-5 and any(source_touch.get(i, -1) >= loss_t for i in (2, 3, 4) if i in g):
                    born = next((b['time'] for b in reversed(births) if b['id'] == identities[g]), -1)
                    if born > loss_t:
                        renewal_group = g
                        qualified[phase].add(identities[g])
        force, potential, contacts = field(x, variant)
        total = kinetic(v)+potential+sum(heat)+bank
        max_error = max(max_error, abs(total-initial_total))
        def note_contacts(entries, time):
            for i,j,f in entries:
                for k in (i,j):
                    if k in (2,3,4):source_touch.setdefault(k,time)
                merged=origins[i] | origins[j] | {'pair:'+LABELS[i]+':'+LABELS[j]}
                origins[i]=merged.copy();origins[j]=merged.copy()
        note_contacts(contacts,t)
        if step % denominator == 0:
            traces.append(dict(time=t, x=x.copy(), v=v.copy(), potential=potential,
                               kinetic=kinetic(v), heat=heat.copy(), bank=bank, load=load,
                               components=[dict(id=identities[g], members=g) for g in groups]))
        if step == HORIZON*denominator:
            break
        def thermal(order):
            dw,ph=capture(x,v,heat,dt/2,order,variant in ('force_disabled','capture_disabled'))
            for i,j in PAIRS:
                dissipative_work[i][j]+=dw[i][j];dissipative_work[j][i]+=dw[j][i]
                captured_by_pair[i][j]+=ph[i][j]
                if j==5:
                    delivered=dw[5][i]
                    for g in groups:
                        if i in g and 5 in g and {CHARGE[k] for k in g if k!=5}=={-1,1} and all(heat[k]<MASS[k]-1e-6 for k in g if k!=5) and sum(captured_by_pair[a][b] for a,b in PAIRS if a in g and b in g)>1e-5:
                            service[identities[g]]=service.get(identities[g],0.)+delivered
                    if phase is not None and i in renewal_group:renewal_work[phase]+=delivered
        thermal(PAIRS)
        old_x = x.copy()
        half_v = [v[i]+dt*force[i]/(2*MASS[i]) for i in range(6)]
        x = [x[i]+dt*half_v[i] for i in range(6)]
        next_force, _, next_contacts = field(x, variant)
        v = [half_v[i]+dt*next_force[i]/(2*MASS[i]) for i in range(6)]
        thermal(tuple(reversed(PAIRS)))
        note_contacts(next_contacts,t+dt)
        f0 = {(i,j): f for i,j,f in contacts}
        f1 = {(i,j): f for i,j,f in next_contacts}
        for i,j in PAIRS:
            avg = (f0.get((i,j),0.)+f1.get((i,j),0.))/2
            pair_work[i][j] += avg*(x[i]-old_x[i])
            pair_work[j][i] -= avg*(x[j]-old_x[j])
            if j == 5:
                delivered = -avg*(x[5]-old_x[5])
                for g in groups:
                    if i in g and 5 in g and {CHARGE[k] for k in g if k != 5} == {-1, 1} and all(heat[k]<MASS[k]-1e-6 for k in g if k != 5) and sum(captured_by_pair[i][j] for i,j in PAIRS if i in g and j in g)>1e-5:
                        service[identities[g]] = service.get(identities[g],0.)+delivered
                if phase is not None and i in renewal_group:
                    renewal_work[phase] += delivered
    whole = load-positive_input
    post = load-loss_load-interval_input
    # The t16 pulse occurs BEFORE the post-loss baseline; its possible input
    # is conservatively debited as well. No output is credited to that pulse.
    last_positive = max(0., events[-1]['debit'])
    post -= last_positive
    return dict(layout=list(layout), denominator=denominator, variant=variant, initial_source_kinetic=capital,
                initial_cohesive_exergy_bound=0. if variant == 'force_disabled' else 8., initial_total_with_bank=initial_total,
                final_load=load, whole_net=whole, post_net=post, operator_positive_input=positive_input,
                final_bank=bank, final_potential=potential, final_kinetic=kinetic(v),
                max_energy_error=max_error, heat=heat, dissipative_pair_work=dissipative_work, captured_by_pair=captured_by_pair, births=births, pulses=events, exposure=opportunities,
                source_first_contact=source_touch, renewal_signed_work=renewal_work,
                renewed_components=[sorted(q) for q in qualified], load_ancestry=sorted(origins[5]),
                pair_work=pair_work, traces=traces)

def panel():
    return dict(schema='dissipative-capture01-authored-v1', natural_worlds=0,
                records=[simulate(layout, d) for layout in LAYOUTS for d in (256,512)]+
                        [simulate((0,1),d,'force_disabled') for d in (256,512)]+
                        [simulate((3,4),d,'reference') for d in (256,512)]+
                        [simulate((0,1),d,'capture_disabled') for d in (256,512)])

if __name__ == '__main__':
    import json
    print(json.dumps(panel(), sort_keys=True, allow_nan=False))
