"""General prospective packed access; pure transitions, no World/task admission."""
import json
VERSION='CONTEXT90-PACKED-ACCESS-v2'
CAPACITIES=(2,4,8)
NEW_OPS=(22,23,24,25)
PRICES={22:2,23:3,24:1,25:1}

def integer(x,lo,hi):
 if type(x) is not int or not lo<=x<=hi:raise ValueError('integer bounds')
 return x

def validate_instruction(t,n):
 integer(n,1,32)
 if type(t) is not list or len(t)!=3:raise ValueError('triple')
 op,a,b=t
 integer(op,22,25)
 if op in (22,23):integer(a,0,1);integer(b,0,1)
 elif op==24:integer(a,0,1);integer(b,0,15)
 else:integer(a,0,7);integer(b,0,n-1)
 return op,a,b

def validate_state(s,n):
 if type(s) is not dict or set(s)!={'memory','registers','pc','energy'}:raise ValueError('state shape')
 m,r=s['memory'],s['registers']
 if type(m) is not list or len(m) not in CAPACITIES or type(r) is not list or len(r)!=2:raise ValueError('physical state')
 for v in m+r:integer(v,0,15)
 integer(s['pc'],0,n-1);integer(s['energy'],1,224)

def transition(s,t,n):
 """Fresh state/event; caller owns global heat/removal/tick/lease integration."""
 op,a,b=validate_instruction(t,n);validate_state(s,n)
 after=json.loads(json.dumps(s));price=PRICES[op];paid=min(s['energy'],price)
 after['energy']-=paid
 event={'version':VERSION,'decoded':t[:],'cpu':1,'logic_fee':paid-1,'actor_cost':paid,'required':price,'completed':paid==price,'read':None,'write':None}
 if paid<price:return after,event
 after['pc']=(s['pc']+1)%n;r=after['registers'];m=after['memory'];q=len(m)
 if op==22:
  slot=r[b]%(2*q);cell=slot//2;offset=2*(slot%2);value=(m[cell]>>offset)&3
  event['read']={'slot':slot,'cell':cell,'offset':offset,'word':m[cell],'value':value};r[a]=value
 elif op==23:
  slot=r[a]%(2*q);cell=slot//2;offset=2*(slot%2);old=m[cell];value=r[b]&3
  m[cell]=(old&(~(3<<offset)&15))|(value<<offset)
  event['write']={'slot':slot,'cell':cell,'offset':offset,'before':old,'value':value,'after':m[cell]}
 elif op==24:r[a]^=b
 else:
  if (r[a%2]>>(a//2))&1:after['pc']=b
 return after,event
