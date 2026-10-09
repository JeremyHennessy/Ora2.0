# ISOLATION-04 — one-world resource, storage and launch-identity recovery

Prospective engineering contract, 2026-10-09; freeze before fresh execution.
No new physics, science, approved-world migration, service or unattended pilot.

Two trial blocks, unchanged seed-1/work-2/32-tick finite world. Ordinary and
confined full references per block. Three sequential chains per block:
CPU stop -> half journal write; memory denial -> pending-file fsync failure;
wall stop -> checkpoint replacement failure. Resource pressure uses unchanged
ISOLATION-03 values/caps at durable tick 5 (CPU user >=4.8, exit 124 or 1816;
memory 256 MiB denied, exit 42; wall twelve-second request stopped at ten, 124).
Resume the SAME source-bound world under its original AppContainer SID and inject
exactly one tick-8 I/O operation fault. CPU/wall matched controls are already
registered and accepted in ISOLATION-03; new ordinary/confined references remain.

At durable pending tick 7 the fixed adapter captures a trusted file snapshot:
manifest, journal, checkpoint, pending bytes and a canonical unlocked writer-lock
byte. Independent replay must verify tick 7 and exact raw prefix through tick 7.
Faults: half journal write followed by OSError; complete pending write/fsync then
OSError; replacement raises OSError before delegating. All faulted writers exit 2.
The partial journal must reject direct resume without changing world bytes.
Other two cases must directly resume exactly. Preserve all damaged worlds.

Restore partial-journal case from the verified tick-7 snapshot; restore the other
two from their verified fault-time tick-8 copy. Partial tick-8 bytes remain in the
damaged original, never truncated or silently repaired. The valid raw prefix is
retained in restoration; deterministic step 8 is reconstructed, not counted as
new science. Each restore is a disposable alternative continuation, not a second
active production world. No overlapping writers.

Each restoration gets a distinct newly created AppContainer profile. Copied
runtime has read/execute permissions; new restore folders start with protected
owner/System/admin ACLs and low integrity. New SID without a workspace grant must
reject (exit 2, no worker-start marker, no world mutation). Grant only that new SID
Modify recursively on this new folder; original SID must reject unchanged under
its valid native token. Then delete original profile before any new-SID resume.
New-SID resumes must exit zero, preserve world/run/source identity, all ancestry,
provenance, RNG/noise, valid journal prefix and all 33 states/32 events. No original
installation ACL, existing profile, global firewall or approved world is altered.

Fixed denominator: 40 launches, 16 world histories, six resource stops, six I/O
faults, two unchanged direct rejections, four exact direct continuations, twelve
permission rejections and six exact new-SID restorations; eight profiles cleaned.
Each native launch uses unchanged 128 MiB/five-CPU-second/ten-wall-second job and
one confined slot (two ordinary), checked while suspended. Actual kernel exit
required; OS liveness never substitutes for state replay. Read-only recorded
observations distinguish stored status from stopped processes.

Independent audit imports no worker, driver or launcher; reconstructs fault bytes,
complete matrix, source/runtime binding, identities, full states and prefixes.
Rehashed state and falsely successful permission claims must reject. Exact source
LF archive, existing operator lock, 5 GB free floor, 256 MiB panel ceiling, 280-second
panel and 300-second parent limits. Parent aggregate 512 MiB / 90 CPU seconds /
eight process slots: extra sequential replay/native work, not relaxed child caps.
Preserve failed/accepted evidence, exits, hashes, D: restoration, reviewed CI,
manual integration and independent C:/ora backup before completion.

This is user-space software-fault and new-profile composition, not real disk
failure, power-loss durability, complete filesystem/network confinement, hostile
escape proof, memory-peak guarantee, full-host recovery or persistent-pilot approval.
