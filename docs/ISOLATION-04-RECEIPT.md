# ISOLATION-04 — integrated one-world recovery verified

2026-10-09, actual Windows / existing Python 3.12.10. Frozen contract
ef8fedcc41ebe16a3af50c1e757d45d686951a8e; executed reviewed LF source
b5d3104087b397d07c62a45592dde4bc13d58e51. No world law, existing checkpoint
code, native gate, observer UI, dependencies or service configuration changed.

Two trial blocks / 40 launches / 16 finite engineering histories. Each of six
chains first hit actual resource limits at durable tick 5, then resumed the SAME
source-bound world and hit an I/O fault at tick 8. CPU stopped at its measured
user-CPU limit (124), memory denied a 256 MiB request under 128 MiB cap (42), and
wall stopped at ten seconds (124). Child job values and AppContainer token/caps
were checked while suspended; every launched process actually stopped.

| Registered outcome | Verified count |
| --- | ---: |
| Resource-triggered stops | 6 |
| Half journal / pending fsync / replacement faults, exit 2 | 6 |
| Partial-journal direct rejections with immutable files | 2 |
| Exact direct continuations from valid journal state | 4 |
| Ungranted new-SID and wrong-original-SID rejections | 12 |
| Exact restoration under distinct new identities | 6 |
| Unique profiles deleted, HRESULT zero | 8 |

The original profile was deleted BEFORE the three new-SID continuations in each
block. All restored/direct completed worlds match 33 complete states and 32
events of ordinary/confined references: world/run/source identity, material and
energy state, ancestry/component provenance, RNG and noise cursor. Raw valid
journal prefixes retained. Corrupted originals are never truncated or repaired:
partial tick-8 bytes remain preserved; their tick-7 trusted snapshots replay
independently, retaining every earlier valid frame. Deterministic reconstruction
of step 8 after restoration is labelled recovery, not a new discovery or replacement
genesis. Valid-journal cases restore their exact fault-time tick-8 inputs.

Independent auditor imports no worker, driver or launcher. It reconstructs exact
fault bytes, manifests, chains, trusted snapshots, copied runtime, complete matrix
and all states/events. Read-only recorded observations pass; stopped native
processes and stored heartbeat status are separate facts. Rehashed final-state
and falsely successful permission forgeries reject. 21 Windows checks attempted:
19 passed / two expected non-Windows guards skipped. 284 shared tracked inputs
unchanged. 1,188 sealed evidence files restored and checked on D:.

Local run `D:/OraLab/runs/isolation04-integrated-20261009`.
Source ZIP SHA256 a0846314af6c3d84489c68df4b892ee28142b031bffc982d75361cf248f75d7d.
Raw panel SHA256 f52cfe1ef07561dea27908b8a2bc8d5f295cae0abf6b1cd27baa846141950657.
Archive SHA256 d1956130ee5c359561e948870b5288f352615ed63edb0118b5861758d2bdc564.
Operator lock, 5 GB free floor, unchanged child limits, finite disk/time and
aggregate parent limits applied. No failed native attempt in this registered run.
Reviewed CI, manual integration and independent-drive restoration are recorded
in the separate final handoff. Same-D restoration alone is not independent backup.

## Remaining pilot gates

This closes the registered bounded resource/software-storage/new-launch-identity
composition. A pilot still needs explicit approval after these remaining gates:

1. Durability/recovery threat assessment: actual storage/power-loss behavior is
   unverified. Current fsync-error results use the running OS/cache. Define the
   acceptable lost-work window; validate recovery without trusting unsynced bytes.
2. Full-host/source-runtime/permission restoration rehearsal. Separate physical
   C:/ora backup is on the same computer and is not an off-host security/power backup.
3. Production isolation scope review: ordinary AppContainer still has Windows
   default access. Controlled denials are not a complete filesystem/network
   allowlist, hostile-escape assessment or memory-peak guarantee.
4. Validated observer telemetry must join authoritative world identity/tick/hash
   with independently checked process identity and advancing state. A PID alone,
   stored running heartbeat or animation cannot prove a live continuing world.
5. A finite, supervised pilot contract: disposable/approved world identity,
   operator ownership, stop conditions, recovery/export procedure, resource limits,
   local read-only observation and separate user authorization. No unattended
   service, public access or auto-execution of fetched commits.

Scientific self-maintenance, autonomous origin, inherited useful organization
and evolution remain unproven. RECYCLE-01 stays a negative baseline; no favorable
tuning. Research Pass 29 unchanged. Existing observer remains approved and paused.
