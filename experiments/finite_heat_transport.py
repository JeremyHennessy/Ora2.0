"""Finite material heat transport; explicit digital law, no sink/reset/controller."""
import math
from itertools import combinations
M=(1.,1.,1.,1.,1.,4.,1.,1.)
Q=(1,-1,1,-1,1,1,0,0)
PAIRS=tuple(combinations(range(8),2))
ARMS=('candidate','shuffle','bare','positive_single','negative_single','transport_disabled','capture_disabled')
TIMES=(16,64)
HORIZON=256

def initial(arm):
    if arm not in ARMS:raise ValueError('Unregistered arm')
    x=[-1.25,0.,-4.,-48.,-160.,1.25,-8.,-96.]
    v=[0.,0.,1.,1.,1.,0.,.25,.25]
    q=list(Q)
    if arm=='shuffle':q[0],q[1]=q[1],q[0]
    if arm=='bare':x[0],x[1]=-300.,-303.
    if arm=='positive_single':x[1]=-303.
    if arm=='negative_single':x[0]=-300.
    return x,v,q

def field(x,q):
    f=[0.]*8;potential=0.;contacts=[]
    for i,j in PAIRS:
        r=x[i]-x[j]
        if abs(r)<1:
            z=1-r*r;value=q[i]*q[j]*z*z;push=4*q[i]*q[j]*r*z
            f[i]+=push;f[j]-=push;potential+=value
            contacts.append((i,j,push))
    return f,potential,contacts

def kinetic(v):return sum(m*a*a/2 for m,a in zip(M,v))

def conduct(x,h,dt,order=PAIRS,disabled=False):
    """Exact pair diffusion of temperature H/C; conserves finite owned heat."""
    flows=[]
    if disabled:return flows
    for i,j in order:
        r=x[i]-x[j]
        if abs(r)>=1:continue
        mu=M[i]*M[j]/(M[i]+M[j]);g=(1-r*r)**2
        amount=mu*(h[j]/M[j]-h[i]/M[i])*(-math.expm1(-g*(1/M[i]+1/M[j])*dt))
        h[i]+=amount;h[j]-=amount
        if amount:flows.append((i,j,amount))
    return flows

def capture(x,v,h,q,dt,order=PAIRS,disabled=False):
    work=[[0.]*8 for _ in M];heat=[[0.]*8 for _ in M]
    if disabled:return work,heat
    for i,j in order:
        r=x[i]-x[j]
        if q[i]*q[j]!=-1 or abs(r)>=1:continue
        relative=v[i]-v[j];mu=M[i]*M[j]/(M[i]+M[j]);energy=mu*relative*relative/2
        if energy<=0:continue
        room=max(0.,min(M[i]-h[i],M[j]-h[j]))
        loss=min(energy*(-math.expm1(-2*(1-r*r)**2*(1/M[i]+1/M[j])*dt)),2*room)
        if loss<=1e-16:continue
        delta=relative*(math.sqrt(max(0.,1-loss/energy))-1)
        oldi=M[i]*v[i]**2/2;oldj=M[j]*v[j]**2/2
        v[i]+=M[j]*delta/(M[i]+M[j]);v[j]-=M[i]*delta/(M[i]+M[j])
        wi=M[i]*v[i]**2/2-oldi;wj=M[j]*v[j]**2/2-oldj
        actual=max(0.,-wi-wj);h[i]+=actual/2;h[j]+=actual/2
        work[i][j]+=wi;work[j][i]+=wj;heat[i][j]+=actual
    return work,heat

def groups(x,v,q):
    parents=list(range(8));edges=[]
    def root(i):
        while parents[i]!=i:i=parents[i]
        return i
    for i,j in PAIRS:
        r=x[i]-x[j]
        if abs(r)<1 and M[i]*M[j]/(M[i]+M[j])*(v[i]-v[j])**2/2+q[i]*q[j]*(1-r*r)**2 < -1e-6:
            parents[root(i)]=root(j);edges.append((i,j))
    connected={}
    for i in range(8):connected.setdefault(root(i),[]).append(i)
    return [tuple(g) for g in connected.values() if len(g)>1],edges

def simulate(arm,denominator):
    if denominator not in (128,256):raise ValueError('Unregistered resolution')
    x,v,q=initial(arm);h=[0.]*8;bank=64.;positive=0.;dt=1/denominator
    initial_state=dict(x=x.copy(),v=v.copy(),charge=q.copy(),heat=h.copy())
    total=kinetic(v)+bank;initial_momentum=sum(m*a for m,a in zip(M,v))
    expected_momentum=initial_momentum;max_energy=max_momentum=0.
    first={};ancestry=[{str(i)} for i in range(8)];ids={};births=[];pulses=[];traces=[]
    pair_work=[[0.]*8 for _ in M];capture_work=[[0.]*8 for _ in M]
    deposition=[[0.]*8 for _ in M];heat_flow=[[0.]*8 for _ in M]
    def register(t):
        nonlocal ids
        connected,edges=groups(x,v,q);fresh={}
        for members in connected:
            key=(members,tuple(e for e in edges if e[0] in members and e[1] in members))
            if key in ids:item=ids[key]
            else:
                item=dict(id=len(births),born=t,members=list(members),edges=[list(e) for e in key[1]],
                          x=x.copy(),v=v.copy(),heat=h.copy(),signed_load_work=0.,exported_heat=0.)
                births.append(item)
            fresh[key]=item
        ids=fresh
        return connected,edges
    def note(i,j,t):
        for k in (i,j):
            if k in (2,3,4):first.setdefault(k,t)
        union=ancestry[i]|ancestry[j];ancestry[i]=union.copy();ancestry[j]=union.copy()
    def thermal(t,order):
        flows=conduct(x,h,dt/2,order,arm=='transport_disabled')
        for i,j,a in flows:
            heat_flow[i][j]+=a;heat_flow[j][i]-=a;note(i,j,t)
            for item in ids.values():
                members=item['members']
                if i in members and j not in members:item['exported_heat']-=a
                if j in members and i not in members:item['exported_heat']+=a
        w,p=capture(x,v,h,q,dt/2,order,arm=='capture_disabled')
        for i,j in PAIRS:
            capture_work[i][j]+=w[i][j];capture_work[j][i]+=w[j][i];deposition[i][j]+=p[i][j]
            if p[i][j]:note(i,j,t)
            if j==5:
                for item in ids.values():
                    if i in item['members'] and 5 in item['members']:item['signed_load_work']+=w[5][i]
    register(0.)
    for step in range(HORIZON*denominator+1):
        t=step/denominator
        if t in TIMES:
            _,before_edges=groups(x,v,q)
            functioning=[dict(id=b['id'],members=b['members'].copy(),work=b['signed_load_work'],exported_heat=b['exported_heat'])
                         for b in ids.values() if 5 in b['members'] and b['signed_load_work']>.02 and b['exported_heat']>.01]
            before=2*v[5]**2;old=kinetic(v);oldp=positive;struck=[]
            # Blind fixed region and raw mass class; no observed-function target.
            for i in range(8):
                if M[i]==1 and -3<=x[i]<=3:
                    impulse=-1 if x[i]<0 else 1;v[i]+=impulse;expected_momentum+=impulse
                    ancestry[i].add('damage:'+str(int(t)));struck.append(i)
            debit=kinetic(v)-old;bank-=debit;positive+=max(0.,debit)
            if bank<0:raise ValueError('Finite bank exhausted')
            _,after_edges=groups(x,v,q)
            lost=[b for b in functioning if any(i in struck for i in b['members']) and
                  not any(i in b['members'] and j in b['members'] for i,j in after_edges)]
            pulses.append(dict(time=t,struck=struck,debit=debit,load_before=before,positive_before=oldp,
                               functioning_before=functioning,lost=lost,virgin_sources=[i for i in (2,3,4) if i not in first],
                               before_edges=[list(e) for e in before_edges],after_edges=[list(e) for e in after_edges]))
            register(t)
        f,potential,contacts=field(x,q)
        max_energy=max(max_energy,abs(kinetic(v)+potential+sum(h)+bank-total))
        max_momentum=max(max_momentum,abs(sum(m*a for m,a in zip(M,v))-expected_momentum))
        if any(a < -1e-10 or a>m+1e-10 for a,m in zip(h,M)):raise ValueError('Heat capacity')
        if step%denominator==0:traces.append(dict(time=t,x=x.copy(),v=v.copy(),heat=h.copy(),potential=potential,bank=bank))
        if step==HORIZON*denominator:break
        for i,j,force in contacts:
            if force:note(i,j,t)
        thermal(t,PAIRS)
        old=x.copy();half=[v[i]+dt*f[i]/(2*M[i]) for i in range(8)]
        x=[x[i]+dt*half[i] for i in range(8)]
        nf,_,nc=field(x,q);v=[half[i]+dt*nf[i]/(2*M[i]) for i in range(8)]
        thermal(t+dt,tuple(reversed(PAIRS)))
        for i,j,force in nc:
            if force:note(i,j,t+dt)
        f0={(i,j):force for i,j,force in contacts};f1={(i,j):force for i,j,force in nc}
        for i,j in PAIRS:
            avg=(f0.get((i,j),0.)+f1.get((i,j),0.))/2
            wi=avg*(x[i]-old[i]);wj=-avg*(x[j]-old[j])
            pair_work[i][j]+=wi;pair_work[j][i]+=wj
            if j==5:
                for item in ids.values():
                    if i in item['members'] and 5 in item['members']:item['signed_load_work']+=wj
        register(t+dt)
    last=pulses[-1];load=2*v[5]**2
    return dict(arm=arm,denominator=denominator,initial=initial_state,final_x=x,final_v=v,heat=h,bank=bank,
                source_kinetic=1.5,carrier_transport_capital=.0625,total_initial_energy=65.5625,
                final_load=load,whole_net=load-positive,post_net=load-last['load_before']-(positive-last['positive_before']),
                operator_positive_input=positive,final_potential=potential,final_kinetic=kinetic(v),
                max_energy_error=max_energy,max_momentum_error=max_momentum,
                pair_work=pair_work,capture_work=capture_work,heat_deposition=deposition,heat_transport=heat_flow,
                load_ancestry=sorted(ancestry[5]),source_first_contact=first,births=births,pulses=pulses,traces=traces,
                physical_cold_preparation_cost=None,physical_fabrication_cost=None,physical_net_work=None,natural_worlds=0)

def panel():
    return dict(protocol='FINITE-HEAT-TRANSPORT-01-v1',natural_worlds=0,reserved_samples_used=0,
                records=[simulate(a,d) for a in ARMS for d in (128,256)])
