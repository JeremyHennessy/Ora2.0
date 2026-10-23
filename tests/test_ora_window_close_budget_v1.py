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
if __name__=='__main__':unittest.main()
