"""Independent polar-gradient/RK4 interpreter; does not import producer."""
import math

def unique(pairs):
    out={}
    for k,v in pairs:
        if k in out:raise ValueError('Duplicate JSON field')
        out[k]=v
    return out

def polar_pair(a,b):
    dx,dy=a[0]-b[0],a[1]-b[1]
    s=dx*dx+dy*dy
    if s>=1 or s==0:return (0.,0.,0.,0.,0.)
    r=math.sqrt(s);phi=math.atan2(dy,dx)
    alpha,beta=a[2]-phi,b[2]-phi
    ca,sa=math.cos(alpha),math.sin(alpha)
    cb,sb=math.cos(beta),math.sin(beta)
    d=math.cos(a[2]-b[2])-3*ca*cb; w=1-s
    radial=-2*r*d*w*(1-3*s)
    tangential=3*r*w*w*(sa*cb+ca*sb)
    nx,ny=dx/r,dy/r
    fx,fy=radial*nx-tangential*ny,radial*ny+tangential*nx
    ti=s*w*w*(math.sin(a[2]-b[2])-3*sa*cb)
    tj=-s*w*w*(math.sin(a[2]-b[2])+3*ca*sb)
    return fx,fy,ti,tj,s*d*w*w

def physics(z,disabled=False):
    result=[[r[3],r[4],r[5],0.,0.,0.] for r in z];potential=0.
    for i in range(6):
        for j in range(i+1,6):
            if disabled and min(i,j)<2:continue
            fx,fy,ti,tj,v=polar_pair(z[i],z[j]);potential+=v
            mi=4. if i==5 else 1.;mj=4. if j==5 else 1.
            result[i][3]+=fx/mi;result[i][4]+=fy/mi;result[i][5]+=ti/mi
            result[j][3]-=fx/mj;result[j][4]-=fy/mj;result[j][5]+=tj/mj
    return result,potential

def energy(z):
    return sum((4. if i==5 else 1.)*sum(a*a for a in r[3:])/2 for i,r in enumerate(z))

def useful(z):return 2*(z[5][3]**2+z[5][4]**2)

def reference(arm):
    sites=[(0.,0.),(.75,.875),(-4.,0.),(-8.,0.),(-12.,0.),(1.25,0.)]
    angles=[0.,math.pi/2,math.pi,math.pi,math.pi,0.]
    if arm=='orientation_shuffle':angles[0],angles[1]=angles[1],angles[0]
    if arm=='bare':sites[0],sites[1]=(-100.,20.),(-103.,20.)
    if arm=='single':sites[1]=(-103.,20.)
    z=[[*sites[i],angles[i],.5 if i in (2,3,4) else 0.,0.,0.] for i in range(6)]
    positive=0.;pulses=[];max_error=0.;dt=1/256
    disabled=arm=='function_disabled';total=energy(z)+physics(z,disabled)[1]
    bank=64.
    for step in range(128*256+1):
        if step in (12*256,64*256):
            before=useful(z);old=energy(z);struck=[]
            for i,r in enumerate(z):
                if -3<=r[0]<=6 and .25<=r[1]<=2:
                    m=4. if i==5 else 1.
                    r[4]+=.5/m;r[5]+=.5/m;struck.append(i)
            debit=energy(z)-old;prior=positive;positive+=max(debit,0.);bank-=debit
            pulses.append(dict(struck=struck,debit=debit,load_before=before,positive_before=prior))
        max_error=max(max_error,abs(energy(z)+physics(z,disabled)[1]+bank-64-total))
        if step==128*256:break
        def shift(k,factor):return [[z[i][j]+dt*factor*k[i][j] for j in range(6)] for i in range(6)]
        k1=physics(z,disabled)[0]
        k2=physics(shift(k1,.5),disabled)[0]
        k3=physics(shift(k2,.5),disabled)[0]
        k4=physics(shift(k3,1.),disabled)[0]
        z=[[z[i][j]+dt*(k1[i][j]+2*k2[i][j]+2*k3[i][j]+k4[i][j])/6 for j in range(6)] for i in range(6)]
    final=useful(z);last=pulses[-1]
    return dict(retained_load=final,whole_net=final-positive,
                post_net=final-last['load_before']-(positive-last['positive_before']),
                positive_input=positive,final_rotation=sum((4. if i==5 else 1.)*r[5]**2/2 for i,r in enumerate(z)),
                max_energy_error=max_error,pulses=pulses)

def check_record(row):
    if row['denominator'] not in (128,256):raise ValueError('Unregistered resolution')
    if row['natural_worlds']!=0 or row['physical_fabrication_cost'] is not None or row['physical_upkeep_cost'] is not None:
        raise ValueError('Invented scope/cost')
    if row['raw_memory_or_controller'] is not False:raise ValueError('Controller')
    def close(a,b,tol=1e-9):
        if type(a) is bool or not math.isfinite(a) or abs(a-b)>tol:raise ValueError('Inconsistent numeric ledger')
    close(row['source_exergy'],.375)
    close(row['initial_potential'],0.)
    close(row['initial_spin'],0.)
    positive=sum(max(p['debit'],0.) for p in row['pulses'])
    close(row['positive_input'],positive)
    close(row['bank'],64-sum(p['debit'] for p in row['pulses']))
    close(row['retained_load'],useful(row['final']))
    close(row['whole_net'],row['retained_load']-positive)
    last=row['pulses'][-1]
    close(row['post_net'],row['retained_load']-last['load_before']-(positive-last['positive_before']))
    disabled=row['arm']=='function_disabled'
    close(row['final_translation']+row['final_rotation'],energy(row['final']))
    close(row['final_potential'],physics(row['final'],disabled)[1])
    close(row['final_translation']+row['final_rotation']+row['final_potential']+row['bank'],64.375,.003)
    pair=sum(sum(v) for v in row['pair_translation_work'].values())+sum(sum(v) for v in row['pair_spin_work'].values())
    close(pair,energy(row['final'])-.375-sum(p['debit'] for p in row['pulses']),.003)
    load_work=0.
    for key,values in row['pair_translation_work'].items():
        i,j=map(int,key.split(':'))
        if i==5:load_work+=values[0]
        if j==5:load_work+=values[1]
    close(load_work,row['retained_load']-sum(p['load_after']-p['load_before'] for p in row['pulses']),.003)
    if row['max_energy_error']>.003 or row['max_momentum_error']>1e-9 or row['max_angular_error']>1e-8:
        raise ValueError('Conservation gate')
    for k,b in enumerate(row['births']):
        if b['identity']!='assembly:'+str(k):raise ValueError('Identity reuse')
        for i,j in b['edges']:
            z=b['state'];m1=4. if i==5 else 1.;m2=4. if j==5 else 1.
            relative=m1*m2/(m1+m2)*sum((z[i][v]-z[j][v])**2 for v in (3,4))/2
            spin=(m1*z[i][5]**2+m2*z[j][5]**2)/2
            if relative+spin+polar_pair(z[i],z[j])[4]>=-1e-6+1e-12:raise ValueError('Unpaid bound birth')
    return True

def audit(data):
    if data['protocol']!='ANGULAR-TRANSFER-01-v1' or data['worlds']!=0 or len(data['records'])!=10 or data['admission'] is not False or data['replication_samples_used']!=0:raise ValueError('Protocol scope')
    arms=('candidate','orientation_shuffle','bare','single','function_disabled')
    if [(r['arm'],r['denominator']) for r in data['records']]!=[(a,d) for a in arms for d in (128,256)]:raise ValueError('Missing case')
    references={};comparison=[]
    for arm in arms:
        references[arm]=reference(arm)
        for row in [r for r in data['records'] if r['arm']==arm]:
            check_record(row)
            other=references[arm]
            for metric in ('retained_load','whole_net','post_net','positive_input','final_rotation'):
                delta=abs(row[metric]-other[metric])
                if delta>.01:raise ValueError('Independent '+arm+' '+metric+' disagreement '+str(delta))
                comparison.append(dict(arm=arm,denominator=row['denominator'],metric=metric,delta=delta))
            if [p['struck'] for p in row['pulses']]!=[p['struck'] for p in other['pulses']]:raise ValueError('Loss-mask disagreement')
            if other['max_energy_error']>.003:raise ValueError('Reference energy error')
    fine={r['arm']:r for r in data['records'] if r['denominator']==256}
    candidate=fine['candidate']
    viable=[a for a in ('bare','single') if fine[a]['whole_net']>.02 and fine[a]['post_net']>.02]
    exposed=sum(bool(p['lost']) for p in candidate['pulses'])
    failed=[]
    if not viable:failed.append('No actual simpler control profitable on BOTH measures')
    if candidate['whole_net']<=.02 or candidate['post_net']<=.02:failed.append('Candidate fails positive whole/fresh surplus')
    if any(candidate[k]<=fine[a][k]+.02 for a in viable for k in ('whole_net','post_net')):failed.append('Profitable simpler dominance or insufficient advantage')
    if any(candidate[k]<=fine['orientation_shuffle'][k]+.02 for k in ('whole_net','post_net')):failed.append('No complete-orientation-shuffle advantage')
    if any(candidate[k]<=fine['function_disabled'][k]+.02 for k in ('whole_net','post_net')):failed.append('No two-metric function-disabled advantage')
    if exposed<2:failed.append('Repeated functional damage UNDEREXPOSED')
    failed.append('All-role renewal not independently reproduced; reserved replication unused')
    # Admission additionally needs independently reproduced, all-role renewal;
    # this admission history cannot authorize a natural panel by its own output.
    return dict(decision='DO_NOT_ADMIT_THIS_AUTHORED_HISTORY',natural_worlds=0,
                candidate_whole_net=candidate['whole_net'],candidate_fresh_post_net=candidate['post_net'],
                profitable_simpler_controls=viable,
                simpler={a:{k:fine[a][k] for k in ('whole_net','post_net','retained_load')} for a in ('bare','single')},
                raw_bound_births=len(candidate['births']),functionally_destroyed_losses=exposed,
                renewal_exposure='UNDEREXPOSED' if exposed<2 else 'EXPOSED_RENEWAL_NOT_YET_INDEPENDENTLY_REPRODUCED',
                independent_comparisons=comparison,references=references,
                physical_net_work=None,physical_costs='UNKNOWN',admitted=False,
                failed_gates=failed,all_role_renewal_verified=False,
                explanation='Common force/torque dynamics measured; all-role functional renewal and reserved replication remain required.')
