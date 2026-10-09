# ISOLATION-02 — actual finite-world continuity inside confinement

2026-10-09. Frozen a56f8cc1, accepted execution 14521c83. Existing HEARTBEAT-04
seed-1/work-2/32-tick engineering fixture; no new scientific samples or physics.
Unchanged ISOLATION-01 suspended token/capability/job gates and unchanged world
producer, independent replay and checkpoint/recovery code are composed in a
disposable AppContainer runtime. No approved world was migrated.

## Accepted matrix

Two trials / 28 launch cases / 12 world histories. Two ordinary uninterrupted
references, two confined uninterrupted references, eight confined interrupted
histories and eight fresh-process resumes, two wrong-identity rejections and
six fail-closed setup refusals. All source-pinned local tests passed: 14.

| Tick-5 boundary | Exits, both trials | Independently verified durable tick | Resume |
|---|---|---|---|
| Before journal commit | 77 | 4 | 0, same 33 states |
| After journal commit | 78 | 5 | 0, same 33 states |
| After pending checkpoint | 79 | 5 | 0, same 33 states |
| After checkpoint replacement | 80 | 5 | 0, same 33 states |

Every completed history independently replays all 33 states and 32 reaction
events, matching the ordinary reference exactly. Complete world/finite ledger,
object/component identity and provenance, ancestry/history, RNG, noise cursor and
event chains survive. Each recovered journal retains the durable byte prefix;
resume reuses the original identity/directory. Lifecycle timestamps, resume epochs
and status frames legitimately differ. There is no byte-identical-journal claim.

Each actual confined worker's kernel token carries its unique package SID and
zero capabilities; parent checks this and reads back the existing 128 MiB
committed-job-memory, five-second CPU, one-process-slot, kill-on-close caps before
resume. Ordinary workers have two slots. Ten-second worker and 300-second panel
horizons; operator lock, five-GB free-space floor and finite panel size ceiling.
No physical-memory-peak or malicious disk-quota claim.

Wrong-world-identity resumes exit 2 with the complete world tree unchanged.
Missing executable fails creation; injected assignment/token gate failures stop
suspended processes before a world directory or worker marker exists. All workers
are independently observed stopped after job/handle closure. Unique profile
cleanup succeeds. Earlier ISOLATION-01 remains the independent file/network/process
capability control; no external network probe is made by this panel.

Existing independent HEARTBEAT-04 inspector captures real state read-only, with
unchanged world tree hashes. Evidence is explicitly recorded; a crash's reported
running frame is not process health. Kernel exit and final audited stopped state
are distinct facts. No observer UI, current telemetry adapter or publication
changed. Separate panel auditor imports no launcher, driver or worker; it validates
the complete matrix, raw histories, copied source/runtime, caps, identities,
observations and prefixes. Rehashed journal plus checkpoint heat forgery rejects
on independent world/provenance/RNG/cursor/history/event replay.

Accepted raw evidence SHA256:
39e6560c0e938d91ab84d4302ca3a87f1d5bf14c0d417a4ee4c5bc5ea2b5180e.
Source archive SHA256:
b316e5335062f7e4137b9393b1cedab1c07f3ffc5be3823177479afd78f8f092.
Accepted archive SHA256:
5e3a1a923960d56e6f4cbf065988eb4851140a55fe0603b51a5a956ba649fc79.
All 641 sealed files restored on D:; all 271 shared tracked files unchanged during
acceptance. Private receipts preserve actual exits, source revisions, complete
worlds, before-resume states, runtime hashes, ACL output and operator evidence.

## Preserved failure

Initial cf3ddef attempt completed the ordinary reference but the new observation
wrapper passed a datetime object to an existing API that requires a UTC string.
The failed run remains sealed; all 346 files restored. Archive SHA256:
5dff0b2e093167671a43055431c316be02bbc0750d010f50d3025506680bd675.
Corrected only the new wrapper/auditor argument type and added a real read-only
observation regression check. Original world, observer, launcher, physics and
prospective contract were not changed.

## Interpretation and next gate

Bounded actual-world process-exit continuity inside this controlled confinement
composition is demonstrated. Resource-triggered termination and software-storage
faults were previously verified separately; their behavior *inside* confinement
must not be assumed. Next separately precommit that composition and test profile /
filesystem-permission restoration across a new launch identity, then assess
production isolation gaps. Physical power-loss, full-host/off-host recovery,
hostile escape/complete filesystem/network assessment and unattended operation
remain open. No persistent pilot is authorized or activated by these results.

Science remains at RECYCLE-01's preserved negative unscreened realization. A
distinct generic full-cost local resource/reaction coupling candidate is still
needed; engineering continuity does not demonstrate autonomous origin,
self-maintenance, functional inheritance or evolution. AI-Research main fef0a523
/ Pass 29 unchanged; no unproven research mechanism installed. Observer paused.
