# STORAGE-01 — verified finite-world snapshot restoration

2026-10-08 local /2026-10-09 UTC. Contract precommit f26919e; initial source
a3481ec; corrected first panel source0e38512; final executed sourcec9a3fb49.
Existing Windows Python3.12.10. This is engineering reuse of seed1/work2/horizon32,
not a new scientific sample, origin experiment, law, unattended service or pilot.

## Demonstrated

The snapshot tool captures an independently replayed finite world at tick5 under
the existing cooperative writer lock. It preserves exact manifest/journal/
checkpoint bytes, identity, all live and historical objects/ancestry, atom/work
provenance, PRNG state and noise cursor. A fixed lock initializer is verified
before acquiring its Windows byte-range lock, then included without rewriting
or reading the held byte through a second descriptor. Repeated snapshots of
the unchanged world are byte-identical.

The frozen ten-case panel ran twice from fresh directories. In each panel:

| Path | Cases | Verified result |
| --- | --- | --- |
| Direct journal recovery |3|Missing/lagged checkpoint and junk pending recovered|
| Direct rejection |7|Partial/corrupt checkpoint or journal, missing journal, bad manifest/lock rejected with exit2; faulted bytes unchanged|
| Trusted-snapshot restoration |10|Create-new restore and explicit resume exited0; original identity and exact captured prefix retained|

All **13 direct/restored continuations** per panel matched the complete
**33-state reference sequence**, not only the final counts. This includes
resource ownership, random draws/cursor, objects and immutable lineage history.
All10 restored worlds passed the unchanged read-only observer CLI; audits left
inputs unchanged and still reported process health as unverified. Canonical
independent audit summaries matched exactly between the two fresh panels;
wall-clock frame timestamps and therefore raw snapshot ZIPs between panels differ.

## Verification and preserved failures

**Seven new Windows tests passed.**29 heartbeat and4 portable resource regressions
also passed on0e38512; these33 logs were reused for final acceptance only after
byte-identical old implementation, test and protocol-input checks. They were not
claimed as rerun on final source. The prior complete Windows and hosted suites
remain separate baseline evidence; hosted complete-suite CI gates this integration.

Focused checks cover exact identity/state round-trip and deterministic packaging,
no overwrite, wrong revision, real competing writer, duplicate ZIP/JSON members,
path/symlink/oversize members, boolean size descriptors and a coherently rehashed
noise-state forgery. The forgery passes envelope hashes but fails independent
world replay. A zero-byte lock-initializer write cannot report restore success:
every restored file is checked before semantic replay. No actual device short
write was induced. Separate disk-record exit/state forgeries were rejected by
the independent panel auditor. Neither auditor imports a simulation worker,
snapshot writer or panel driver.

All six initial tests failed because Windows denied a second-descriptor read
of the held lock byte. Original source/log/manifest/evidence were preserved and
restored; the correction and subsequent review are described in
[the diagnostic note](STORAGE-01-DIAGNOSTIC.md). No fault severity, expected outcome,
initial condition, old law or old runtime was adjusted. A second acceptance
attempt while the first still held the operator lock was refused before creating
another run; no overlapping laboratory writer was launched.

Acceptance retained raw worlds, fault copies, snapshots, original/replay panels,
process commands/exits, read-only audits, failure source and exact source ZIP.
Sealed evidence restoration matched657 files on the laboratory drive. Old
laboratory evidence, sealed archives and approved observer bytes remained intact.
Exact private locations and archive/file checksums are preserved locally rather
than republished as laboratory metadata. Operator locking,5GB floor and300-second
per-process deadlines applied. Existing science and reserved samples were untouched.

## What this does not establish

These are authored file-corruption/removal probes and same-drive snapshots.
They do not establish independent off-drive backup, physical power-loss or drive
failure, actual full-disk/short-write/fsync/replace-error durability, directory
flush behavior, noncooperative writer safety, hardened filesystem/network
isolation, a verified Windows memory-peak ceiling or readiness for an unattended
world. Invalid restoration outputs remain disposable diagnostic evidence and
are not run. Existing destinations and archives are never overwritten.

Persistence of the supplied world says nothing new about autonomous startup,
self-maintenance, reproduction, functional inheritance, adaptation or evolution.
Those scientific questions and the current negative baselines remain independent.

Next engineering gates: independently located backup and restore verification;
prespecified interrupted-write/fsync/replace-error boundaries; restricted process
isolation. Keep validated actual-state telemetry separate from recordings and
OS-health evidence. A supervised persistent pilot still needs its remaining
gates and separate authorization. Science should separately register generic
startup/renewal accounting and controls before installing or executing new physics.
