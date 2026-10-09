# STORAGE-02 — injected write, synchronization and replacement failures

Prospective engineering contract, 2026-10-09. Preserve STORAGE-01/BACKUP-01,
all historical worlds and science. This is a disposable HEARTBEAT-04 fixture,
not a new law, natural sample, durable-device certification or running service.

## Frozen scope before execution

Seed1, work2, horizon32, world ID `storage02-reference`; all fault targets are
the advancing frame at tick5. Keep one uninterrupted reference and a trusted
tick3 paused snapshot. Every test uses a new directory and the exact reviewed
source archive. No old receipt is opened for writing. Full state means identity,
PRNG, cursor, ancestry, material and work provenance, not just the final tick.

Cross journal/pending writes with seven distinct injections: half-length return,
zero-length return, half-write then OSError, flush OSError before delegation,
fsync OSError before delegation, fsync OSError after successful delegation,
half-write/real flush+fsync followed by actual process exit. Add replacement
OSError before and after successful replacement:16 cases per complete panel.
An out-of-process injector wraps the existing writer's real file operations;
it never modifies authoritative input after the worker stops. It records exactly
one targeted injection. Exit codes81/82 mean forced journal/pending termination;
ordinary propagated injected errors must exit2. No platform disk is filled or
powered off. Python buffering and the same OS cache remain in the test boundary.

Freeze injection names/order and byte fractions. A reported short successful
write is a specific falsifier: the worker must propagate an error rather than
claim successful completion. First diagnose it on the preserved baseline;
preserve any failure before the smallest write-count guard repair. This repair
may change I/O error handling, never physics, formats, identity rules, costs,
old evidence, or any expectation to make a corrupted journal acceptable.

## Independent criteria and controls

Three half-journal cases must reject direct resume with exit2 and preserve
all input bytes. Zero journal write leaves tick4; the other complete-journal
cases leave tick5 and must continue exactly through32. All pending/replace
faults leave the independently valid tick5 journal and must recover. Pending
bytes are never authority. Successful continuation must retain its entire
previous journal prefix. Read-only inspection must not modify any file.

For every case, restore the untouched tick3 snapshot to a separate new directory
and resume to32. Each direct/backup continuation must match all33 independently
replayed reference states, including original identity and every history field.
The verifier imports no worker, injector or panel generator. It reconstructs
expected interrupted journal/checkpoint/pending bytes from the captured tick5
payload and verified prefix, checks exact commands/exits, source hashes and the
whole ordered case denominator. Timestamped raw journals need not match across
fresh invocations; canonical complete state histories and normalized results must.
Rehashing a false claimed outcome must not defeat semantic verification.

Run two fresh complete panels with deterministic normalized audit agreement,
focused I/O regressions and existing heartbeat/snapshot regressions. Operator
lock, at least5GB free, finite32 ticks, subprocess30-second limits and overall
300-second acceptance limits apply. Capture failures, process exits, source ZIP,
raw before/after files, hashes, replay audit and same-drive archive restoration.
Preserve new sealed evidence on the already user-selected independent backup
drive with readback; active experiment files remain on the laboratory drive.

## Interpretation and stopping

Any unexpected exit, injection multiplicity, mutation of a rejected input,
state/history mismatch or false independent acceptance fails this gate. Diagnose
the original failure before changing code. Do not discard failed cases, repair
their data, truncate journal tails or silently start a replacement world.
Passing establishes this registered user-space fault/recovery boundary only.
It does not prove filesystem crash consistency, directory fsync durability,
physical power-loss/device recovery, whole-host reconstruction, hard memory
bounds, filesystem/network isolation, unattended safety or scientific progress.
Those gates and separate persistent-pilot authorization remain outstanding.
