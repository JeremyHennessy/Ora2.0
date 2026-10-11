"""Finite authored internal-mode physics; no policy or external API."""
from decimal import Decimal as D, getcontext
import json
getcontext().prec=80
ARMS=('candidate','direct','mode_disabled','formation_disabled','shuffle_identity','shuffle_exchange')
NAMES=('a0','a1','s0','s1','s2','load')
RANK={n:i for i,n in enumerate(NAMES)}
EPS=D('1e-60')
def mass(p):return D(sum(4 if n=='load' else 1 for n in p['members']))
def kinetic(p):return mass(p)*p['v']*p['v']/2
def render(x):return str(x)
class World:
    def __init__(self,arm):
        if arm not in ARMS:raise ValueError('Unknown arm')
        self.arm=arm; self.t=D(0);self.heat=D(0);self.bill=D(0);self.compress=D(0)
        self.serial=0;self.bond=0;self.first={};self.events=[];self.lost=False;self.rebuilt=[];self.rebuilt_work=D(0)
        entries=[('a0',-1,1),('a1',1,-1),('s0',-16,2),('s1',-64,2),('s2',-128,2),('load',16,0)]
        if arm=='direct':entries[:2]=[('a0',-1000,1),('a1',-1100,-1)]
        if arm=='shuffle_exchange':entries[:2]=[('a0',-1,-1),('a1',1,1)]
        self.parts=[dict(id='raw:'+n,members=[n],x=D(x),v=D(v),bond=None,mode=0) for n,x,v in entries]
    def order(self):self.parts.sort(key=lambda p:(p['x'],min(RANK[n] for n in p['members'])))
    def load(self):return kinetic(next(p for p in self.parts if p['members']==['load']))
    def snapshot(self):
        self.order()
        return dict(time=render(self.t),heat=render(self.heat),formation=render(self.bill),compression=render(self.compress),next_object=self.serial,next_bond=self.bond,first={n:render(t) for n,t in sorted(self.first.items())},parts=[dict(id=p['id'],members=p['members'],x=render(p['x']),v=render(p['v']),bond=p['bond'],mode=p['mode']) for p in self.parts])
    def identity(self):
        n='object:'+str(self.serial);self.serial+=1;return n
    def contact(self):
        self.order(); pairs=[]
        for i,(a,b) in enumerate(zip(self.parts,self.parts[1:])):
            if a['v']>b['v']:pairs.append(((b['x']-a['x'])/(a['v']-b['v']),i))
        if not pairs:return None,None
        first=min(t for t,i in pairs)
        return next((max(t,D(0)),i) for t,i in pairs if abs(t-first)<=EPS)
    def check(self):
        assert sorted(n for p in self.parts for n in p['members'])==sorted(NAMES)
        assert abs(sum(mass(p)*p['v'] for p in self.parts)-6)<=EPS
        assert abs(sum(kinetic(p)+p['mode'] for p in self.parts)+self.heat-7)<=EPS
        assert self.heat>=-EPS and all(p['mode'] in (0,1) and (p['bond'] is not None or p['mode']==0) for p in self.parts)
    def step(self,kind,dt,index=None):
        before=self.snapshot(); old_load=self.load();old_bill=self.bill;old_compress=self.compress;old_heat=self.heat
        for p in self.parts:p['x']+=p['v']*dt
        self.t+=dt;parents=[];newborn=None;mode_bond=None
        if kind=='collision':
            a,b=self.parts[index:index+2];assert abs(a['x']-b['x'])<=EPS and a['v']>b['v'];parents=[a['id'],b['id']]
            for n in a['members']+b['members']:
                if n.startswith('s'):self.first.setdefault(n,self.t)
            m,n,u,v=mass(a),mass(b),a['v'],b['v'];cm=(m*u+n*v)/(m+n);r=m*n*(u-v)**2/(2*(m+n))
            if self.arm!='formation_disabled' and a['bond'] is None and b['bond'] is None and 'load' not in a['members']+b['members'] and r>=1:
                mode_bond=self.bond;self.bond+=1;newborn=self.identity()
                c=dict(id=newborn,members=sorted(a['members']+b['members'],key=RANK.get),x=a['x'],v=cm,bond=mode_bond,mode=1)
                self.parts[index:index+2]=[c];self.bill+=r;self.heat+=r-1;channel='form'
                if self.lost and {'a0','a1'}<=set(c['members']):self.rebuilt.append(newborn)
            else:
                modes=sorted((p for p in (a,b) if p['bond'] is not None),key=lambda p:p['bond'])
                channel='elastic';rp=r
                if modes and self.arm!='mode_disabled':
                    p=modes[0];mode_bond=p['bond']
                    if p['mode']==1:p['mode']=0;rp=r+1;channel='release'
                    elif r>=1:p['mode']=1;rp=r-1;self.compress+=1;channel='compress'
                s=(2*(m+n)*rp/(m*n)).sqrt();a['v']=cm-n*s/(m+n);b['v']=cm+m*s/(m+n)
                if self.lost and 'load' in a['members']+b['members']:
                    partner=b if 'load' in a['members'] else a
                    if partner['id'] in self.rebuilt:self.rebuilt_work+=self.load()-old_load
        elif kind=='damage':
            self.loss_load=old_load;self.loss_cost=self.bill+self.compress
            self.loss_bonds=sum(p['bond'] is not None for p in self.parts);self.unused=sorted(set(('s0','s1','s2'))-set(self.first))
            parts=[]
            for p in self.parts:
                if p['bond'] is None:parts.append(p)
                else:
                    parents.append(p['id']);self.heat+=p['mode']
                    for n in p['members']:parts.append(dict(id=self.identity(),members=[n],x=p['x'],v=p['v'],bond=None,mode=0))
            self.parts=parts;self.lost=True;channel='destroy_all'
        elif kind=='finish':channel='horizon'
        else:raise ValueError('Unknown event')
        self.check()
        self.events.append(dict(kind=kind,dt=render(dt),channel=channel,parents=parents,newborn=newborn,mode_bond=mode_bond,formation_debit=render(self.bill-old_bill),compression_debit=render(self.compress-old_compress),heat_delta=render(self.heat-old_heat),load_work=render(self.load()-old_load),before=before,after=self.snapshot()))
    def run(self):
        for _ in range(514):
            dt,index=self.contact();boundary=D(64 if not self.lost else 192)
            if dt is None or self.t+dt>=boundary:
                self.step('damage' if not self.lost else 'finish',boundary-self.t)
                if boundary==192:break
            else:
                if sum(e['kind']=='collision' for e in self.events)>=512:raise RuntimeError('Contact cap')
                if dt<0:raise RuntimeError('Negative time')
                self.step('collision',dt,index)
        else:raise RuntimeError('Event cap')
        whole=self.load()-self.bill-self.compress;post=self.load()-self.loss_load-(self.bill+self.compress-self.loss_cost)
        score=dict(load=render(self.load()),formation=render(self.bill),compression=render(self.compress),whole_margin=render(whole),post_margin=render(post),post_load=render(self.load()-self.loss_load),loss_bonds=self.loss_bonds,unused=self.unused,rebuilt=self.rebuilt,rebuilt_work=render(self.rebuilt_work),success=bool(self.loss_bonds and self.unused and self.rebuilt and self.rebuilt_work>0 and whole>0 and post>0))
        return dict(arm=self.arm,initial=self.events[0]['before'],events=self.events,score=score)
def fixtures():return dict(schema='mode-converter01-v1',scope='Six authored internal-mode histories',natural_worlds=0,records=[World(a).run() for a in ARMS])
if __name__=='__main__':print(json.dumps(fixtures(),sort_keys=True,separators=(',',':')))
