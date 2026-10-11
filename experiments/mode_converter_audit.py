"""Independent momentum-quadratic interpreter; no producer import."""
from decimal import Decimal as D,getcontext,InvalidOperation
import json,sys
getcontext().prec=80
NAMES=('a0','a1','s0','s1','s2','load')
ARMS=('candidate','direct','mode_disabled','formation_disabled','shuffle_identity','shuffle_exchange')
EPS=D('1e-60');TOL=D('1e-55')
def unique(pairs):
    d={}
    for k,v in pairs:
        if k in d:raise ValueError('Duplicate evidence name')
        d[k]=v
    return d
def equal(a,b):
    if type(a) is not type(b):return False
    if type(a) is dict:return set(a)==set(b) and all(equal(a[n],b[n]) for n in a)
    if type(a) is list:return len(a)==len(b) and all(equal(x,y) for x,y in zip(a,b))
    if type(a) is str:
        try:
            x,y=D(a),D(b)
            return x.is_finite() and y.is_finite() and abs(x-y)<=TOL
        except InvalidOperation:return a==b
    return a==b
def m(p):return D(sum(4 if n=='load' else 1 for n in p[1]))
def k(p):return m(p)*p[3]**2/2
def order(ps):return sorted(ps,key=lambda p:(p[2],min(NAMES.index(n) for n in p[1])))
def view(t,h,c,r,serial,bond,first,ps):
    return dict(time=str(t),heat=str(h),formation=str(c),compression=str(r),next_object=serial,next_bond=bond,first={n:str(first[n]) for n in sorted(first)},parts=[dict(id=p[0],members=list(p[1]),x=str(p[2]),v=str(p[3]),bond=p[4],mode=p[5]) for p in order(ps)])
def audit_record(record,arm):
    if set(record)!={'arm','initial','events','score'} or record['arm']!=arm:raise ValueError('Arm/schema')
    entries=[('a0',-1,1),('a1',1,-1),('s0',-16,2),('s1',-64,2),('s2',-128,2),('load',16,0)]
    if arm=='direct':entries[:2]=[('a0',-1000,1),('a1',-1100,-1)]
    if arm=='shuffle_exchange':entries[:2]=[('a0',-1,-1),('a1',1,1)]
    ps=[('raw:'+n,(n,),D(x),D(v),None,0) for n,x,v in entries]
    t=h=c=r=D(0);serial=bond=0;first={};lost=False;finished=False;rebuilt=[];work=D(0);contacts=0
    if not equal(view(t,h,c,r,serial,bond,first,ps),record['initial']):raise ValueError('Raw initial state')
    if type(record['events']) is not list or len(record['events'])>514:raise ValueError('Event cap')
    for observed in record['events']:
        if finished:raise ValueError('Event after horizon')
        ps=order(ps);before=view(t,h,c,r,serial,bond,first,ps)
        options=[((b[2]-a[2])/(a[3]-b[3]),i) for i,(a,b) in enumerate(zip(ps,ps[1:])) if a[3]>b[3]]
        boundary=D(192 if lost else 64)
        if options:
            least=min(q for q,i in options);dt,i=next((max(q,D(0)),i) for q,i in options if abs(q-least)<=EPS)
            if least < -EPS:raise ValueError('Backward contact')
        else:dt=i=None
        if dt is None or t+dt>=boundary:kind='finish' if lost else 'damage';dt=boundary-t
        else:kind='collision'
        old_c,old_r,old_h=c,r,h;load_before=next(k(p) for p in ps if p[1]==('load',))
        ps=[(p[0],p[1],p[2]+p[3]*dt,p[3],p[4],p[5]) for p in ps];t+=dt
        parents=[];newborn=None;mode_bond=None
        if kind=='collision':
            contacts+=1
            if contacts>512:raise ValueError('Contact cap')
            a,b=ps[i:i+2];parents=[a[0],b[0]]
            if abs(a[2]-b[2])>EPS or a[3]<=b[3]:raise ValueError('Invalid collision')
            for name in a[1]+b[1]:
                if name.startswith('s') and name not in first:first[name]=t
            ma,mb=m(a),m(b);p=ma*a[3]+mb*b[3];total=ma+mb
            rel=k(a)+k(b)-p*p/(2*total)
            if arm!='formation_disabled' and a[4] is None and b[4] is None and 'load' not in a[1]+b[1] and rel>=1:
                newborn='object:'+str(serial);serial+=1;mode_bond=bond;bond+=1
                child=(newborn,tuple(sorted(a[1]+b[1],key=NAMES.index)),a[2],p/total,mode_bond,1)
                ps[i:i+2]=[child];c+=rel;h+=rel-1;channel='form'
                if lost and 'a0' in child[1] and 'a1' in child[1]:rebuilt.append(newborn)
            else:
                channel='elastic';rp=rel
                available=[(z[4],j,z) for j,z in enumerate((a,b)) if z[4] is not None]
                if available and arm!='mode_disabled':
                    mode_bond,j,z=min(available);new_mode=z[5]
                    if z[5]:rp+=1;new_mode=0;channel='release'
                    elif rel>=1:rp-=1;new_mode=1;r+=1;channel='compress'
                    if j==0:a=(a[0],a[1],a[2],a[3],a[4],new_mode)
                    else:b=(b[0],b[1],b[2],b[3],b[4],new_mode)
                # Independent elimination of each momentum-constrained quadratic.
                va=p/total-(2*mb*rp/(ma*total)).sqrt()
                vb=p/total+(2*ma*rp/(mb*total)).sqrt()
                a=(a[0],a[1],a[2],va,a[4],a[5]);b=(b[0],b[1],b[2],vb,b[4],b[5]);ps[i:i+2]=[a,b]
                if lost and 'load' in a[1]+b[1]:
                    partner=b if 'load' in a[1] else a
                    if partner[0] in rebuilt:work+=next(k(z) for z in ps if z[1]==('load',))-load_before
        elif kind=='damage':
            loss_c=c+r;loss_k=load_before;loss_bonds=sum(p[4] is not None for p in ps);unused=sorted(n for n in ('s0','s1','s2') if n not in first)
            dissolved=[]
            for z in ps:
                if z[4] is None:dissolved.append(z)
                else:
                    parents.append(z[0]);h+=z[5]
                    for name in z[1]:
                        dissolved.append(('object:'+str(serial),(name,),z[2],z[3],None,0));serial+=1
            ps=dissolved;lost=True;channel='destroy_all'
        else:finished=True;channel='horizon'
        if sorted(n for z in ps for n in z[1])!=sorted(NAMES) or abs(sum(m(z)*z[3] for z in ps)-6)>EPS or abs(sum(k(z)+z[5] for z in ps)+h-7)>EPS or h < -EPS:raise ValueError('Conservation')
        load_after=next(k(z) for z in ps if z[1]==('load',))
        expected=dict(kind=kind,dt=str(dt),channel=channel,parents=parents,newborn=newborn,mode_bond=mode_bond,formation_debit=str(c-old_c),compression_debit=str(r-old_r),heat_delta=str(h-old_h),load_work=str(load_after-load_before),before=before,after=view(t,h,c,r,serial,bond,first,ps))
        if not equal(expected,observed):raise ValueError(json.dumps(dict(arm=arm,contact=contacts,expected=expected,observed=observed),sort_keys=True))
    if not finished or not lost:raise ValueError('Incomplete history')
    load=next(k(z) for z in ps if z[1]==('load',));whole=load-c-r;post=load-loss_k-(c+r-loss_c)
    score=dict(load=str(load),formation=str(c),compression=str(r),whole_margin=str(whole),post_margin=str(post),post_load=str(load-loss_k),loss_bonds=loss_bonds,unused=unused,rebuilt=rebuilt,rebuilt_work=str(work),success=bool(loss_bonds and unused and rebuilt and work>0 and whole>0 and post>0))
    if not equal(score,record['score']):raise ValueError('False endpoint')
    return dict(arm=arm,contacts=contacts,heat=str(h),score=score,channels={n:sum(e['channel']==n for e in record['events']) for n in ('form','compress','release','elastic')})
def audit(receipt):
    if not equal({k:v for k,v in receipt.items() if k!='records'},dict(schema='mode-converter01-v1',scope='Six authored internal-mode histories',natural_worlds=0)) or set(receipt)!={'schema','scope','natural_worlds','records'}:raise ValueError('Receipt scope')
    if type(receipt['records']) is not list or len(receipt['records'])!=6:raise ValueError('Six records')
    rows=[audit_record(r,a) for r,a in zip(receipt['records'],ARMS)];scores={r['arm']:r['score'] for r in rows}
    left,right=receipt['records'][0],receipt['records'][4]
    if left['events']!=right['events'] or left['initial']!=right['initial'] or left['score']!=right['score']:raise ValueError('Identity alias differs')
    candidate,direct,shuffle=(scores[n] for n in ('candidate','direct','shuffle_exchange'))
    profitable=all(D(direct[n])>0 for n in ('whole_margin','post_margin'))
    advantage=all(D(candidate[n])>D(direct[n]) and D(candidate[n])>D(shuffle[n]) for n in ('whole_margin','post_margin'))
    return dict(verified=True,records=rows,direct_profitable=profitable,candidate_advantage=advantage,admitted=bool(candidate['success'] and profitable and advantage),natural_worlds=0,scope='Declared digital-law fixture; no life claim')
if __name__=='__main__':print(json.dumps(audit(json.load(sys.stdin,object_pairs_hook=unique)),sort_keys=True,indent=2))
