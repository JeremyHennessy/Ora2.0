"""Independent pure literal of four proposed operations; no producer imports."""
import json

def transition(state,instruction,length):
 def bounded(v,upper):
  if type(v) is not int or not 0<=v<=upper:raise ValueError('literal bounds')
 if type(length) is not int or not 1<=length<=32:raise ValueError('literal code')
 if type(instruction) is not list or len(instruction)!=3:raise ValueError('literal triple')
 o,x,y=instruction
 bounded(o,25)
 if o not in (22,23,24,25):raise ValueError('literal opcode')
 bounded(x,7 if o==25 else 1);bounded(y,length-1 if o==25 else 15 if o==24 else 1)
 if type(state) is not dict or set(state)!=set(('memory','registers','pc','energy')):raise ValueError('literal state')
 memory=state['memory'];registers=state['registers']
 if type(memory) is not list or len(memory) not in (2,4,8) or type(registers) is not list or len(registers)!=2:raise ValueError('literal units')
 for v in memory+registers:bounded(v,15)
 bounded(state['pc'],length-1)
 if type(state['energy']) is not int or not 1<=state['energy']<=224:raise ValueError('literal fuel')
 out=json.loads(json.dumps(state));total=2 if o==22 else 3 if o==23 else 1;charge=min(state['energy'],total)
 out['energy']-=charge
 receipt=dict(version='CONTEXT90-PACKED-ACCESS-v2',decoded=instruction[:],cpu=1,logic_fee=charge-1,actor_cost=charge,required=total,completed=charge==total,read=None,write=None)
 if charge!=total:return out,receipt
 out['pc']=(state['pc']+1)%length
 if o in (22,23):
  address=registers[y if o==22 else x]%(len(memory)*2);index=address//2;shift=0 if address%2==0 else 2
  original=memory[index]
  if o==22:
   val=(original//(1 if shift==0 else 4))%4;out['registers'][x]=val
   receipt['read']=dict(slot=address,cell=index,offset=shift,word=original,value=val)
  else:
   val=registers[y]%4;other=(original//4)*4 if shift==0 else original%4
   replacement=other+val*(1 if shift==0 else 4);out['memory'][index]=replacement
   receipt['write']=dict(slot=address,cell=index,offset=shift,before=original,value=val,after=replacement)
 elif o==24:out['registers'][x]=registers[x]^y
 else:
  bit=(registers[x%2]//(2**(x//2)))%2
  if bit==1:out['pc']=y
 return out,receipt
