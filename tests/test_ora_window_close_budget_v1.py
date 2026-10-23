"""Window-tail scheduling regression; no live models/stores or timing extension."""
import math,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments.ora_controller_v1 import service_duration,EPOCH_CLOSE_RESERVE
class Budget(unittest.TestCase):
 def test_retained_failed_tail_reserves_close_before_model_deadline(self):
  # Observed old model budget287.351689577. Allow4s preparation here.
  model=287.35168957710266;preparation=4.0
  duration=service_duration(300,model-preparation,model-preparation)
  self.assertAlmostEqual(duration,253.35168957710266)
  self.assertLessEqual(preparation+duration+EPOCH_CLOSE_RESERVE,model)
  old_duration=min(300,model-preparation)
  self.assertGreater(preparation+old_duration+1,model)
 def test_full_epoch_unchanged_when_budget_sufficient(self):
  self.assertEqual(service_duration(300,700,650),300)
 def test_both_window_and_model_cap_work(self):
  self.assertEqual(service_duration(300,100,800),70)
  self.assertEqual(service_duration(300,800,100),70)
 def test_clock_jump_cannot_extend_budget(self):
  self.assertEqual(service_duration(300,10000,80),50)
 def test_exhausted_preparation_refuses_work(self):
  for x in [0,-1,30,30.9]:
   with self.assertRaises(TimeoutError):service_duration(300,x,900)
 def test_invalid_or_nonfinite_budget_refused(self):
  for x in [True,float('inf'),float('nan'),'100']:
   with self.assertRaises(ValueError):service_duration(300,x,900)
class Lifecycle(unittest.TestCase):
 def run_case(self,prep=40,utc_jump=0,dead=False,seconds=200):
  import tempfile,json,types
  from unittest.mock import patch
  from experiments import ora_controller_v1 as c
  class Clock:
   now=0.;jump=0.
   def time(self):return 1000+self.now+self.jump
   def monotonic(self):return 100+self.now
   def sleep(self,x):self.now+=x
  clock=Clock();services=[];model_closes=[];service_end=[0.];service_stop=[None]
  class Model:
   start={'pid':123,'creation_filetime_decimal':'456'}
   thread=types.SimpleNamespace(is_alive=lambda:not dead)
   def __enter__(self):return self
   def prepare(self):clock.now+=prep;clock.jump+=utc_jump
   def check_model(self):pass
   def __exit__(self,*args):clock.now+=3;model_closes.append(clock.now)
  def native(builder,*args,**kw):
   command=builder()
   if 'experiments.ora_supervised_service_v1' in command:
    duration=float(command[command.index('--seconds')+1]);services.append(duration);service_end[0]=clock.now+duration;service_stop[0]=kw['stop_event']
   else:clock.now+=float(command[command.index('--seconds')+1])
   return dict(exit_code=0,reason='exit',output='{}',post_close_processes_exited=True,descendant_leak=False,output_limit_exceeded=False)
  class Thread:
   def __init__(self,target,**kw):self.target=target
   def start(self):self.target()
   def is_alive(self):return clock.now<service_end[0] and not (service_stop[0] and service_stop[0].is_set())
   def join(self,seconds):clock.now+=min(seconds,max(0,service_end[0]-clock.now))
  with tempfile.TemporaryDirectory() as d:
   root=Path(d)
   with patch.object(c,'time',clock),patch.object(c,'OwnedOllama',return_value=Model()),patch.object(c,'boot_token',return_value='fixture'),patch.object(c,'identity',return_value={'pid':123,'creation_filetime_decimal':'456'}),patch.object(c,'run_slice',side_effect=native),patch.object(c.threading,'Thread',Thread):
    result=c.controller(root,seconds=seconds,epoch_seconds=300,practice=0)
   hold=(root/'controller-safety-hold.json').exists()
  return result,services,model_closes,hold,clock
 def test_preparation_and_final_service_close_inside_unchanged_window(self):
  result,services,closes,hold,clock=self.run_case()
  self.assertEqual(services,[130]);self.assertLess(closes[0],200)
  self.assertEqual(result['completed_epochs'],1);self.assertEqual(result['failures'],0);self.assertFalse(hold)
  self.assertEqual(result['deadline_utc'],1200);self.assertEqual(result['reason'],'time-bound')
 def test_late_preparation_starts_no_service_and_fails_closed(self):
  result,services,closes,hold,clock=self.run_case(prep=175)
  self.assertEqual(services,[]);self.assertEqual(result['failures'],1);self.assertTrue(hold)
  self.assertEqual(result['deadline_utc'],1200)
 def test_unexpected_model_death_still_charges_failure_and_hold(self):
  result,services,closes,hold,clock=self.run_case(prep=20,dead=True,seconds=400)
  self.assertEqual(result['failures'],1);self.assertTrue(hold)
  self.assertIn('Owned model server exited',result['history'][-1]['error'])
 def test_utc_backwards_cannot_extend_monotonic_budget(self):
  result,services,closes,hold,clock=self.run_case(utc_jump=-100)
  self.assertEqual(services,[130]);self.assertLess(closes[0],200);self.assertFalse(hold)
 def test_utc_forward_caps_service_earlier(self):
  result,services,closes,hold,clock=self.run_case(utc_jump=40)
  self.assertEqual(services,[90]);self.assertLess(closes[0]+40,200);self.assertFalse(hold)
if __name__=='__main__':unittest.main()

