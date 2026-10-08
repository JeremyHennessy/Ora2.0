# RESOURCE-01 — supervised finite Windows process limits

2026-10-08. Prospective contract, freeze before implementation/execution.
Baseline Ora main 2648b11829d991c2130ea31bdf1737182c1e077c; research main
ba1581557d599801ef5942c8047156f184925777. Science and HEARTBEAT-04 unchanged.

## Question and boundary

Can a manual supervisor enforce finite aggregate memory, aggregate user CPU,
active-process count and wall duration on an explicitly requested known Python
process tree, including cleanup after the root exits? This is engineering,
not learning, self-maintenance, filesystem/network isolation or permission to
activate an unattended world. No service installation or local launcher change.

Use Windows Job Objects through standard-library ctypes, no dependency/admin
installation. The supervisor holds the only job handle; kill-on-job-close is
mandatory. A known bootstrap waits for permission on stdin. Assign that bootstrap
to the configured job before granting permission to spawn the actual command.
If job creation/configuration/assignment fails, terminate the bootstrap and fail
closed; never run the target outside the job. Child inheritance is Windows job
membership, not an inheritable job handle. No shell evaluation.

Job limits: finite aggregate committed memory, aggregate user CPU, maximum active
processes, and kill-on-close. The bootstrap counts as an active process; require
at least two process slots. Set CPU exhaustion to terminate the entire job rather
than posting a notification. Monotonic wall timeout causes explicit whole-job
termination, then closure. Even normal root completion closes the job so orphaned
descendants cannot remain. Capture output with a draining thread and at most
1 MiB retained bytes; discard excess and report truncation. Limits do not bound
disk writes, network access, filesystem rights, kernel CPU, GPU or the supervisor
itself. Do not describe them as a security sandbox or hardware power-loss safety.

Report configured limits, bootstrap exit, timeout, observed peak committed job
memory, job-accounting user CPU and number of started processes, bounded output,
and explicit Windows-only status. Observed accounting is supplementary; do not
infer which limit caused an exit merely from its code. Cap enforcement must be
supported by a dedicated causal fixture.

## Frozen fixtures and acceptance

All commands are disposable authored test fixtures, never historical worlds.
Use a 128 MiB job-memory cap, 5 user CPU seconds, 3 process slots and 5 wall seconds
unless a causal fixture specifies a stricter limit. Fixed fixtures:

1. Finite success: print a marker and exit zero.
2. CPU limit: unbounded arithmetic worker under 0.2 user CPU seconds / 5 wall
   seconds; nonzero termination before wall deadline, observed user CPU recorded.
3. Memory limit: attempt a single 256 MiB allocation under 128 MiB job memory.
   Catch MemoryError, emit marker and exit 42; allocation must not succeed.
4. Process limit: bootstrap + worker + sleeping child fill 3 slots; fourth
   process creation must fail. Report child PID and attempt outcome. Child must
   be gone after supervised return.
5. Timeout tree: worker starts sleeping child, reports its PID, then waits;
   wall limit 0.5 seconds must terminate both, within a 5-second fixture margin.
6. Normal orphan cleanup: worker starts sleeping child, prints PID, exits zero;
   supervisor return must still imply child exit.
7. Output limit: worker emits 2 MiB; only at most 1 MiB retained, excess reported;
   completion must not block or exhaust supervisor output storage.
8. Fail-closed assignment: inject a deterministic assignment refusal; a target
   side-effect marker must remain absent and the waiting bootstrap must exit.
9. Portable invalid-config tests reject nonfinite/zero CPU or wall caps, memory
   below 32 MiB, process counts below two and invalid commands without spawning.
10. Read-only source/receipt guards and all existing tests must pass. Linux CI
    explicitly skips Windows enforcement fixtures; passing Linux tests is not
    Windows cap evidence.

Independently inspect OS child exit using a synchronization handle where possible,
rather than trusting stdout alone. Preserve every failure, source revision,
fixture logs, exact replay of deterministic assertions, test results and same-D
archive restoration. No fresh/reserved scientific samples, source-law retuning,
observer application edits, auto-updates, external API or continuous activation.

Acceptance is bounded Windows process-tree resource enforcement only. Independent
off-D backup/restore, physical power-loss/storage-fault testing and hardened
restricted filesystem/network execution remain open. Continue science separately
with precommitted precursor reaction-coupling accounting, without treating resource
cap verification as scientific progress.

