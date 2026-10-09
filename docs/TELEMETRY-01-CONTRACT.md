# TELEMETRY-01 — validated recorded/live readiness without UI changes

Prospective contract, 2026-10-09; freeze before bounded tests. Read-only function
adapter, no service, simulation command, network listener, UI redesign or publishing.
Use unchanged HEARTBEAT-04 independent world auditor for actual states/identity/
ancestry/resources/RNG/noise/event history. Never fabricate movement or components.

Default mode is recorded: emit verified current world, tick, noise cursor, state/
frame hashes, last actual event, identity and recorded heartbeat status. No process
probe and no active claim. Ordinary frozen receipts are always recorded data.

Live mode requires an explicit trusted operator launch binding containing PID,
Windows process creation FILETIME, world_id, run_id and exact source revision.
Manifest must match all three world/source IDs. Native probe uses only process
query-limited-information and synchronization rights; creation time must match.
PID reuse, denied/unavailable native query or invalid binding cannot imply active.
Binding authenticity is a launcher/operator provenance requirement, not something
inferred from any user-supplied JSON or PID. Existing launcher receipts without
creation-time binding cannot be silently promoted to live observations.

Active requires two coherent independently audited snapshots in live mode with
same binding/identity, earlier frame hash in current valid history, increasing
simulation tick, fresh stored heartbeat and currently alive matching native process.
An alive process with unchanged state remains awaiting advancement. Stored stopped/
paused world status remains stopped/paused even if its process exists. A gone native
PID is stopped; a reused PID is mismatch. Partial/invalid history, source mismatch,
incoherent reads or history regression returns unknown/mismatch, never active.
Exclude the intentionally locked writer.lock from read-only checksums; all other
world files must match before/after the audit. Concurrent advancing writes can
cause retry/unknown, not forged consistency or world mutation.

Fields are point-in-time samples with observed_utc/last_heartbeat_utc. A future
observer must expire an active display within two seconds without another fresh
sample and clear it on any unknown/mismatch/stall. This adapter does not implement
frontend polling/publication or a continuous-world connection. Preserve approved UI,
recording and paused owning chat. Its automation owns publication.

Bounded tests: recorded mode performs no native probe; damaged partial journal
returns unknown unchanged; actual Windows PID/creation-time and in-writer tick1/2
snapshots verify awaiting/active; repeated state stays inactive; wrong creation time
and forged prior frame hash stay inactive; stopped world stays stopped while test
process remains alive. Source-bound disposable three-tick world only, no approved
world altered. Independent semantic auditing remains outside world producer.
Pin exact LF source under existing operator lock, five-GB floor, D: temp/raw files,
finite existing resource/time caps, preserve logs/exits/hash/restored archive and
independent backup. Linux CI may skip actual Windows identity fixture explicitly.

This verifies adapter readiness, not live deployed telemetry, production isolation,
physical durability, pilot safety or new scientific capability. Further trusted
launcher binding, end-to-end observer validation and pilot approval remain required.
