"""Prospective authored digital angular-transfer histories; no natural worlds."""
import math

MASS = (1., 1., 1., 1., 1., 4.)
INERTIA = MASS
LABELS = ('a0', 'a1', 's0', 's1', 's2', 'load')
ARMS = ('candidate', 'orientation_shuffle', 'bare', 'single', 'function_disabled')
LOSSES = (12, 64)
HORIZON = 128

def initial(arm):
    if arm not in ARMS: raise ValueError('Unknown arm')
    sites = [(0., 0.), (.75, .875), (-4., 0.), (-8., 0.), (-12., 0.), (1.25, 0.)]
    angles = [0., math.pi/2, math.pi, math.pi, math.pi, 0.]
    if arm == 'orientation_shuffle': angles[:2] = angles[1::-1]
    if arm == 'bare': sites[:2] = [(-100., 20.), (-103., 20.)]
    if arm == 'single': sites[1] = (-103., 20.)
    return [[*sites[i], angles[i], .5 if 2 <= i <= 4 else 0., 0., 0.] for i in range(6)]

def field(state, disabled=False):
    """Analytic -gradient of ONE rotation-invariant potential."""
    u = [(math.cos(z[2]), math.sin(z[2])) for z in state]
    forces = [[0., 0., 0.] for _ in state]
    potential = 0.
    contacts = []
    for i in range(6):
        for j in range(i+1, 6):
            if disabled and (i < 2 or j < 2): continue
            x, y = state[i][0]-state[j][0], state[i][1]-state[j][1]
            s = x*x+y*y
            if s >= 1: continue
            a = u[i][0]*u[j][0]+u[i][1]*u[j][1]
            b = u[i][0]*x+u[i][1]*y
            c = u[j][0]*x+u[j][1]*y
            p = a*s-3*b*c
            w = 1-s
            value = p*w*w
            fx = -(w*w*(2*a*x-3*(c*u[i][0]+b*u[j][0]))-4*w*p*x)
            fy = -(w*w*(2*a*y-3*(c*u[i][1]+b*u[j][1]))-4*w*p*y)
            ti = -(s*(-u[i][1]*u[j][0]+u[i][0]*u[j][1])-3*(-u[i][1]*x+u[i][0]*y)*c)*w*w
            tj = -(s*(-u[i][0]*u[j][1]+u[i][1]*u[j][0])-3*b*(-u[j][1]*x+u[j][0]*y))*w*w
            potential += value
            for k, f in enumerate((fx, fy, ti)): forces[i][k] += f
            forces[j][0] -= fx; forces[j][1] -= fy; forces[j][2] += tj
            contacts.append((i, j, fx, fy, ti, tj, value))
    return forces, potential, contacts

def accounts(state):
    trans = sum(MASS[i]*(z[3]*z[3]+z[4]*z[4])/2 for i,z in enumerate(state))
    spin = sum(INERTIA[i]*z[5]*z[5]/2 for i,z in enumerate(state))
    momentum = [sum(MASS[i]*z[3+k] for i,z in enumerate(state)) for k in range(2)]
    angular = sum(MASS[i]*(z[0]*z[4]-z[1]*z[3])+INERTIA[i]*z[5] for i,z in enumerate(state))
    return trans, spin, momentum, angular

def load(state):
    z = state[5]
    return MASS[5]*(z[3]*z[3]+z[4]*z[4])/2

def groups(state, contacts):
    parents = list(range(6)); edges = []
    def root(i):
        while i != parents[i]: i = parents[i]
        return i
    for i,j,*tail in contacts:
        relative = sum((state[i][3+k]-state[j][3+k])**2 for k in range(2))
        internal = MASS[i]*MASS[j]/(MASS[i]+MASS[j])*relative/2
        internal += (INERTIA[i]*state[i][5]**2+INERTIA[j]*state[j][5]**2)/2
        if internal+tail[-1] < -1e-6:
            edges.append((i,j)); parents[root(i)] = root(j)
    connected = {}
    for i in range(6): connected.setdefault(root(i), []).append(i)
    return [tuple(g) for g in connected.values() if len(g)>1], edges

def simulate(arm, denominator):
    if denominator not in (128,256): raise ValueError('Unregistered resolution')
    state = initial(arm); disabled = arm == 'function_disabled'
    start = [z.copy() for z in state]
    bank = 64.; positive = 0.; pulses = []; births = []; existing = {}
    first = {}; ancestry = [{name} for name in LABELS]
    pair_work = {}; torque_work = {}; checkpoints = []
    kt,kr,mom,angular = accounts(state); _,pot,contacts = field(state,disabled)
    total = kt+kr+pot+bank
    expected_mom = mom.copy(); expected_angular = angular
    max_energy = max_momentum = max_angular = 0.
    dt = 1/denominator
    def register(t, current_contacts):
        nonlocal existing
        for i,j,*_ in current_contacts:
            for source in (i,j):
                if 2 <= source <= 4: first.setdefault(LABELS[source], t)
            joined = ancestry[i] | ancestry[j]
            ancestry[i] = joined.copy(); ancestry[j] = joined.copy()
        connected, edges = groups(state,current_contacts)
        fresh = {}
        for members in connected:
            fingerprint = (members,tuple(e for e in edges if e[0] in members and e[1] in members))
            if fingerprint in existing: item = existing[fingerprint]
            else:
                item = dict(identity='assembly:'+str(len(births)),members=list(members),
                            edges=[list(e) for e in fingerprint[1]],born=t,
                            service=0.,spin_work=0.,state=[z.copy() for z in state])
                births.append(item)
            fresh[fingerprint] = item
        existing = fresh
        return connected,edges
    register(0.,contacts)
    for tick in range(HORIZON*denominator+1):
        t = tick/denominator
        if t in LOSSES:
            before_groups, before_edges = groups(state, contacts)
            old_function = [dict(identity=b['identity'],members=b['members'].copy(),
                                 service=b['service'],spin_work=b['spin_work'])
                            for b in existing.values() if 5 in b['members'] and b['service']>.02 and abs(b['spin_work'])>.002]
            before = load(state); before_k = sum(accounts(state)[:2])
            struck=[]; delta_p=[0.,0.]; delta_l=0.
            # Fixed spatial mask and identical impulses; no function/identity labels.
            for i,z in enumerate(state):
                if -3 <= z[0] <= 6 and .25 <= z[1] <= 2:
                    struck.append(i); z[4] += .5/MASS[i]; z[5] += .5/INERTIA[i]
                    delta_p[1] += .5; delta_l += .5*z[0]+.5
            debit = sum(accounts(state)[:2])-before_k
            bank -= debit; positive += max(0.,debit)
            if bank < 0: raise ValueError('Finite intervention bank exhausted')
            expected_mom = [expected_mom[k]+delta_p[k] for k in range(2)]
            expected_angular += delta_l
            _,_,contacts = field(state,disabled)
            _,after_edges=groups(state,contacts)
            lost=[b for b in old_function if not any(tuple(e) in after_edges for e in before_edges if e[0] in b['members'] and e[1] in b['members'])]
            pulses.append(dict(time=t,struck=struck,debit=debit,load_before=before,
                               load_after=load(state),positive_before=positive-max(0.,debit),
                               functioning_before=old_function,lost=lost,
                               virgin_sources=[s for s in LABELS[2:5] if s not in first],
                               before_edges=[list(e) for e in before_edges],after_edges=[list(e) for e in after_edges]))
            register(t,contacts)
        kt,kr,mom,angular = accounts(state); _,pot,contacts = field(state,disabled)
        max_energy=max(max_energy,abs(kt+kr+pot+bank-total))
        max_momentum=max(max_momentum,*[abs(mom[k]-expected_mom[k]) for k in range(2)])
        max_angular=max(max_angular,abs(angular-expected_angular))
        if t in (0,12,64,128):
            checkpoints.append(dict(time=t,state=[z.copy() for z in state],bank=bank,
                                    translation=kt,rotation=kr,potential=pot,momentum=mom,angular=angular))
        if tick == HORIZON*denominator: break
        old=[z.copy() for z in state]
        force,_,contacts=field(state,disabled)
        register(t,contacts)
        for i,z in enumerate(state):
            for k, mass in enumerate((MASS[i],MASS[i],INERTIA[i])):
                z[3+k] += dt*force[i][k]/(2*mass)
                z[k] += dt*z[3+k]
        next_force,_,next_contacts=field(state,disabled)
        for i,z in enumerate(state):
            for k,mass in enumerate((MASS[i],MASS[i],INERTIA[i])):
                z[3+k] += dt*next_force[i][k]/(2*mass)
        oldmap={(c[0],c[1]):c for c in contacts}; newmap={(c[0],c[1]):c for c in next_contacts}
        for key in oldmap.keys() | newmap.keys():
            i,j=key; a=oldmap.get(key,(i,j,0.,0.,0.,0.,0.)); b=newmap.get(key,(i,j,0.,0.,0.,0.,0.))
            f=[(a[k]+b[k])/2 for k in range(2,6)]
            wi=f[0]*(state[i][0]-old[i][0])+f[1]*(state[i][1]-old[i][1])
            wj=-f[0]*(state[j][0]-old[j][0])-f[1]*(state[j][1]-old[j][1])
            si=f[2]*(state[i][2]-old[i][2]); sj=f[3]*(state[j][2]-old[j][2])
            label=str(i)+':'+str(j)
            pair_work.setdefault(label,[0.,0.]); torque_work.setdefault(label,[0.,0.])
            pair_work[label][0]+=wi; pair_work[label][1]+=wj
            torque_work[label][0]+=si; torque_work[label][1]+=sj
            for item in existing.values():
                members=item['members']
                if i in members and j in members:
                    if i == 5:item['service']+=wi
                    if j == 5:item['service']+=wj
                    item['spin_work']+=si+sj
        register(t+dt,next_contacts)
    final_load=load(state); last=pulses[-1]
    return dict(arm=arm,denominator=denominator,initial=start,final=state,
                source_exergy=.375,initial_potential=0.,initial_spin=0.,bank=bank,
                positive_input=positive,retained_load=final_load,
                whole_net=final_load-positive,
                post_net=final_load-last['load_before']-(positive-last['positive_before']),
                final_translation=kt,final_rotation=kr,final_potential=pot,
                max_energy_error=max_energy,max_momentum_error=max_momentum,max_angular_error=max_angular,
                births=births,pulses=pulses,source_first_contact=first,
                ancestry=[sorted(a) for a in ancestry],pair_translation_work=pair_work,
                pair_spin_work=torque_work,checkpoints=checkpoints,
                physical_fabrication_cost=None,physical_upkeep_cost=None,
                raw_memory_or_controller=False,construction_law='common paid force/torque dynamics',
                natural_worlds=0)

def panel():
    return dict(protocol='ANGULAR-TRANSFER-01-v1',worlds=0,
                records=[simulate(arm,d) for arm in ARMS for d in (128,256)],
                admission=False,replication_samples_used=0)
