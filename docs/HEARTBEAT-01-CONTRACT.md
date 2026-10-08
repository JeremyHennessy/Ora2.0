# HEARTBEAT-01 — finite authoritative-state telemetry fixture

2026-10-08, engineering only. Freeze before implementation. This separate
branch introduces no new scientific law, population service, layout change or
unattended runtime. It does not make constructor worlds persistent.

## Smallest meaningful fixture

Operator-launched finite worker on a **new** output directory, exact source
revision and nonempty immutable world ID. Configuration: integer work0..1000,
max_ticks1..1000, optional pause_after1..max_ticks. This is an authored energy
counter, not an artificial organism. Each transition consumes1work, produces
1heat, advances simulation_tick exactly1 and changes the state hash.
Work+heat equals initial work at every tick. No clock callback counts as a
transition. Stop on zero work or max_ticks; optional pause checkpoint reports
paused and ends this invocation. No auto-resume or new replacement identity.

World ID, source revision, config hash and run ID (hash of their combination)
are immutable in every telemetry frame. simulation_tick is distinct from UTC
last_heartbeat. Frames contain complete authoritative state, state_sha256,
previous frame hash, frame_sha256, status running/paused/stopped/failed and
reason. A status-only frame can change wall time/status but must not increase
tick or fabricate a changed state. The state digest includes immutable
identity and tick/work/heat, excludes wall-clock metadata.

Use exclusive output-directory creation as first-writer admission; an
existing output is rejected rather than overwritten or resumed. An exclusive
writer.lock identifies an admitted invocation and is removed when it exits.
Append/fsync each complete frame to frames.jsonl; atomically replace latest.json
after the journal write. No server, scheduler, new dependency or terminal
window. Finite limits plus the existing external300-second/minimum-space/
operator-lock acceptance harness bound local work. No OS CPU isolation claim.

## Read-only observer and independent verification

Observer reads journal/latest only, creates/edits nothing, and never invokes
worker or advances the state. Independently verify identity, hashes, complete
integer state, conservation and all transitions from tick0. A running initial
tick0 is ready but has advanced zero transitions. A timer/status-only heartbeat
with a claimed new tick must fail audit. Require latest to equal the last
journal frame. Return inconsistent evidence when a concurrent reader observes
a journal/snapshot mismatch; never invent a fresh verified state.

At a caller-supplied current UTC time, report age and stale threshold. Valid
stopped/paused/failed statuses remain truthful even when old. A journal left
running beyond threshold is reported stale; a recent running frame is
reported_running with **process health unverified**. A timestamp alone cannot
prove an actual worker is alive. Reject future timestamps, backward timestamps,
corrupt hashes, skipped/doubled ticks, changed identity/config/source and
negative/invented energy. Report verified tick/state hash separately from
wall age and status. No learning/lineage/material-network claims are supported.

## Acceptance and limits

Authored manual dry run: work12/max_ticks32 ends stopped/exhausted at tick12;
pause case work12/max_ticks32/pause_after5 ends paused at tick5; quota case
work20/max_ticks7 ends stopped/tick_limit at tick7. Independent observer audits
each. Replay identities/state transitions must match after stripping wall-clock
frame fields/hashes; frame hashes themselves will differ with real UTC time.
Test stale running, no-op timer fabrication, tampered state/identity/journal,
snapshot mismatch and existing-output competing writer rejection. Verify the
observer does not change bytes. Preserve exact source/logs and same-D restore.

This is finite telemetry and operator stop/pause **semantics**, not checkpoint
restart or process health validation. No resume API exists. Durable power-loss
recovery, schema-specific journal/checkpoint crash replay, CPU isolation and
independent off-D backup remain future gates. Required physical power-loss/
isolation/backup verification and separate human authorization still precede
unattended activation. RUNTIME-01 is reported AL01 evidence, not this schema's
restart proof. Maintain science and engineering as independent evidence axes.
