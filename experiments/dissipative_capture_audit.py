"""Independent ODE/intervention and receipt interpreter; imports no producer."""
import itertools
import math

def unique(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise ValueError('Duplicate JSON key')
        out[key] = value
    return out

def _finite(value):
    if type(value) is bool:
        raise ValueError('Boolean numeric or identity field')
    if isinstance(value, dict):
        for v in value.values(): _finite(v)
    elif isinstance(value, list):
        for v in value: _finite(v)
    elif isinstance(value, float) and not math.isfinite(value):
        raise ValueError('Nonfinite number')

def _physics(position, velocity, disabled=False):
    masses = (1.,1.,1.,1.,1.,4.)
    accelerations = [0.]*6
    potential = 0.
    for a in range(6):
        for b in range(a+1,6):
            if disabled: continue
            distance = position[a]-position[b]
            if -1 < distance < 1:
                well = 1-distance*distance
                potential += (1,-1,1,-1,1,1)[a]*(1,-1,1,-1,1,1)[b]*well*well
                push = 4*(1,-1,1,-1,1,1)[a]*(1,-1,1,-1,1,1)[b]*distance*well
                accelerations[a] += push/masses[a]
                accelerations[b] -= push/masses[b]
    kinetic = sum(masses[i]*velocity[i]*velocity[i]/2 for i in range(6))
    return accelerations, potential, kinetic

def _contact_forces(position, disabled=False):
    if disabled: return {}
    result = {}
    for a in range(6):
        for b in range(a+1,6):
            r = position[a]-position[b]
            if abs(r)<1:
                # Use the identical analytic derivative evaluation as _physics;
                # float exponentiation can round differently from multiplication.
                result[a,b] = 4*(1,-1,1,-1,1,1)[a]*(1,-1,1,-1,1,1)[b]*r*(1-r*r)
    return result

def _thermal(position, velocity, internal, duration, reverse=False, off=False, reference=False):
    masses=(1.,1.,1.,1.,1.,4.);q=(1,-1,1,-1,1,1)
    work=[[0.]*6 for _ in range(6)];heat_pairs=[[0.]*6 for _ in range(6)]
    if off:return work,heat_pairs
    pairs=list(itertools.combinations(range(6),2))
    if reverse:pairs.reverse()
    for left,right in pairs:
        distance=position[left]-position[right]
        if q[left]*q[right]!=-1 or not -1<distance<1:continue
        relative=velocity[left]-velocity[right]
        reduced=masses[left]*masses[right]/(masses[left]+masses[right])
        relative_energy=reduced*relative*relative/2
        if relative_energy<=0:continue
        remaining=max(0.,min(masses[left]-internal[left],masses[right]-internal[right]))
        requested=relative_energy*(-math.expm1(-2*(1-distance*distance)**2*(1/masses[left]+1/masses[right])*duration))
        transfer=min(requested,2*remaining)
        if transfer<=1e-16:continue
        old_left=masses[left]*velocity[left]*velocity[left]/2
        old_right=masses[right]*velocity[right]*velocity[right]/2
        ratio=math.sqrt(max(0.,1-transfer/relative_energy))
        if reference:
            center=(masses[left]*velocity[left]+masses[right]*velocity[right])/(masses[left]+masses[right])
            velocity[left]=center+masses[right]/(masses[left]+masses[right])*relative*ratio
            velocity[right]=center-masses[left]/(masses[left]+masses[right])*relative*ratio
        else:
            difference=relative*(ratio-1)
            velocity[left]+=masses[right]/(masses[left]+masses[right])*difference
            velocity[right]-=masses[left]/(masses[left]+masses[right])*difference
        wl=masses[left]*velocity[left]*velocity[left]/2-old_left
        wr=masses[right]*velocity[right]*velocity[right]/2-old_right
        actual=max(0.,-wl-wr)
        internal[left]+=actual/2;internal[right]+=actual/2
        work[left][right]+=wl;work[right][left]+=wr;heat_pairs[left][right]+=actual
    return work,heat_pairs

def _rk4(layout, resolution, disabled=False, reference=False, capture_off=False):
    locations = (-1.25,0.,2.5,-100.,-103.)
    state = [locations[layout[0]],locations[layout[1]],-4.,-12.,-20.,1.25,0.,0.,1.,1.,1.,0.]
    if reference: state = [-100.,-103.,-4.,-203.,-206.,0.,0.,0.,1.,0.,0.,0.]
    internal=[0.]*6
    h = 1/resolution
    bank = 64.
    pulses = []
    baseline = 0.
    drift = 0.
    def derivative(z):
        accel, _, _ = _physics(z[:6],z[6:],disabled)
        return z[6:] + accel
    for step in range(32*resolution+1):
        t = step/resolution
        if t in (8,16):
            before = _physics(state[:6],state[6:],disabled)[2]
            for a in range(2):
                if -3 <= state[a] <= 3:
                    state[a+6] += -1 if state[a] < 0 else 1
            paid = _physics(state[:6],state[6:],disabled)[2]-before
            bank -= paid
            pulses.append(paid)
            baseline = 2*state[11]**2
        _, u, k = _physics(state[:6],state[6:],disabled)
        drift = max(drift,abs(k+u+sum(internal)+bank-(64.5 if reference else 65.5)))
        if step == 32*resolution: break
        speed=state[6:]
        _thermal(state[:6],speed,internal,h/2,off=disabled or capture_off,reference=True)
        state[6:]=speed
        k1 = derivative(state)
        k2 = derivative([state[i]+h*k1[i]/2 for i in range(12)])
        k3 = derivative([state[i]+h*k2[i]/2 for i in range(12)])
        k4 = derivative([state[i]+h*k3[i] for i in range(12)])
        state = [state[i]+h*(k1[i]+2*k2[i]+2*k3[i]+k4[i])/6 for i in range(12)]
        speed=state[6:]
        _thermal(state[:6],speed,internal,h/2,reverse=True,off=disabled or capture_off,reference=True)
        state[6:]=speed
    work = 2*state[11]**2
    return dict(load=work, whole=work-sum(max(0,p) for p in pulses),
                post=work-baseline-max(0,pulses[-1]), bank=bank,
                potential=u, kinetic=k, heat=internal, drift=drift, pulses=pulses)

def _replay_metadata(row):
    """Reconstruct every reported identity, loss, source and work attribution."""
    names = ('a0','a1','s0','s1','s2','load')
    masses = (1.,1.,1.,1.,1.,4.)
    locations = (-1.25,0.,2.5,-100.,-103.)
    x = [locations[row['layout'][0]],locations[row['layout'][1]],-4.,-12.,-20.,1.25]
    velocity = [0.,0.,1.,1.,1.,0.]
    scale = row['denominator']
    disabled = row['variant'] == 'force_disabled'
    reference = row['variant'] == 'reference'
    capture_off = row['variant'] in ('force_disabled','capture_disabled')
    if reference:
        x = [-100.,-103.,-4.,-203.,-206.,0.]
        velocity = [0.,0.,1.,0.,0.,0.]
    internal=[0.]*6
    h = 1/scale
    bank = 64.
    touch = {}
    sources = [{n} for n in names]
    active = {(a,):a for a in range(6)}
    fingerprints = {(a,):() for a in range(6)}
    serial = 6
    births = []
    losses = []
    pulses = []
    traces = []
    renewed = [set(),set()]
    attributed = [0.,0.]
    service = {}
    matrix = [[0.]*6 for _ in range(6)]
    dissipative = [[0.]*6 for _ in range(6)]
    heat_pairs = [[0.]*6 for _ in range(6)]
    def geometry():
        edges = []
        clusters = [{a} for a in range(6)]
        for a in range(6):
            for b in range(a+1,6):
                if disabled: continue
                r = x[a]-x[b]
                if abs(r) < 1:
                    mu = masses[a]*masses[b]/(masses[a]+masses[b])
                    if mu*(velocity[a]-velocity[b])**2/2+(1,-1,1,-1,1,1)[a]*(1,-1,1,-1,1,1)[b]*(1-r*r)**2 < -1e-6:
                        edges.append((a,b))
                        left = next(g for g in clusters if a in g)
                        right = next(g for g in clusters if b in g)
                        if left is not right:
                            left.update(right)
                            clusters.remove(right)
        return sorted(tuple(sorted(g)) for g in clusters),tuple(edges)
    def contacts():
        return _contact_forces(x,disabled)
    for step in range(32*scale+1):
        time = step/scale
        if time in (8,16):
            groups,old_edges = geometry()
            before = _physics(x,velocity,disabled)[2]
            hit = []
            for a in range(2):
                if -3 <= x[a] <= 3:
                    hit.append(a)
                    velocity[a] += -1 if x[a] < 0 else 1
                    sources[a].add('pulse'+str(int(time)))
            debit = _physics(x,velocity,disabled)[2]-before
            bank -= debit
            _,remaining = geometry()
            lost = [g for g in groups if len(g)>=2 and any(a in hit for a in g)
                    and not any(a in g and b in g for a,b in remaining)]
            functional = [g for g in lost if g in active and
                          fingerprints[g] == tuple(e for e in old_edges if e[0] in g and e[1] in g)
                          and service.get(active[g],0.) > .02
                          and {(1,-1,1,-1,1,1)[k] for k in g if k!=5} == {-1,1}
                          and all(internal[k]<masses[k]-1e-6 for k in g if k!=5)]
            losses.append(dict(time=time,struck=hit,pre_groups=groups,pre_bound=old_edges,
                               post_bound=remaining,all_edges_lost=lost,functional_lost=functional,
                               fresh_sources=[a for a in (2,3,4) if a not in touch]))
            pulses.append(dict(kind='external_pulse',time=time,debit=debit,bank=bank))
        groups,edges = geometry()
        new_active = {}
        new_fingerprints = {}
        for group in groups:
            signature = tuple(e for e in edges if e[0] in group and e[1] in group)
            new_fingerprints[group] = signature
            if group in active and fingerprints[group] == signature:
                new_active[group] = active[group]
            else:
                parents = sorted(active[old] for old in active if set(old)&set(group))
                births.append(dict(id=serial,time=time,members=group,parents=parents,heat=[internal[k] for k in group]))
                new_active[group] = serial
                serial += 1
        active = new_active
        fingerprints = new_fingerprints
        load = 2*velocity[5]**2
        phase = 0 if 8 < time < 16 else 1 if time > 16 else None
        replacement = ()
        if phase is not None and losses[phase]['functional_lost']:
            for group in groups:
                if 5 in group and {(1,-1,1,-1,1,1)[k] for k in group if k != 5} == {-1,1} and all(internal[k]<masses[k]-1e-6 for k in group if k!=5) and sum(heat_pairs[a][b] for a,b in itertools.combinations(range(6),2) if a in group and b in group)>1e-5 and any(touch.get(a,-1)>= (8,16)[phase] for a in (2,3,4) if a in group):
                    created = next((b['time'] for b in reversed(births) if b['id']==active[group]),-1)
                    if created > (8,16)[phase]:
                        replacement = group
                        renewed[phase].add(active[group])
        accel,potential,ke = _physics(x,velocity,disabled)
        old_contacts = contacts()
        def note(entries, when):
            for a,b in entries:
                for k in (a,b):
                    if k in (2,3,4):touch.setdefault(k,when)
                union=sources[a] | sources[b] | {'pair:'+names[a]+':'+names[b]}
                sources[a]=union.copy();sources[b]=union.copy()
        note(old_contacts,time)
        if step % scale == 0:
            traces.append(dict(time=time,x=x.copy(),v=velocity.copy(),potential=potential,
                               kinetic=ke,heat=internal.copy(),bank=bank,load=load,
                               components=[dict(id=active[g],members=g) for g in groups]))
        if step==32*scale: break
        def thermal(reverse):
            dw,ph=_thermal(x,velocity,internal,h/2,reverse,capture_off)
            for a,b in itertools.combinations(range(6),2):
                dissipative[a][b]+=dw[a][b];dissipative[b][a]+=dw[b][a]
                heat_pairs[a][b]+=ph[a][b]
                if b==5:
                    delivered=dw[5][a]
                    for group in groups:
                        if a in group and 5 in group and {(1,-1,1,-1,1,1)[k] for k in group if k!=5}=={-1,1} and all(internal[k]<masses[k]-1e-6 for k in group if k!=5) and sum(heat_pairs[i][j] for i,j in itertools.combinations(range(6),2) if i in group and j in group)>1e-5:
                            service[active[group]]=service.get(active[group],0.)+delivered
                    if phase is not None and a in replacement:attributed[phase]+=delivered
        thermal(False)
        old_x = x.copy()
        half = [velocity[a]+h*accel[a]/2 for a in range(6)]
        x = [x[a]+h*half[a] for a in range(6)]
        new_accel = _physics(x,velocity,disabled)[0]
        velocity = [half[a]+h*new_accel[a]/2 for a in range(6)]
        thermal(True)
        new_contacts = contacts()
        note(new_contacts,time+h)
        for a in range(6):
            for b in range(a+1,6):
                push = (old_contacts.get((a,b),0.)+new_contacts.get((a,b),0.))/2
                matrix[a][b] += push*(x[a]-old_x[a])
                matrix[b][a] -= push*(x[b]-old_x[b])
                if b == 5:
                    delivered = -push*(x[5]-old_x[5])
                    for group in groups:
                        if a in group and 5 in group and {(1,-1,1,-1,1,1)[k] for k in group if k != 5} == {-1,1} and all(internal[k]<masses[k]-1e-6 for k in group if k!=5) and sum(heat_pairs[a][b] for a,b in itertools.combinations(range(6),2) if a in group and b in group)>1e-5:
                            service[active[group]] = service.get(active[group],0.)+delivered
                    if phase is not None and a in replacement:
                        attributed[phase] += delivered
    expected = dict(births=births,pulses=pulses,exposure=losses,source_first_contact=touch,
                    renewed_components=[sorted(g) for g in renewed],renewal_signed_work=attributed,
                    load_ancestry=sorted(sources[5]),pair_work=matrix,traces=traces,heat=internal,dissipative_pair_work=dissipative,captured_by_pair=heat_pairs)
    # Canonical JSON preserves types as well as values and normalizes integer
    # dictionary keys and tuple/list representation at the file boundary.
    import json
    for key,value in expected.items():
        if json.dumps(row[key],sort_keys=True) != json.dumps(value,sort_keys=True):
            raise ValueError('Independent metadata reconstruction: '+key)

def _check_record(row):
    fields = {'layout','denominator','variant','initial_source_kinetic','initial_cohesive_exergy_bound',
              'initial_total_with_bank','final_load','whole_net','post_net','operator_positive_input',
              'final_bank','final_potential','final_kinetic','max_energy_error','births','pulses',
              'exposure','source_first_contact','renewal_signed_work','renewed_components',
              'load_ancestry','pair_work','traces','heat','dissipative_pair_work','captured_by_pair'}
    if set(row) != fields: raise ValueError('Record fields')
    _finite(row)
    if row['variant'] not in ('ordinary','force_disabled','capture_disabled','reference'): raise ValueError('Variant')
    disabled = row['variant'] == 'force_disabled'
    reference = row['variant'] == 'reference'
    capture_off = row['variant'] in ('force_disabled','capture_disabled')
    if len(row['layout']) != 2 or any(type(a) is not int for a in row['layout']): raise ValueError('Layout types')
    if type(row['denominator']) is not int or row['denominator'] not in (256,512):
        raise ValueError('Resolution')
    if row['initial_source_kinetic'] != (.5 if reference else 1.5) or row['initial_cohesive_exergy_bound'] != (0. if disabled else 8.) or row['initial_total_with_bank'] != (64.5 if reference else 65.5):
        raise ValueError('Capital')
    traces = row['traces']
    if len(traces) != 33 or [t['time'] for t in traces] != list(range(33)):
        raise ValueError('Trace coverage')
    maximum = 0.
    for snapshot in traces:
        _, u, k = _physics(snapshot['x'],snapshot['v'],disabled)
        if abs(u-snapshot['potential']) > 1e-12 or abs(k-snapshot['kinetic']) > 1e-12 or abs(2*snapshot['v'][5]**2-snapshot['load']) > 1e-12:
            raise ValueError('Snapshot energy')
        maximum = max(maximum,abs(k+u+sum(snapshot['heat'])+snapshot['bank']-(64.5 if reference else 65.5)))
        if snapshot['bank'] < 0 or u < -8-1e-12:
            raise ValueError('Finite store')
        if len(snapshot['heat'])!=6 or any(h<0 or h>m+1e-10 for h,m in zip(snapshot['heat'],(1.,1.,1.,1.,1.,4.))):raise ValueError('Finite heat capacity')
        represented = [a for c in snapshot['components'] for a in c['members']]
        if sorted(represented) != list(range(6)):
            raise ValueError('Material ownership')
    if row['max_energy_error'] < maximum-1e-12 or row['max_energy_error'] > .002:
        raise ValueError('Verlet drift gate')
    if row['heat']!=traces[-1]['heat'] or abs(sum(row['heat'])-sum(sum(q) for q in row['captured_by_pair']))>1e-10:raise ValueError('Heat ancestry account')
    if row['traces'][-1]['load'] != row['final_load']:
        raise ValueError('Final load')
    if [p['time'] for p in row['pulses']] != [8,16]: raise ValueError('Pulse times')
    debits = [p['debit'] for p in row['pulses']]
    if abs(row['operator_positive_input']-sum(max(0,p) for p in debits)) > 1e-12:
        raise ValueError('External input debit')
    if abs(row['whole_net']-(row['final_load']-row['operator_positive_input'])) > 1e-12:
        raise ValueError('Whole metric')
    if abs(row['post_net']-(row['final_load']-traces[16]['load']-max(0,debits[1]))) > 1e-12:
        raise ValueError('Post metric')
    births = row['births']
    if [b['id'] for b in births] != list(range(6,6+len(births))): raise ValueError('Fresh serials')
    known = {i: (i,) for i in range(6)}
    for birth in births:
        if not birth['parents'] or any(type(p) is not int or p not in known for p in birth['parents']):
            raise ValueError('Birth parents')
        if sorted(set(birth['members'])) != birth['members'] or any(a not in range(6) for a in birth['members']):
            raise ValueError('Birth material')
        if any(not set(known[p]) & set(birth['members']) for p in birth['parents']):
            raise ValueError('Ancestry')
        known[birth['id']] = tuple(birth['members'])
    for t in traces:
        for c in t['components']:
            if tuple(c['members']) != known.get(c['id']): raise ValueError('Component identity')
    _replay_metadata(row)
    # A different integrator independently solves the constitutive equations,
    # including finite-bank pulses. No receipt score controls its evolution.
    independent = _rk4(row['layout'],row['denominator'],disabled,reference,capture_off)
    if independent['drift'] > .0002: raise ValueError('RK4 drift gate')
    for key, expected in [('final_load','load'),('whole_net','whole'),('post_net','post'),
                          ('final_bank','bank'),('final_potential','potential'),('final_kinetic','kinetic')]:
        if abs(row[key]-independent[expected]) > .02:
            raise ValueError('Independent dynamics disagree: '+key)
    if any(abs(h-i)>.02 for h,i in zip(row['heat'],independent['heat'])):raise ValueError('Independent heat dynamics')
    return independent

def audit(data):
    if set(data) != {'schema','natural_worlds','records'} or data['schema'] != 'dissipative-capture01-authored-v1' or type(data['natural_worlds']) is not int or data['natural_worlds'] != 0:
        raise ValueError('Authored scope')
    layouts = [(0,1),(1,0),(0,2),(2,0),(1,2),(2,1),(3,4),(1,4),(3,1)]
    expected = [(list(g),d,'ordinary') for g in layouts for d in (256,512)]+[([0,1],d,'force_disabled') for d in (256,512)]+[([3,4],d,'reference') for d in (256,512)]+[([0,1],d,'capture_disabled') for d in (256,512)]
    if [(r['layout'],r['denominator'],r['variant']) for r in data['records']] != expected:
        raise ValueError('Complete unscreened authored list')
    independent = [_check_record(row) for row in data['records']]
    fine = data['records'][1::2]
    for coarse,refined in zip(data['records'][::2],fine):
        for key in ('final_load','whole_net','post_net'):
            if abs(coarse[key]-refined[key]) > .02: raise ValueError('Refinement gate')
    reference = fine[10]
    if abs(reference['final_load']-.32) > .0002 or abs(reference['final_kinetic']-.5) > .0002:
        raise ValueError('Two-body reflection reference')
    rows = fine[:9];candidate=rows[0]
    profitable = [r for r in rows[1:] if r['whole_net']>.02 and r['post_net']>.02]
    comparison = bool(profitable) and all(candidate[k]>max(r[k] for r in profitable)+.06 for k in ('whole_net','post_net'))
    shuffle = {k:sum(r[k] for r in rows[:6])/6 for k in ('whole_net','post_net')}
    advantage = all(candidate[k]>shuffle[k]+.06 for k in shuffle)
    renewal = all(e['functional_lost'] and e['fresh_sources'] and ids and w>.02 for e,ids,w in zip(candidate['exposure'],candidate['renewed_components'],candidate['renewal_signed_work']))
    capture_causal = all(candidate[k]>fine[11][k]+.06 for k in ('whole_net','post_net')) and sum(candidate['heat'])>1e-5
    admitted = comparison and advantage and renewal and capture_causal and candidate['whole_net']>.02 and candidate['post_net']>.02
    return dict(verified=True,natural_worlds=0,authored_layouts=9,dynamics_records=24,source_kinetic=1.5,
        signed_potential_lower_bound=-8.,intervention_bank=64.,
        reference={k:reference[k] for k in ('final_load','whole_net','post_net','final_kinetic')},
        diagnostic={k:fine[9][k] for k in ('final_load','whole_net','post_net','initial_cohesive_exergy_bound')},
        rows=[{k:r[k] for k in ('layout','final_load','whole_net','post_net','operator_positive_input','max_energy_error','renewal_signed_work','renewed_components','exposure','heat')} for r in rows],
        independent=independent,profitable_simpler_layouts=[r['layout'] for r in profitable],simpler_comparison_pass=comparison,
        full_shuffle_mean=shuffle,full_shuffle_advantage=advantage,all_role_renewal_exposed_pass=renewal,capture_causal_pass=capture_causal,
        capture_disabled={k:fine[11][k] for k in ('final_load','whole_net','post_net','heat')},
        admitted=admitted,decision='ADMISSION_PASSED_REPLICATION_REQUIRED' if admitted else 'REJECT_THIS_FROZEN_PROTOTYPE_BEFORE_WORLDS',
        empirical_physics=False,self_maintenance_demonstrated=False)

if __name__ == '__main__':
    import json
    import sys
    from pathlib import Path
    d = json.loads(Path(sys.argv[1]).read_bytes(),object_pairs_hook=unique)
    print(json.dumps(audit(d),sort_keys=True,allow_nan=False))
