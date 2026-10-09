# TELEMETRY-01 — validated state/process adapter readiness

2026-10-09. Frozen contract 4fdeec3ff106658e8842615fb40718989ab16bfb;
executed exact LF source e2dce7f791ae598edc4eb88be94c3d664c39341f.
This is a read-only function adapter and bounded engineering fixture, not a
deployed live-world connection or an activated persistent pilot.

Default recorded mode independently validates full finite-world state, identity,
ancestry/provenance, resources, RNG/noise, event and history hashes. It never
probes a PID or calls recorded data active. Live mode additionally requires an
explicit trusted launcher/operator binding: PID, Windows process creation time,
world_id, run_id and exact source revision. An alive matching process is necessary
but insufficient: active requires coherent audited advancement and a valid shared
history prefix. Repeated state, stale data, wrong process birth, bad history and
unavailable process queries cannot imply active. Stored stopped/paused worlds
remain stopped/paused even while a native process exists.

Three Windows tests passed. A separate disposable three-tick fixture captures
real Windows PID/creation-time bindings and four independently replayed snapshots
(ticks 1..3 and terminal). Two advancing observations active; three repeated-state,
three wrong-birth and three forged-prior-history observations inactive. Terminal
world stopped while its test process was still alive; recorded terminal observation
validated but never active. Independent interpreter checks all reported world
values against the actual journals. A forged reported heat value rejects. No
historical PID is represented as currently alive.

Producer/audit/test exits and exact raw bytes preserved. Existing Python 3.12.10,
exclusive operator lock, five-GB floor, fresh D: folders and ordinary parent limits
(512 MiB committed-memory cap, 15 user-CPU seconds, three process slots, 30-second
wall limit per command). This fixture is not an AppContainer deployment test or
physical memory-peak measurement. 295 shared tracked inputs unchanged; 329 sealed
accepted files restored on D:.

First evidence harness failed before fixture execution because its private launcher
omitted the helper import directory. Three tests had passed; no fixture world was
launched. The failed source/logs/exits are preserved (305 restored files). Only
private packaging changed; the accepted rerun uses the SAME frozen public source.

Private laboratory receipts:

- Accepted `D:/OraLab/runs/telemetry01-readiness-20261009-v2`, raw telemetry SHA256
  `f3469be55984eb5d176e7e1b3e9b696f133b98514ef8d5f9708e19c821b1029e`.
- Accepted archive SHA256
  `eaa9adf6771e6ea3bec6ec6bd7a78bb6b943ef551269c5bc14c7be6ef1dfc77d`.
- Failed archive SHA256
  `d2a312959cd219c04e1053999ce8051fe6120c55d7334d0e9554207a5727d537`.

**Remaining:** trusted birth-time binding from the actual approved launcher;
observer end-to-end validation and expiration of active displays within two seconds
without fresh samples. Existing launch receipts lack this binding and remain
recorded. No frontend polling, publication, service, UI redesign or unattended
simulation was added. Observer work/publication remain paused in their owning chat.
Physical durability, full-host recovery, production isolation and a finite
supervised pilot contract with separate approval remain open. No scientific
self-maintenance, reproduction, learning or evolution demonstrated by telemetry.
