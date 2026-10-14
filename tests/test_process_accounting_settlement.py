"""Delayed job accounting must not be confused with genuine live children."""
import unittest
from unittest.mock import Mock, patch
from experiments import process_limits as resource

class AccountingSettlement(unittest.TestCase):
    def test_signalled_exit_waits_for_observed_zero_accounting(self):
        job=Mock();job.usage.side_effect=[{'active_before_close':1},{'active_before_close':1},{'active_before_close':0}]
        job.pids.return_value=[17]
        with patch.object(resource.time,'monotonic',return_value=0),patch.object(resource.time,'sleep') as sleep,patch.object(resource,'process_exited',return_value=True):
            self.assertEqual(resource.settled_usage(job,resource.Limits(),0)['active_before_close'],0)
            self.assertEqual(sleep.call_count,2)
    def test_real_orphan_is_never_relabelled_as_exited(self):
        job=Mock();job.usage.return_value={'active_before_close':1};job.pids.return_value=[17]
        with patch.object(resource.time,'monotonic',return_value=0),patch.object(resource.time,'sleep') as sleep,patch.object(resource,'process_exited',return_value=False):
            self.assertEqual(resource.settled_usage(job,resource.Limits(),0)['active_before_close'],1)
            sleep.assert_not_called()
    def test_accounting_wait_cannot_extend_registered_wall_deadline(self):
        job=Mock();job.usage.return_value={'active_before_close':1};job.pids.return_value=[]
        with patch.object(resource.time,'monotonic',return_value=5),patch.object(resource.time,'sleep') as sleep:
            self.assertEqual(resource.settled_usage(job,resource.Limits(wall_seconds=5),0)['active_before_close'],1)
            sleep.assert_not_called()

if __name__=='__main__':unittest.main()
