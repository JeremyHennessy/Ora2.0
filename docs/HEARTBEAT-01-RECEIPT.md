# HEARTBEAT-01 finite engineering acceptance — 2026-10-08

**Completed:** an operator-launched finite state-counter fixture and independent
read-only telemetry observer. Heartbeat ticks correspond to verified counter
transitions, not a clock callback. This is infrastructure validation,
not a population world, learning experiment, checkpoint restart or service.

## Frozen contract and executed source

[Contract](HEARTBEAT-01-CONTRACT.md) precommitted at
`bedd4457eac909aa892444cfd5b5dbf94f0d980b`. Implemented on an independent
branch; reconciled with verified science PR23/main5d23624 before acceptance.
Reviewed execution `6eaa85474205f396e08856380d654ed1bc864ea6` includes both
prior scientific work and the new finite engineering code. No science law,
dataset, observer page/UI baseline, dependency or original clone changed.

World/source/config/run identities remain immutable in every frame. A tick
consumes1work, produces1heat, and changes authoritative state hash. Config
limits are finite, max1000 ticks/work; manual acceptance also uses existing
operator lock,5GB free-space floor and300-second per-process timeout.
Exclusive output creation admits one writer; existing worlds are rejected
rather than overwritten or silently replaced. Append/fsync journal and atomic
latest snapshot contain state/hash, status and a separate UTC timestamp.

## Actual authored dry runs

| Case | Initial work / tick cap | Verified final tick | Status / reason | Frames |
|---|---:|---:|---|---:|
| Energy exhaustion |12 /32|12|stopped /exhausted|14|
| Preconfigured operator pause |12 /32, pause at5|5|paused /operator_pause|7|
| Tick quota |20 /7|7|stopped /tick_limit|9|

Three original and three replay invocations ended at the exact registered
state. All work/heat ledgers conserved. Authoritative sequences and independent
observer reports matched exactly after excluding wall-clock frame fields and
their chain hashes. Real UTC timestamps differ, so whole telemetry bytes are
**not** claimed byte-identical between new invocations. State hashes include
identity and tick, not the timer. The replay copies are not checkpoint resumes.

The observer's reads left all fixture bytes unchanged. A deliberately shortened
copy retaining the final running frame at tick12, observed6seconds later with
threshold5seconds, reported **stale** and verified tick12. This is a static
abandoned-journal test, not an actual crash/power-loss test. Recent running
telemetry reports `reported_running`, with process health **unverified**;
stopped/paused statuses stay truthful even when old. A journal/latest race
mismatch fails verification instead of showing invented freshness.

## Tests, failures and scope

**218 Windows Python3.12.10 tests passed**, exit0, on the reconciled repository.
New adversarial checks reject coherently rehashed timer-only ticks, skipped
ticks, changed world/config, invented energy, boolean tick counts, false stop
reason, backward/future time, corrupt journal and inconsistent snapshots.
An actual two-thread bounded writer race admitted one invocation and rejected
the other; observer verified the winning identity/tick4. Sequential reuse of
an existing output is also rejected. No acceptance failure occurred.

Same-D evidence archive restored all34 files exactly. No new scientific
initializations, auto-executed fetched commits, new worker scheduling, server,
public endpoint, API/model call, UI change or unattended operation occurred.
The counter is intentionally authored infrastructure; no maintenance,
evolution, lineage, cognition or organism capability follows from these tests.

Local run: `D:\OraLab\runs\heartbeat01-fixture-20261008T195320Z-6eaa8547`.
Archive: `D:\OraLab\archives\heartbeat01-fixture-20261008T195320Z-6eaa8547-evidence.zip`.

- Source ZIP:`0e279671acfb11175a162c92536dfb80ab91e23408f03755b26e5358641cdd94`
- Authoritative sequence:`ea239eed9614450f30fd057cbea813cf08c9298377953ce19fc8c6360855739e`
- Archive:`0893e2aa59eb103b363a7b5d8b9d8078b86c5750bffdf6506fd83db44a0579c6`

## Remaining limits and next engineering milestone

No resume API exists. A pause ends this invocation with an auditable snapshot;
it does not establish executable checkpoint continuity. First-writer directory
admission does not solve ownership/locking during later resume. Fsync and an
atomic latest file are not proof of physical power-loss durability. Failure
frames are best effort; storage failures can leave stale/inconsistent evidence.
The fixture does not verify OS CPU isolation, process health or a constructor
population schema. Reported original RUNTIME-01 AL01 acceptance is separate.

**Next engineering priority:** preregister schema-specific journal/checkpoint
restart for this finite fixture with immutable identity, injected before/after
journal/checkpoint process exits, exact authoritative-state recovery, no double
transition, source/config mismatch and competing-resume rejection. Use a
disposable manually launched copy and finite endpoint. Only after that passes
should a scientifically selected world adapter claim continuity. Off-D backup,
actual power-loss recovery, unprivileged isolation and separate human approval
still precede any unattended activation.

**Science remains separate:** CONSTRUCTOR-01 failed renewed-chain/exposure
admission and is closed. Its next prospective question concerns paid material
turnover/compositional production, not making the failed candidate appear alive
by keeping a timer running. AI-Research mainf2839a5c/Pass16 remains unchanged at
final review; literature/hypothesis work is not independent reproduction.
