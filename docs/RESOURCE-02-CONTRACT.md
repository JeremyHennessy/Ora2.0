# RESOURCE-02 — resource-triggered finite-world continuity

2026-10-08. Freeze before implementation or fresh execution. Ora baseline
e67eae76fe1ae78e8ad7565ad8294802c6567e9a; research main
57e9bcda3919675492b3e0a5be068121d17455b7 (merged Pass 28).

## Question and unchanged boundaries

Do RESOURCE-01 Windows process-tree controls compose with HEARTBEAT-04 recovery
without changing world identity, committed history, random state, ancestry or
material/work provenance? This is disposable engineering replay of development
seed 1/work 2/horizon 32, not a new scientific sample, continuously running world,
origin, self-maintenance, reproduction or evolution experiment.

Do not edit either installed mechanism, its laws, source hash inventory, prior
protocol or data. Add a separate explicit finite pressure fixture, panel driver,
independent auditor and tests. No auto-restart, service, observer publication,
dependency installation, launcher change or automatic execution of fetched code.
Use exact reviewed revision, existing base Python for job commands, operator lock,
5 GB free-space floor, 300-second outer process deadline and D: evidence storage.

## Frozen boundary and causal contrasts

Generate one uninterrupted supervised reference under 512 MiB aggregate job
memory, 15 aggregate user CPU seconds, four process slots and 30 wall seconds.
Each replica has the same reference identity and original horizon, in a separate
new directory. These replicas do not become replacement worlds after interruption.

In the separate authored fixture, wrap the existing checkpoint-file write solely
to inject pressure after the tick-5 advanced checkpoint.pending has been written
and fsynced, before replacement of checkpoint.json. At this point frames.jsonl
contains tick 5, checkpoint.json contains tick 4, pending contains tick 5, and the
existing writer lock is held. Print and flush a boundary marker; spawn one known
sleeping descendant for OS cleanup verification. No draws or scientific state
changes are injected. Two ordered repeats of six cases, twelve records total:

| Case | Pressure after durable boundary | Caps: memory / CPU / wall |
| --- | --- | --- |
| cpu | Arithmetic for 1.5 worker process CPU seconds | 128 MiB / 1 s / 15 s |
| cpu-control | Identical arithmetic | 128 MiB / 5 s / 15 s |
| memory | Single 256 MiB allocation | 128 MiB / 5 s / 15 s |
| memory-control | Identical allocation | 512 MiB / 5 s / 15 s |
| wall | Sleep for 4 seconds | 128 MiB / 5 s / 2 s |
| wall-control | Identical sleep | 128 MiB / 5 s / 15 s |

All cases use four process slots (bootstrap, worker, sleeping child; one spare).
CPU exhaustion must occur after the boundary marker, before wall timeout, with
nonzero exit and at least 0.8 s observed aggregate user CPU. Memory denial emits
its causal marker then exits 42; the larger-memory control must really allocate
256 MiB and finish normally. The wall case must time out and exit nonzero; all
three controls finish tick 32 and exit zero. Preserve raw memory peaks and timing:
no exact hard CPU ceiling or verified peak-memory bound is claimed.

Copy each post-return world directory to immutable before evidence, then perform
one explicit supervised resume under the reference caps. Every resume must exit
zero, preserve the exact committed journal prefix, reach the same terminal world,
and retain the original manifest/run identity. All twelve complete canonical
state sequences must exactly equal the independently replayed reference, including
PRNG, noise cursor, every object/history/token and material/energy provenance.
For stopped pressure cases, independent before audit must report tick 5 and a
valid lagged checkpoint. Controls report stopped tick 32/current checkpoint.
Each sleeping descendant must have exited, independently checked through Windows
OS synchronization, on both limit-triggered and normal return. A terminal resume
must leave an already stopped control byte-idempotent.

## Verification and falsifiers

The new auditor imports neither new driver nor heartbeat worker nor resource
supervisor. Use the existing separate HEARTBEAT-04 interpreter for semantic replay
and RESOURCE-01 audit OS exit routine. Check exact source inventories, commands,
queried job caps, complete ordered panel, boundary/pressure markers, stop/control
contrasts, before/after manifests, journal prefixes, canonical sequences and
read-only behavior. Reject forged successful CPU stops, changed resume identities,
truncated or coherently rehashed world history, altered limits and duplicate keys.
The existing read-only heartbeat audit/observer CLI must remain compatible and
must continue reporting process health as unverified.

Any missing boundary, unexpected exit, malformed durable journal, surviving child,
source/config mismatch, altered prefix/identity/state or failed causal control
falsifies acceptance. Preserve failures and exact original source; investigate
before changing code. Do not silently adjust pressure or caps after seeing results.
Run regressions, preserve raw output/exits/audits/checksums, independently restore
the sealed evidence archive on D:, and leave prior laboratory/observer data intact.
Linux CI explicitly skips actual Windows enforcement; it cannot establish this
composition or physical power-loss reliability.

Off-drive backup, physical power-loss/storage-fault recovery, interpretation of
Windows peak-memory statistics and hardened filesystem/network isolation remain
open. The scheduling permission allows reviewed bounded development; unattended
continuous Ora world activation remains separately gated. Pass 27/28 prospective
scientific intake keeps transmission, fitness and reproductive packaging distinct;
neither literature nor engineering recovery changes frozen scientific studies.
