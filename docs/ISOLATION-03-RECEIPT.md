# ISOLATION-03 — actual confined resource stops and exact continuation

Verified local Windows 2026-10-09; Python 3.12.10. Engineering, not new science.
Frozen contract 700600b5b9f7b510f54847504ee20609064d5005; original failed source
a48cc8153b3b46eb7b97fd61a6d480e8f415c3be. Corrected precommitted execution
302066f409f889a8aca4a858d39b0baf6b9e4385 includes the explicit
[execution erratum](ISOLATION-03-EXECUTION-ERRATUM.md). The original contract and
earlier approved evidence remain immutable. No simulation law or cap was tuned.

## Actual results

Two trial blocks, 22 native launches, 16 disposable seed-1 finite engineering
world histories, six actual resource stops and six exact fresh-process confined
resumes. CPU pressure hit the five-user-CPU-second supervisor (exit 124, before
wall deadline); 256 MiB committed allocation denied under the 128 MiB job limit
(MemoryError then authored exit 42); wall pressure hit ten seconds (exit 124).
Each stopped at the durable tick-5 journal/pending boundary with checkpoint tick 4.
Matched 0.05-second CPU/wall and 32 MiB memory controls completed under identical
native caps. Ordinary and confined references completed. No process remained active.

Every resumed/control/reference history independently replays to tick 32 and
matches all 33 complete states and 32 events: world identity, finite resources,
component provenance/ancestry, RNG and noise cursor. All six resumes retain the
original durable journal prefix. Kernel token, unique AppContainer SID, zero
capabilities and unchanged native Job settings checked before thread resume.
Recorded read-only observations leave world files unchanged; they are not a live
world display or OS-liveness claim. Unique profile deletion returned HRESULT zero.

Independent audit imports no driver/producer/launcher. A fully rehashed final
heat alteration in journal and checkpoint rejects for semantic world/work/RNG/
cursor/history/event divergence. 18 Windows checks attempted: 17 passed and one
expected non-Windows guard skipped. Existing capability/world/recovery regressions
included. All 277 shared tracked input files unchanged during acceptance.

## Failure and narrow correction

The first attempt passed 16 checks with one expected skip, then failed at native
CPU cleanup. Repeated clock queries accumulated kernel CPU, so the pressure marker
completed before the user-CPU criterion. Replace only instrumentation with the
existing integer-batch pattern; require measured user CPU at the stop. A concurrent
Job exit also caused TerminateProcess error 5. The launcher now tolerates that
specific race only after the process handle becomes signaled within two seconds.
Unsignaled access denial and other native errors still fail and have regressions.
Measured stop reason and final job usage are retained. No cap was relaxed.
Fresh corrected execution and separate audits passed; the failure is retained.

## Preserved evidence

Local records: `D:/OraLab/runs/isolation03-resource-20261009` (failed) and
`D:/OraLab/runs/isolation03-resource-20261009-v2` (accepted). Both source archives,
raw worlds, markers, ACL/native records, exits, logs, tests and audit retained.

| Evidence | SHA256 |
| --- | --- |
| Accepted source ZIP | 07cf3f272f25384933e0e78345fe54188e76add340ff9f4f4429bcfb6aaa6fce |
| Accepted raw panel | 1e0863f1f31780fdcaef6805e7c3c5785cb800f723570a983011746e922ee8c5 |
| Failed archive | 556b548bcc3d56ff68d5579eefaad8d973af7a609b4007ed80a6f5db872d94b4 |
| Accepted archive | c08e72e2c0652d4fc35b891e173b1f2eb3fcf53e3683a63a030d07f8dccc399c |

369 failed / 696 accepted sealed files restored and checked on D:. Operator lock,
finite process/time/memory bounds, panel disk ceiling and free-space floor applied.
Reviewed integration and independent off-drive handoff are recorded separately;
same-D archive restoration alone is not independent backup.

## What remains

This establishes bounded actual resource-triggered recovery inside tested native
confinement. It does not establish physical memory-peak bounds, hardware power-loss
recovery, hostile-escape resistance, complete filesystem/network confinement,
production security or unattended operation. Next: separately freeze software
storage faults inside confinement, then profile/permission restoration across a
new launch identity. No persistent pilot authorized or activated. RECYCLE-01
negative science, immutable histories and observer UI preserved; observer paused.
AI-Research main fef0a523 / Pass 29 unchanged. No autonomous origin, self-maintenance,
functional inheritance or evolution newly demonstrated.
