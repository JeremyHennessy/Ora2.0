# ISOLATION-02 — confined finite-world continuity

Frozen prospective engineering matrix, 2026-10-09. Builds on accepted ISOLATION-01,
HEARTBEAT-04 and RESOURCE-02 without changing those laws, launchers or receipts.
No approved world migration, fresh science samples, service or observer publication.

Use the existing HEARTBEAT-04 seed-1 / work-2 / 32-tick template-world fixture.
Copy its exact eight source/protocol files plus package initializer into the
disposable read/execute runtime. Same explicit world identity within each paired
trial; full state, finite ledger, component provenance, ancestry, RNG and noise
cursor must match an ordinary reference at every one of 33 states.

Two trials. Each executes an ordinary uninterrupted reference and a confined
uninterrupted reference, then four fresh confined histories interrupted at tick 5:
pre_commit (77), post_journal (78), post_pending (79), post_checkpoint (80).
Fresh confined process resumes each history, reusing the original directory and
identity. Expected pre-resume durable tick is 4 for pre_commit, 5 otherwise;
resume exit 0 and terminal tick 32. Every journal prefix must be preserved byte
for byte; all 33 independently replayed states and event sequences must equal
the ordinary and confined references. Timestamps/epoch/resume frames legitimately
differ; do not demand byte-identical journals across different lifecycle paths.

Each trial also attempts wrong-world-identity resume of a completed confined
reference: exit 2, original world tree unchanged. Three setup refusals per trial
(missing executable, injected assignment gate and injected token gate) must not
resume, create a world directory or write the worker-start marker. Each worker is
created suspended; the unchanged ISOLATION-01 token/capability/job gates run first.
Both references intentionally share authored fixture identity, not production
authoritative world instances; no claim of spontaneous organization or evolution.

Limits: exclusive laboratory operator lock, 5 GB free-space floor, 256 MiB panel
disk ceiling checked between cases, 300 seconds panel horizon. Existing kernel
job readback: 128 MiB committed job memory, five CPU seconds, ten wall seconds,
one process slot confined / two ordinary. Outer bounded supervisor caps parent
tree. No physical-memory peak or malicious disk-quota claim. Unique temporary
profile is deleted; only new D: workspace/runtime ACLs changed. No external network
probe, installed-runtime permission change, global firewall, service or existing
profile modification. Unchanged ISOLATION-01 remains the file/network null control.

Existing independent HEARTBEAT-04 inspector replays all serialized states/events.
Observer compatibility uses that same read-only inspector: capture report and
source hashes before/after inspection, prove world tree unchanged. Observation is
explicit recorded evidence. Reported running at a crash is not process liveness;
kernel process-stop checks establish the exited worker, and terminal stopped
requires verified final state. No UI, existing telemetry adapter or publication
changes. Independent panel auditor must verify full matrix, source/runtime hashes,
tokens/caps, exits, durable prefixes, exact states/events, identities, object and
component histories, observations and cleanup. A recomputed-hash tampered final
state must be rejected by semantic replay. Preserve all failures.

Success is bounded process-exit continuity of an actual finite world inside this
controlled AppContainer/job composition. It is not physical power-loss, hostile
escape assessment, complete filesystem/network confinement, full-host recovery,
production security or an unattended persistent-world authorization. If accepted,
next review production isolation gaps and physical durability verification before
a separately authorized supervised pilot; scientific startup/renewal remains an
independent unresolved track.
