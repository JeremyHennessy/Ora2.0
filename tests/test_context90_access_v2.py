"""NEW pure source/interface tests only; no World, task labels or old tests."""
import copy
import unittest
from experiments import digital_context90_access_v2 as vm
from experiments import digital_context90_access_literal_v2 as literal
from experiments import digital_context90_source_v2 as source


def abstract_trial(memory,entry,cue,feedback,pre=7,post=6):
 """Invented register dataflow only; operation fuel is not a living state."""
 code=source.programme(len(memory),entry);r=[0,0];m=memory[:];pc=entry;phase=0;cost=0;cpu=0;fees=0;writes=[];action=None;reads=[]
 for _ in range(64):
  old=pc;op,a,b=code[pc];pc=(pc+1)%len(code);cpu+=1;cost+=1
  if op in vm.NEW_OPS:
   state=dict(memory=m,registers=r,pc=old,energy=224)
   after,event=vm.transition(state,[op,a,b],len(code))
   m,r,pc=after['memory'],after['registers'],after['pc'];cost+=event['logic_fee'];fees+=event['logic_fee']
   if event['write'] is not None:writes.append(event['write'])
   if event['read'] is not None:reads.append(event['read'])
  elif op==0:r[a]=cue if phase==0 else pre if phase==1 else post;phase+=1
  elif op==1:r[a]=feedback
  elif op==4:r[a]=b
  elif op==6:action=r[a]&1
  elif op==7:pc=b
  elif op==8:
   if r[a]==0:pc=b
  elif op==21:r[a]^=15
  else:raise AssertionError('unexpected source operation')
  if (old,pc) in source.BOUNDARIES:
   source.completed_boundary(old,pc)
   return dict(memory=m,entry=pc,registers=r,action=action,cost=cost,cpu=cpu,fees=fees,writes=writes,reads=reads)
 raise AssertionError('unfinished loop')


def slot(memory,index):return (memory[index//2]>>(2*(index%2)))&3

def put(memory,index,value):
 m=memory[:];c=index//2;s=2*(index%2);m[c]=(m[c]&(~(3<<s)&15))|(value<<s);return m


class PackedAccess(unittest.TestCase):
 def test_new_interface_literal_neighbours(self):
  for q in (2,4,8):
   for index in range(16):
    for word in range(16):
     for value in range(16):
      for a,b in ((0,1),(1,0),(0,0),(1,1)):
       r=[value,value];r[a]=index
       s=dict(memory=[word]*q,registers=r,pc=0,energy=9);before=copy.deepcopy(s)
       t=[23,a,b];out,event=vm.transition(s,t,30)
       self.assertEqual((out,event),literal.transition(s,t,30));self.assertEqual(s,before)
       address=r[a]%(2*q);cell=address//2;shift=2*(address%2)
       self.assertEqual(out['memory'][cell]&(~(3<<shift)&15),word&(~(3<<shift)&15))
       self.assertEqual((out['memory'][cell]>>shift)&3,r[b]&3)
       read=[22,b,a];self.assertEqual(vm.transition(s,read,30),literal.transition(s,read,30))

 def test_new_alu_branch_types_and_bounds(self):
  for x in range(16):
   for y in range(16):
    for a in (0,1):
     s=dict(memory=[0]*8,registers=[x,x],pc=0,energy=9)
     self.assertEqual(vm.transition(s,[24,a,y],30),literal.transition(s,[24,a,y],30))
   for a in range(8):
    for target in (0,29):
     s=dict(memory=[0]*2,registers=[x,x],pc=4,energy=9)
     self.assertEqual(vm.transition(s,[25,a,target],30),literal.transition(s,[25,a,target],30))
  good=dict(memory=[0]*8,registers=[0,1],pc=0,energy=9)
  for t in ([True,0,0],[22,2,0],[23,0,2],[24,0,16],[25,8,0],[25,0,30],[22,False,0],(22,0,0),[18,0,0]):
   for impl in (vm,literal):
    with self.assertRaises(ValueError):impl.transition(good,t,30)
  for key,value in (('energy',0),('energy',True),('pc',30),('memory',[0]*3),('registers',[0,16])):
   s=copy.deepcopy(good);s[key]=value
   for impl in (vm,literal):
    with self.assertRaises(ValueError):impl.transition(s,[22,0,1],30)

 def test_new_billing_partial_and_snapshot(self):
  for t in ([22,0,1],[23,1,0],[24,0,8],[25,7,3]):
   for energy in range(1,7):
    s=dict(memory=[10]*8,registers=[3,9],pc=6,energy=energy);before=copy.deepcopy(s)
    out,e=vm.transition(s,t,30);self.assertEqual((out,e),literal.transition(s,t,30));self.assertEqual(s,before)
    self.assertEqual(out['energy']+e['actor_cost'],energy);self.assertEqual(e['cpu']+e['logic_fee'],e['actor_cost'])
    if energy<vm.PRICES[t[0]]:
     self.assertFalse(e['completed']);self.assertEqual(out['pc'],s['pc']);self.assertEqual(out['memory'],s['memory']);self.assertEqual(out['registers'],s['registers'])
    self.assertEqual(vm.transition(s,t,30),vm.transition(s,t,30))

 def test_new_independent_capacity_aliases(self):
  for q in (2,4,8):
   for entry in (1,3):
    code=source.programme(q,entry);self.assertEqual(len(code),30);self.assertEqual(3*len(code)+q+8,98+q)
    addresses=[(cue+(8 if route else 0))%(2*q) for route in (0,1) for cue in range(8)]
    self.assertEqual(len(set(addresses)),2*q)
  m=[0]*8
  for i in range(16):m=put(m,i,1 if i%2 else 2)
  self.assertEqual([slot(m,i) for i in range(16)],[1 if i%2 else 2 for i in range(16)])

 def test_new_complete_own_feedback_and_distractors(self):
  for q in (2,4,8):
   for entry in (1,3):
    for cue in range(8):
     for initial in (0,1,2):
      address=(cue+(8 if entry==3 else 0))%(2*q);memory=put([0]*q,address,initial)
      for feedback in (0,1,2):
       reference=None
       for pre in range(8):
        for post in range(8):
         got=abstract_trial(memory,entry,cue,feedback,pre,post)
         stable={k:v for k,v in got.items() if k!='registers'}
         if reference is None:reference=stable
         self.assertEqual(stable,reference);self.assertEqual(got['action'],initial&1)
         self.assertEqual(got['cost'],got['cpu']+got['fees'])
       got=reference
       if feedback==2:self.assertEqual(got['memory'],memory);self.assertEqual(got['entry'],entry)
       elif feedback==1:
        self.assertEqual(got['entry'],entry)
        self.assertEqual(slot(got['memory'],address),2 if initial==0 else initial)
       elif initial==0:
        self.assertEqual(got['entry'],entry);self.assertEqual(slot(got['memory'],address),1)
       else:
        alternative=(cue+(0 if entry==3 else 8))%(2*q)
        self.assertNotEqual(got['entry'],entry);self.assertEqual(slot(got['memory'],alternative),2 if got['action']==1 else 1)
        if q==8:self.assertEqual(slot(got['memory'],address),initial)

 def test_new_personal_retention_and_reuse(self):
  for start in (1,3):
   memory=[0]*8;entry=start
   for cue in range(8):
    t=abstract_trial(memory,entry,cue,1);memory,entry=t['memory'],t['entry']
   first_route=memory[:]
   t=abstract_trial(memory,entry,0,0);memory,entry=t['memory'],t['entry']
   for cue in range(1,8):
    t=abstract_trial(memory,entry,cue,0);memory,entry=t['memory'],t['entry']
   for cue in range(8):
    a=cue+(8 if start==3 else 0);self.assertEqual(slot(memory,a),slot(first_route,a));self.assertEqual(slot(memory,a^8),1)
   t=abstract_trial(memory,entry,0,0);memory,entry=t['memory'],t['entry'];self.assertEqual(entry,start)
   used=abstract_trial(memory,entry,7,1)
   self.assertEqual(used['action'],0);self.assertEqual(used['writes'],[]);self.assertEqual(used['reads'][0]['value'],2)

 def test_new_boundaries_and_path_costs(self):
  for pair in source.BOUNDARIES:self.assertEqual(source.completed_boundary(*pair),pair[1])
  for pair in ((28,29),(23,3),(27,1),(True,1)):
   with self.assertRaises(ValueError):source.completed_boundary(*pair)
  for entry in (1,3):
   for state in (0,1,2):
    for feedback in (0,1,2):
     address=8 if entry==3 else 0
     got=abstract_trial(put([0]*8,address,state),entry,0,feedback)
     self.assertLessEqual(got['cpu'],19);self.assertLessEqual(got['cost'],23)

if __name__=='__main__':unittest.main()
