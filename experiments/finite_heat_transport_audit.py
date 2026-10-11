"""Separate COM-temperature/RK4 interpreter; imports no producer."""
import math
from itertools import combinations
MASSES=(1.,1.,1.,1.,1.,4.,1.,1.)
PAIRS=tuple(combinations(range(8),2))
ARMS=('candidate','shuffle','bare','positive_single','negative_single','transport_disabled','capture_disabled')
def unique(pairs):
    out={}
    for k,v in pairs:
        if k in out:raise ValueError('Duplicate JSON field')
        out[k]=v
    return out
def force(x,q):
    a=[0.]*8;potential=0.
    for i,j in PAIRS:
        gap=x[j]-x[i]
        if abs(gap)<1:
            c=q[i]*q[j];well=1-gap*gap
            push=-4*c*gap*well
            a[i]+=push/MASSES[i];a[j]-=push/MASSES[j];potential+=c*well*well
    return a,potential
def ke(v):return sum(m*w*w/2 for m,w in zip(MASSES,v))
def thermal(x,v,h,q,dt,order,off,cap_off):
    if not off:
        for i,j in order:
            distance=x[i]-x[j]
            if abs(distance)>=1:continue
            ci,cj=MASSES[i],MASSES[j];common=(h[i]+h[j])/(ci+cj)
            retain=math.exp(-(1-distance*distance)**2*(1/ci+1/cj)*dt)
            old=h[i];h[i]=ci*common+(old-ci*common)*retain;h[j]-=h[i]-old
    if cap_off:return
    for i,j in order:
        distance=x[i]-x[j]
        if q[i]*q[j]!=-1 or abs(distance)>=1:continue
        mi,mj=MASSES[i],MASSES[j];center=(mi*v[i]+mj*v[j])/(mi+mj)
        relative=v[i]-v[j];reduced=mi*mj/(mi+mj);old=reduced*relative*relative/2
        if old<=0:continue
        target=old*(-math.expm1(-2*(1-distance*distance)**2*(1/mi+1/mj)*dt))
        loss=min(target,2*max(0.,min(mi-h[i],mj-h[j])))
        if loss<=1e-16:continue
        newrelative=math.copysign(math.sqrt(max(0.,2*(old-loss)/reduced)),relative)
        before=mi*v[i]*v[i]/2+mj*v[j]*v[j]/2
        v[i]=center+mj*newrelative/(mi+mj);v[j]=center-mi*newrelative/(mi+mj)
        actual=max(0.,before-mi*v[i]*v[i]/2-mj*v[j]*v[j]/2)
        h[i]+=actual/2;h[j]+=actual/2
def reference(arm):
    x=[-1.25,0.,-4.,-48.,-160.,1.25,-8.,-96.];v=[0.,0.,1.,1.,1.,0.,.25,.25]
    q=[1,-1,1,-1,1,1,0,0]
    if arm=='shuffle':q[0],q[1]=q[1],q[0]
    if arm=='bare':x[0],x[1]=-300.,-303.
    if arm=='positive_single':x[1]=-303.
    if arm=='negative_single':x[0]=-300.
    h=[0.]*8;bank=64.;positive=0.;pulses=[];dt=1/256;maximum=0.
    for step in range(256*256+1):
        if step in (16*256,64*256):
            before=2*v[5]**2;prior=positive;old=ke(v);struck=[]
            for i in range(8):
                if MASSES[i]==1 and -3<=x[i]<=3:
                    v[i]+=(-1 if x[i]<0 else 1);struck.append(i)
            debit=ke(v)-old;bank-=debit;positive+=max(0.,debit)
            pulses.append(dict(struck=struck,debit=debit,load_before=before,positive_before=prior))
        maximum=max(maximum,abs(ke(v)+force(x,q)[1]+sum(h)+bank-65.5625))
        if step==256*256:break
        thermal(x,v,h,q,dt/2,PAIRS,arm=='transport_disabled',arm=='capture_disabled')
        ax=force(x,q)[0]
        k1x=v.copy();k1v=ax
        k2x=[v[i]+dt*k1v[i]/2 for i in range(8)]
        k2v=force([x[i]+dt*k1x[i]/2 for i in range(8)],q)[0]
        k3x=[v[i]+dt*k2v[i]/2 for i in range(8)]
        k3v=force([x[i]+dt*k2x[i]/2 for i in range(8)],q)[0]
        k4x=[v[i]+dt*k3v[i] for i in range(8)]
        k4v=force([x[i]+dt*k3x[i] for i in range(8)],q)[0]
        x=[x[i]+dt*(k1x[i]+2*k2x[i]+2*k3x[i]+k4x[i])/6 for i in range(8)]
        v=[v[i]+dt*(k1v[i]+2*k2v[i]+2*k3v[i]+k4v[i])/6 for i in range(8)]
        thermal(x,v,h,q,dt/2,tuple(reversed(PAIRS)),arm=='transport_disabled',arm=='capture_disabled')
    load=2*v[5]**2;last=pulses[-1]
    return dict(final_load=load,whole_net=load-positive,
                post_net=load-last['load_before']-(positive-last['positive_before']),
                operator_positive_input=positive,heat=h,bank=bank,max_energy_error=maximum,pulses=pulses)
def check_record(r):
    def close(a,b,tol=1e-9):
        if type(a) is bool or not math.isfinite(a) or abs(a-b)>tol:raise ValueError('Numeric ledger')
    if r['natural_worlds']!=0 or any(r[k] is not None for k in ('physical_cold_preparation_cost','physical_fabrication_cost','physical_net_work')):raise ValueError('Invented price or scope')
    close(r['source_kinetic'],1.5);close(r['carrier_transport_capital'],.0625);close(r['total_initial_energy'],65.5625)
    close(ke(r['initial']['v']),1.5625)
    close(force(r['initial']['x'],r['initial']['charge'])[1],0.)
    close(r['final_kinetic'],ke(r['final_v']))
    close(r['final_potential'],force(r['final_x'],r['initial']['charge'])[1])
    positive=sum(max(0.,p['debit']) for p in r['pulses']);last=r['pulses'][-1]
    close(r['operator_positive_input'],positive);close(r['bank'],64-sum(p['debit'] for p in r['pulses']))
    close(r['final_load'],2*r['final_v'][5]**2)
    close(r['whole_net'],r['final_load']-positive)
    close(r['post_net'],r['final_load']-last['load_before']-(positive-last['positive_before']))
    if r['max_energy_error']>.004 or r['max_momentum_error']>1e-9:raise ValueError('Conservation gate')
    close(r['final_kinetic']+r['final_potential']+sum(r['heat'])+r['bank'],65.5625,.004)
    for i,(h,m) in enumerate(zip(r['heat'],MASSES)):
        if h<-1e-10 or h>m+1e-10:raise ValueError('Finite capacity')
        deposited=sum(r['heat_deposition'][i])/2+sum(row[i] for row in r['heat_deposition'])/2
        close(h,deposited+sum(r['heat_transport'][i]),1e-8)
        for j in range(8):close(r['heat_transport'][i][j],-r['heat_transport'][j][i],1e-12)
    close(sum(r['heat']),sum(sum(row) for row in r['heat_deposition']),1e-8)
    mechanical=sum(sum(row) for row in r['pair_work'])+sum(sum(row) for row in r['capture_work'])
    close(mechanical,r['final_kinetic']-1.5625-sum(p['debit'] for p in r['pulses']),.004)
    for n,b in enumerate(r['births']):
        if b['id']!=n:raise ValueError('Reused assembly identity')
        for i,j in b['edges']:
            gap=b['x'][i]-b['x'][j];qi,qj=r['initial']['charge'][i],r['initial']['charge'][j]
            binding=MASSES[i]*MASSES[j]/(MASSES[i]+MASSES[j])*(b['v'][i]-b['v'][j])**2/2+qi*qj*(1-gap*gap)**2
            if abs(gap)>=1 or binding>=-1e-6+1e-12:raise ValueError('Unpaid birth')
    return True
def audit(data):
    if data['protocol']!='FINITE-HEAT-TRANSPORT-01-v1' or data['natural_worlds']!=0 or data['reserved_samples_used']!=0:raise ValueError('Scope')
    rows=data['records']
    if [(r['arm'],r['denominator']) for r in rows]!=[(a,d) for a in ARMS for d in (128,256)]:raise ValueError('Missing authored history')
    refs={};comparisons=[]
    for arm in ARMS:
        other=reference(arm);refs[arm]=other
        if other['max_energy_error']>.0005:raise ValueError('Independent energy gate')
        for r in (r for r in rows if r['arm']==arm):
            check_record(r)
            for k in ('final_load','whole_net','post_net','operator_positive_input'):
                delta=abs(r[k]-other[k]);comparisons.append(dict(arm=arm,denominator=r['denominator'],metric=k,delta=delta))
                if delta>.03:raise ValueError('Independent '+arm+' '+k+' discrepancy '+str(delta))
            if any(abs(a-b)>.03 for a,b in zip(r['heat'],other['heat'])):raise ValueError('Independent heat disagreement')
            if [p['struck'] for p in r['pulses']]!=[p['struck'] for p in other['pulses']]:raise ValueError('Loss exposure disagreement')
    fine={r['arm']:r for r in rows if r['denominator']==256};c=fine['candidate']
    viable=[a for a in ('bare','positive_single','negative_single') if fine[a]['whole_net']>.04 and fine[a]['post_net']>.04]
    exposure=sum(bool(p['lost']) for p in c['pulses'])
    failed=[]
    if not viable:failed.append('No actual whole/fresh profitable simpler control')
    if c['whole_net']<=.04 or c['post_net']<=.04:failed.append('Candidate whole/fresh surplus fails')
    if any(c[k]<=fine[a][k]+.08 for a in viable for k in ('whole_net','post_net')):failed.append('No simpler-control advantage')
    shuffle={k:(c[k]+fine['shuffle'][k])/2 for k in ('whole_net','post_net')}
    if any(c[k]<=shuffle[k]+.08 for k in shuffle):failed.append('No complete two-assignment shuffle advantage')
    if any(c[k]<=fine['transport_disabled'][k]+.08 for k in ('whole_net','post_net')):failed.append('No whole/fresh heat-transport causal advantage')
    if exposure<2:failed.append('Repeated full functioning damage UNDEREXPOSED')
    failed.append('All-role renewal/independent reserved reproduction not established')
    return dict(verified=True,decision='DO_NOT_ADMIT_THIS_FROZEN_HISTORY',admitted=False,natural_worlds=0,
                records=len(rows),candidate_whole_net=c['whole_net'],candidate_fresh_post_net=c['post_net'],
                profitable_simpler_controls=viable,raw_bound_births=len(c['births']),
                renewal_exposure='UNDEREXPOSED' if exposure<2 else 'EXPOSED_BUT_RENEWAL_UNVERIFIED',
                all_role_renewal_verified=False,physical_net_work=None,physical_prices='UNKNOWN',
                rows={a:{k:r[k] for k in ('whole_net','post_net','final_load','heat','source_first_contact','pulses')} for a,r in fine.items()},
                complete_shuffle_mean=shuffle,independent_references=refs,independent_comparisons=comparisons,failed_gates=failed)
