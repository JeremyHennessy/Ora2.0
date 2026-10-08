# RESOURCE-01 — bounded Windows process-tree controls receipt

2026-10-08. Original contract precommit 1f51448; diagnostic addendum e6fc005.
Executed clean source cdaff83f062a3f21cf6cc56afd5b5f5344404e95, Python 3.12.10.
This is engineering verification on disposable fixtures, with zero scientific
worlds and no reserved samples. Observer application and simulation laws unchanged.

## Implemented and independently checked

Manual standard-library Windows Job Object supervisor. Known bootstrap waits on
stdin until assignment succeeds; job limits are queried back before command
permission. Aggregate memory allocation constraint, aggregate user CPU budget,
active-process limit, monotonic wall timeout and kill-on-close are configured.
CPU is also polled every 10ms, because native cumulative-time enforcement is
periodic. Non-Windows calls fail closed; Linux CI cannot verify Windows limits.
Supervisor retains at most 1 MiB output while draining excess. Normal root exit
also closes the job, stopping orphaned descendants. No install, service, simulation
execution from UI, launcher change, automatic update or unattended activation.

**279 Windows tests completed: 278 passed, 1 non-Windows-only guard skipped**,
184.847 seconds, exit0. All previous 268 tests passed. Windows fixtures test
assignment refusal before target side effects as well as causal enforcement.
Acceptance: eight fixed fixtures repeated twice, 16 records; independent auditor
imports no supervisor, checks source/limits/contrasts, and checks six descendant
exits through separate OS synchronization handles. Deterministic assertions
matched across trials; CPU timings/PIDs are variable and are not byte-replay claims.
Forged CPU-success and duplicate-key evidence rejected, expected exit1; raw inputs
unchanged by audit.

| Fixture | Original result | Repeat result |
| --- | --- | --- |
| finite success | exit0 | exit0 |
| CPU0.2 / wall5 | supervisor stop, exit124, CPU0.203125s, wall0.312s | exit124, CPU0.203125s, wall0.297s |
| 256MiB allocation under 128MiB cap | MemoryError, exit42 | MemoryError, exit42 |
| same allocation under 512MiB control | allocation succeeds, exit0 | allocation succeeds, exit0 |
| 3 process slots | fourth creation denied; child exited | same assertion |
| wall0.5 with child | exit124, wall0.500s; child exited | exit124, wall0.516s; child exited |
| normal orphan | root exit0; child exited | same assertion |
| 2MiB output | exit0; exactly1MiB retained, excess discarded | same assertion |

## Failures preserved and limits of the claim

Initial implementation ae8cd1a and development logs remain recorded:
focused-first had seven failures because Windows venv redirectors occupied extra
process slots. The known stdlib bootstrap and authored fixtures now use the
existing base Python directly; target commands are never silently substituted.
Venv targets still need allowance for their redirector processes.

Focused-base preserved two failures: native CPU termination missed the fixed
five-second wall deadline in one test, and a memory-peak assertion failed.
An identical diagnostic later terminated at CPU0.8125s / wall0.906s. Prospective
addendum froze supervisor polling and the larger-cap causal memory control before
their implementation/execution; original scientific/engineering data unchanged.

Windows PeakJobMemoryUsed reports approximately289MB during both refused and
allowed256MiB allocations. The denied test really raises MemoryError and succeeds
only under the larger cap, with configured128MiB read back. The statistic's
relationship to denied commitment remains unresolved. Retain raw peaks;
**no verified peak-memory upper-bound claim** follows from them.
Likewise, polling/scheduling may overshoot CPU thresholds; **no exact hard CPU
ceiling**. User CPU budget excludes kernel/GPU usage. No disk-write, filesystem,
network, supervisor-resource or adversarial security isolation established.

Original contract/addendum preserved. This demonstrates the tested allocation
constraint, observed CPU-budget termination and whole-tree lifecycle controls,
not a hardened sandbox, power-loss durability or biological capability.

## Preservation and observer coordination

Run: D:/OraLab/runs/resource01-caps-20261008T225657Z-cdaff83f.
Source ZIP SHA256: 4faa817da1c6137da0d8ebfb4fe5d92259efbcb35d9cf3196f8b855f2063fddf.
Fixtures SHA256: 67ef50b8d78038f456d50dd5379ea0cba6fae638742ecea9facf936d763ccdb5.
Evidence archive: D:/OraLab/archives/resource01-caps-20261008T225657Z-cdaff83f-evidence.zip,
SHA256 0610b902c755ea38320d90b6ec889746bb5430d812d44186ba95b83bdd30b89e.
All16 archived files restored byte-for-byte on D:. 63 historical receipt/archive,
shared dashboard/tool and launcher hashes unchanged. Same-D restoration is not
an independent off-drive backup.

Human-authorized coordination with Build Read-Only Universe Observer confirmed
three local-only observer commits through aa84f64. That chat advanced local main,
while GitHub main remained2648b118. Its ora-observer-v1 app reads the existing
HEARTBEAT-04 reference, with no spatial/live-world claim; actual Safari remains
unverified. Preserve local observer commits and appended plan during manual
integration. This resource PR does not publish the app, recording or screenshots.
Research main ba158155 / merged Pass26 unchanged; Pass25 PR5 remains open/conflicted.
No AI-Research files changed.

Next science remains separately precommitted activated-precursor/reaction-energy
coupling feasibility, with full costs and external-subsidy withdrawal controls.
Next engineering: investigate memory accounting and prospectively verify a
disposable finite checkpointed world's recovery after resource-triggered exit.
Off-D backup, physical power-loss/storage-fault recovery and hardened restricted
execution remain open; no unattended activation.

