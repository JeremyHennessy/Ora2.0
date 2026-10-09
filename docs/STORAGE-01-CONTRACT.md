# STORAGE-01 — verified snapshots and bounded storage-fault recovery

Freeze before implementation and fresh execution. Baseline Ora main1be0c4ed;
research mainbfbd53c7. This is engineering reuse of development seed1/work2/
horizon32, not a fresh science sample, new physical law or persistent pilot.
All approved laws, runtime interfaces, observer files and historical data stay
unchanged. Add separate snapshot/restore tools, an independent panel auditor,
focused tests and a disposable finite fault panel. No service or auto-restart.

## Snapshot contract

Capture an independently replayed, paused HEARTBEAT-04 world at tick5 under its
existing cooperative writer lock. Snapshot the exact manifest, complete journal,
current or valid-prefix checkpoint when present, and one-byte lock initializer.
Ignore pending files. Retain original identity, source/Python bindings, complete
objects/history/ancestry, all material/work provenance, PRNG and noise cursor.
Pin exact reviewed revision. Bind snapshot-tool/contract and old world-source
hashes, file sizes/hashes, final frame/state hashes and captured tick in metadata.
Two snapshots of this unchanged world must be byte-identical.

Only explicit create-new archive and create-new restore directory operations;
never overwrite, repair or truncate an existing world or backup. Require a
complete fixed member allowlist, reject duplicate names/JSON keys, paths,
directories, encrypted/symlink members and unsupported compression. Limits:
journal16MiB, manifest/checkpoint1MiB each, lock1 byte, metadata64KiB; reject
declared oversize before decompression. Source, identity and checksums must agree.
Restoration must pass the separate old world interpreter before reporting success.
A coherently rehashed but semantically invalid archive must fail; preserve its
new disposable restoration output for diagnosis, never run it or overwrite old data.
No pickle or executable archive contents. A valid hash alone is not a valid world.

## Frozen panel

Create an uninterrupted reference and one paused tick5 snapshot. For every case,
copy the paused world into a new disposable fault directory, perform exactly one
listed mutation, preserve an immutable copy, attempt one explicit existing-world
resume, then restore the same trusted snapshot to a separate fresh directory and
resume to the original horizon. These are storage-path replicas of one identity.
Never present a new replacement identity as continuation.

| Fault | Mutation | Direct resume expected |
| --- | --- | --- |
| missing-checkpoint | Remove only disposable checkpoint |0, recover audited journal|
| stale-checkpoint | Use exact tick2 journal frame |0, recover audited journal|
| junk-pending | Add malformed ignored pending bytes |0, ignore pending|
| partial-checkpoint | Keep first half of checkpoint bytes |2, reject|
| rehashed-checkpoint | Add one heat, recompute state/frame hashes |2, reject non-prefix|
| partial-journal | Append incomplete JSON without LF |2, reject|
| corrupt-journal | Alter tick1 heat, coherently rehash entire frame chain and checkpoint |2, reject semantic divergence|
| missing-journal | Remove only disposable journal |2, reject|
| bad-manifest | Replace configuration digest with zeros |2, reject|
| bad-lock | Replace initializer with two bytes |2, reject writer lock|

For all ten cases, backup-based continuation must exit0 and its complete canonical
33-state sequence must match the independently regenerated reference, including
identity/ancestry/PRNG/provenance. Original snapshot manifest and exact captured
journal prefix must remain present. All seven direct rejections must preserve
faulted file bytes. The bad-lock case may remain readable by the old observer;
readable state is not writer readiness or OS process health.

The new auditor imports no panel driver, snapshot writer or simulation worker.
Independently derive the listed mutations, verify archive members/metadata/source
bindings, replay every world through the existing independent interpreter, verify
prefixes, original identity, expected exits and full reference state sequences.
Re-run the panel in a fresh directory; canonical outcome summaries must match
despite wall-clock frame differences. Old read-only observer CLI must accept all
restored final worlds and leave their inputs unchanged.

## Acceptance and limits

Test exact round-trip state/identity, no overwrite, malformed/oversize/duplicate/
path/symlink archives, coherently rehashed semantic forgery, and a real competing
writer. Apply operator lock,5GB floor,300-second per-process deadlines, existing
Python and D: temporary/evidence storage. Independently restore sealed acceptance
evidence and retain source, process exits, raw worlds, fault copies, audits, hashes
and all failures. Guard historical laboratory, archive and observer bytes.

Any unexpected exit, mutation of rejected inputs, lost identity/prefix/state,
accepted invalid snapshot, missing control or independent audit/replay mismatch
falsifies this acceptance. Investigate and preserve failures before amendments;
do not silently alter old laws, fault severity or expected outcomes.

Injected file corruption/removal is not a real exhausted/full/failing device,
short-write syscall, permission boundary or physical power loss. Restoration on
the laboratory drive is not independent off-drive backup. Filesystem durability,
directory fsync, malicious noncooperative writers, hardened isolation, Windows
peak-memory bounds and persistent-pilot authorization remain separate open gates.
Snapshots preserve supplied finite world state; they establish no autonomous
origin, self-maintenance, functional inheritance, adaptation or evolution.
