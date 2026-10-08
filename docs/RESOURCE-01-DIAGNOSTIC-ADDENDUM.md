# RESOURCE-01 prospective diagnostic addendum

2026-10-08, after initial development failures; preserve original contract/law.
Original precommit 1f51448; initial implementation committed separately before
this addendum. Development logs focused-first.log, focused-base.log and
caps-diagnostic.log are preserved under D:/OraLab/runs/resource01-development.

The venv redirector consumes additional process slots. Known stdlib bootstrap
and disposable fixtures use the existing base Python directly; arbitrary target
commands retain their argument vector and must budget every launcher process.

With fixed original 128 MiB / 3-process limits, the allocation actually raises
MemoryError (exit42), but Windows PeakJobMemoryUsed reports about 289 MB. Its
relationship to denied commitment is unresolved: retain that raw statistic,
do not call it a verified upper bound or silently remove the discrepancy.
Read configured limits back from the job and fail closed if they differ.
Prospective causal memory control: the exact same 256 MiB allocation under a
512 MiB job cap must succeed, versus rejection at the original 128 MiB cap.
This is an additional engineering control, not a retuned scientific experiment.

Microsoft documents job user-time enforcement as periodic:
https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_basic_limit_information
One original CPU fixture exceeded the five-second wall margin before OS CPU
termination; later identical diagnostic execution ended at 0.8125 user CPU
seconds / 0.906 wall seconds under the 0.2 CPU cap. Preserve this variability.
Add manual supervisor polling of aggregate job user CPU every 10ms and whole-job
termination on observed threshold crossing, retaining the OS limit as a backstop.
Report supervisor_cpu_stop separately from wall timeout and raw exit codes.
Polling and scheduling can overshoot; no exact CPU hard ceiling claim.
Keep original CPU0.2 / wall5 fixture and success/falsifier unchanged.

Validate configured memory/CPU/process flags and values at construction and
return them alongside accounting. Refused allocation + causal allowance is
evidence of the allocation constraint; raw peak statistics are an unresolved
accounting limitation, not scientific evidence. Kernel/GPU/disk/FS/network and
supervisor resource usage remain outside the claim.

Reference for memory limit and raw peak field definitions:
https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_extended_limit_information

Re-execute the original fixed fixtures plus the prospective memory control,
preserve negative development outputs and exact source pins, then full regression
suite. No installation, observer files, runtime launchers or simulation changed.

