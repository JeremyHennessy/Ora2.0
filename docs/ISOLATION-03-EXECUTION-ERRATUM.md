# ISOLATION-03 execution correction, frozen before corrected execution

The original 700600b contract remains immutable. Initial execution a48cc815
passed 16 Windows tests (one platform skip), then failed in native CPU cleanup.
Preserved archive: isolation03-resource-20261009-evidence.zip, SHA256
556b548bcc3d56ff68d5579eefaad8d973af7a609b4007ed80a6f5db872d94b4,
369 files restored. Profile deletion succeeded; no accepted recovery result.

Two engineering defects were found, without changing world physics or cap values:

1. Clock-query-only pressure accrued substantial kernel time; process-time seven
   seconds is not five user CPU seconds. The marker showed the request completed.
   Use existing RESOURCE-02-style integer batches between process-clock queries
   to exercise user CPU. Requested seven seconds and matched 0.05 control remain.
   Audit also requires measured user CPU >=4.8 seconds for CPU stop, versus <5
   for wall stop. This is instrumentation correction, not favorable science tuning.
2. Job termination is asynchronous. A second TerminateProcess can return error 5
   for an already exiting process. Accept only error 5 followed by a signaled
   process handle within two seconds; any unsignaled or other failure still rejects.
   Preserve measured supervisor reason/usage and final job usage. Unit regression
   must reject access-denied with an unsignaled handle and other native failures.

[Microsoft's native API contract](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-terminateprocess)
documents asynchronous termination and error 5 on already terminated processes.
The earlier accepted ISOLATION-01/02 raw evidence, source and contracts stay frozen.
The focused launcher cleanup change requires their relevant regression checks.
All original matrix, costs, controls, boundaries, exact-state/prefix/replay criteria,
resource values and no-service/security limitations continue unchanged.
