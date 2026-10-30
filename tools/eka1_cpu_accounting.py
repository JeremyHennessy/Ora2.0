"""Single-root postpaid CPU receipts. No launcher, refund or recovery authority."""
import ctypes
import hashlib
import os
import threading
from pathlib import Path
from experiments.process_limits import Accounting, ExtendedLimits, checked
from tools.eka1_native_owner_candidate import current_birth

_claim_lock=threading.Lock()
_claimed_assignments=set()
_claimed_roots=set()  # Strong references: GC/handle reuse cannot refund a claim.


class CpuAccountingFailure(RuntimeError):
    pass


class CpuBudgetExceeded(CpuAccountingFailure):
    pass


def ticks(value):
    if type(value) is not int or not 0 <= value < 2**63:
        raise CpuAccountingFailure('Missing/invalid exact CPU counter')
    return value


def root_snapshot(job):
    """Raw integer counters from the same retained root handle, never floats."""
    a=Accounting();limits=ExtendedLimits()
    checked(job.k.QueryInformationJobObject(job.handle,1,ctypes.byref(a),ctypes.sizeof(a),None))
    checked(job.k.QueryInformationJobObject(job.handle,9,ctypes.byref(limits),ctypes.sizeof(limits),None))
    return {'user_ticks':a.user,'kernel_ticks':a.kernel,'period_user_ticks':a.period_user,
            'period_kernel_ticks':a.period_kernel,'active':a.active_processes,
            'total_processes':a.total_processes,'cpu_limit_ticks':limits.basic.job_cpu,
            'memory_limit':limits.job_memory,'process_limit':limits.basic.active_processes,
            'flags':limits.basic.flags}


class RootCpuAttempt:
    """Pending before any child creation; one final debit, before root close.

    An interrupted pending receipt is unresolved, never zero or resumable.
    Final CPU excludes the external owner/build/archive scopes explicitly.
    """
    def __init__(self,job,out,mode,owner,save):
        if type(mode) is not int or mode!=3:raise CpuAccountingFailure('One fixed CPU role only')
        self.job=job;self.handle=int(job.handle);self.owner=owner;self.save=save
        self.out=Path(out);self.mode=mode;self.consumed=False
        self.assignment=owner._assignment;self.birth=tuple(owner._birth)
        self.physical=tuple(owner._physical);self.extent=owner._ledger._bytes
        with _claim_lock:
            root_key=(current_birth(),self.handle)
            if self.assignment in _claimed_assignments or root_key in _claimed_roots:
                raise CpuAccountingFailure('Root/assignment CPU claim consumed; no replacement')
            _claimed_assignments.add(self.assignment);_claimed_roots.add(root_key)
        self.base={'schema':'EKA-CPU-METERED-ATTEMPT-v1','mode':mode,
                   'assignment':self.assignment,'owner_birth':list(self.birth),
                   'ledger_identity':list(self.physical),'ledger_extent':self.extent,
                   'root_handle_in_owner':self.handle,'scope':'ROOT_JOB_USER_PLUS_KERNEL_ONLY',
                   'private_is_subset_not_added':True,'strict_prepaid_bound':False,
                   'external_owner_build_observer_archive_costs':'UNSETTLED_SEPARATE_SCOPES',
                   'historical_costs':'PRESERVED_UNRESOLVED_NO_AMNESTY',
                   'no_retry':True,'no_refund':True,'native_scientific_ready':False}
        self._custody()
        self.ledger_sha256=hashlib.sha256(owner._path.read_bytes()).hexdigest()
        self.base['ledger_sha256']=self.ledger_sha256
        self._custody()
        self.save(self.out/(str(mode)+'.cpu-pending.json'),dict(self.base,status='PENDING_UNRESOLVED',debit_ticks=None))
        initial=root_snapshot(job)
        self.base['initial']=initial
        self.save(self.out/(str(mode)+'.cpu-initial.json'),dict(self.base,status='INITIAL_OBSERVATION'))
        self._counters(initial)
        if initial['user_ticks'] or initial['kernel_ticks'] or initial['active'] or initial['total_processes']:
            raise CpuAccountingFailure('Root CPU epoch must be fresh and empty')

    def _custody(self):
        if int(self.job.handle or 0)!=self.handle or not self.handle:
            raise CpuAccountingFailure('Root handle custody interrupted')
        o=self.owner;fd=os.fstat(o._fd);named=o._path.lstat()
        if (current_birth()!=self.birth or o._closed or o._failed is not None or
            o._assignment!=self.assignment or tuple(o._birth)!=self.birth or
            tuple(o._physical)!=self.physical or
            (fd.st_dev,fd.st_ino)!=self.physical or (named.st_dev,named.st_ino)!=self.physical or
            fd.st_nlink!=1 or named.st_nlink!=1 or fd.st_size!=self.extent or named.st_size!=self.extent):
            raise CpuAccountingFailure('Owner/assignment/physical ledger custody interrupted')
        if hasattr(self,'ledger_sha256') and hashlib.sha256(o._path.read_bytes()).hexdigest()!=self.ledger_sha256:
            raise CpuAccountingFailure('Canonical ledger bytes changed')

    @staticmethod
    def _counters(value):
        ticks(value['user_ticks']);ticks(value['kernel_ticks'])
        if ticks(value['period_user_ticks'])!=value['user_ticks'] or ticks(value['period_kernel_ticks'])!=value['kernel_ticks']:
            raise CpuAccountingFailure('Root CPU accounting epoch reset/inconsistent')
        if (type(value['active']) is not int or value['active']!=0 or
            value['cpu_limit_ticks']!=80000000 or value['memory_limit']!=256*1024**2 or
            value['process_limit']!=4 or value['flags']!=0x220c):
            raise CpuAccountingFailure('Root closure/limit readback inconsistent')

    def finish(self,guardian,private,errors):
        if self.consumed:raise CpuAccountingFailure('CPU debit consumed; no retry')
        self.consumed=True  # Burns authority before any final read/write.
        report=dict(self.base,status='UNKNOWN_UNRESOLVED',debit_ticks=None,
                    guardian=guardian,private_subset=private,control_errors=list(errors))
        failure=None
        try:
            self._custody()
            final=root_snapshot(self.job);report['final']=final
            self._counters(final)
            report['debit_ticks']=ticks(final['user_ticks'])+ticks(final['kernel_ticks'])
            report['debit_status']='MEASURED_ROOT_ONLY_ONCE'
            if errors:raise CpuAccountingFailure('Termination/capture/custody incomplete')
            if not guardian or guardian['signaled'] is not True or guardian['root_member'] is not True:
                raise CpuAccountingFailure('Retained guardian closure missing')
            if type(guardian['pid']) is not int or guardian['pid']<=0 or int(guardian['birth'])<=0:
                raise CpuAccountingFailure('Guardian birth custody missing')
            if type(final['total_processes']) is not int or final['total_processes']!=2:
                raise CpuAccountingFailure('Root successful-birth accounting inconsistent')
            if not private or private['closed'] is not True:
                raise CpuAccountingFailure('Private final counters/closure missing')
            if (type(private.get('total_processes')) is not int or private['total_processes']!=1 or
                type(private.get('active_processes')) is not int or private['active_processes']!=0):
                raise CpuAccountingFailure('Sole private successful-birth/closure accounting inconsistent')
            if (guardian['pid'],str(guardian['birth']))==(private['pid'],str(private['birth'])):
                raise CpuAccountingFailure('Guardian and sole child must be distinct retained births')
            pu=ticks(private['user_ticks']);pk=ticks(private['kernel_ticks'])
            if (private['leader_signaled'] is not True or private['leader_root_member'] is not True or
                private['leader_private_member'] is not True or type(private['pid']) is not int or
                private['pid']<=0 or int(private['birth'])<=0 or
                ticks(private['leader_user_ticks'])!=pu or ticks(private['leader_kernel_ticks'])!=pk):
                raise CpuAccountingFailure('Sole CPU child custody/accounting inconsistent')
            gu=ticks(guardian['user_ticks']);gk=ticks(guardian['kernel_ticks'])
            if final['user_ticks']!=pu+gu or final['kernel_ticks']!=pk+gk:
                raise CpuAccountingFailure('Nested/process CPU accounting inconsistent')
            if pu>10000000 or final['user_ticks']>80000000:
                report['status']='FAIL_CPU_BUDGET'
                raise CpuBudgetExceeded('CPU budget exceeded; full measured debit retained')
            report['status']='MEASURED_WITHIN_USER_CEILINGS_NOT_NATIVE_QUALIFICATION'
        except BaseException as exc:
            failure=exc;report['failure']=type(exc).__name__+': '+str(exc)
        # A write failure leaves PENDING unresolved; no second debit/write try.
        try:self.save(self.out/(str(self.mode)+'.cpu-final.json'),report)
        except BaseException as write_error:
            if failure is not None:
                failure.cpu_observation=dict(report,persistence='FINAL_WRITE_INCOMPLETE_NO_RETRY')
                failure.add_note('CPU final receipt write failed; pending unresolved: '+repr(write_error))
                raise failure from write_error
            raise
        if failure is not None:raise failure
        return report
