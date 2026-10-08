# HEARTBEAT-02 — Windows process-exit continuity acceptance

2026-10-08. Engineering fixture only; no new independent science worlds.
Frozen [contract](HEARTBEAT-02-CONTRACT.md) commit
`1a14b7b`; executed reviewed commit
`1b3d57b8fb2421eda06f7039d53801f3beb8db2f` on existing Windows Python3.12.10.
HEARTBEAT-01, RUNTIME-01, scientific laws/data and both original clones preserved.

## What now works in this finite fixture

Explicit restart continues the same authored work counter and original total
tick budget. Identity binds world/configuration/source-file hashes/Python and
exact declared Git revision. A fully audited committed journal is authoritative;
lagging or missing checkpoints can be rebuilt. Corrupt/ahead/non-prefix snapshots
and partial/corrupt history fail closed without byte changes. Stable OS writer
lock rejects a real competing resume; process exit releases it without PID-based
lock deletion. Independent observer reads only and distinguishes journal state,
checkpoint lag, UTC age and unverified process health.

**226 tests passed**, exit0,102.383seconds, from archived source. Eight new test
methods cover actual exits, repeated recovery, pauses, terminal idempotence,
missing/lagging snapshots, source/config/world/Python rejection, coherently
rehashed semantic forgeries, stale journal views, real competing processes and
the32-resume cap. Existing science and runtime regression tests also passed.

Separate manual acceptance preserved **11 forced process exits**:

| Fault boundary | Exit | Energy case | Quota case |
|---|---:|---|---|
| Next state computed, before journal commit |77|tick5; journal remains4|tick7; journal remains6|
| After complete journal flush/fsync |78|committed5; checkpoint4|committed7; checkpoint6|
| After pending checkpoint flush/fsync |79|committed5; checkpoint4|committed7; checkpoint6|
| After checkpoint replacement |80|committed5; checkpoint5|committed7; checkpoint7|

These eight single-fault histories plus one history interrupted sequentially at
5/pre_commit,6/post_journal,7/post_pending account for11 process exits. The latter
completed under the same run identity across three explicit resume epochs.
All original committed journal bytes remained a prefix after every recovery.

**11 completed comparison histories matched uninterrupted authoritative state
sequences byte-for-byte:** eight single faults, one triple-fault history, one
pause/resume and one recovery after a competing lock was released. These are
correlated engineering scenarios, not11 independent scientific samples.
Energy referencework12/max_ticks32 stopped at12; quota referencework20/max_ticks7
stopped at7; emptywork0 stopped at0. Completed resumes were byte-idempotent.
Pause at5 retained its state and subsequently reached12, rather than replacing
the world. Source/work mismatch, partial tail and held lock exited2; all explicit
resumes and observer audits exited0. No missing/double counter tick or work.

Byte equivalence applies to the canonical tick0..endpoint **state sequence**.
Wall times, invocation epochs, lifecycle-only frames and journal hashes differ
and are preserved rather than described as identical. This is simpler evidence
than a stochastic population checkpoint with an independently restored PRNG.

## Preserved evidence and failures

Local run:
`D:\OraLab\runs\heartbeat02-checkpoint-20261008T201319Z-1b3d57b8`.
Includes source ZIP, manual acceptance helper and lab guard source, full tests,
all process exits/audits, canonical states, pre-resume copies and negative files.
Manual helper:`D:\OraLab\tools\verify_heartbeat_checkpoint.py`.

- Source ZIP SHA256:`671bcd865414dfd36e5b3714a32d1f1661ac366afcb72d42d190b063b6b830e0`.
- Energy states:`d68f6ee2f0e72d8f100485e40f0cf9df50c02153e1a934c714fd5b637c2a717c`.
- Quota states:`71c2a6d721a8935b96cc0a0055305e943eaa65f2b62d39149bd9bee33a09715e`.
- Evidence archive SHA256:`202b0f84030570aa8e18c9d1bd380c1f5c1ed0ef8000af2668b0e81f0b359389`.
- **210 archived files restored byte-for-byte on the same D: drive**.

Two earlier development failures remain in the archive. The first invocation
used the sandbox's default C: temporary folder and failed directory permissions;
it was rerun with explicit D: TMP/TEMP. The first D: focused run passed six
methods but the competition test tried reading a Windows-locked byte. The test
now compares unlocked files during ownership and every byte after release;
eight focused methods passed in43.251seconds. Neither failure justified changing
counter physics or deleting prior evidence. Final pinned acceptance passed.

## Limits and next decision

No physical power-loss, disk-write interruption, hardware failure or independent
off-D backup was tested. Flush/fsync and replacement alone do not establish
those guarantees. No OS CPU/memory/security isolation, population/PRNG
continuity, automatic restart, service, external API or unattended activation.
The counter is an authored engineering object, not evidence of self-maintenance,
evolution, learning or life. RUNTIME-01's historical full Windows receipt remains
reported AL01 evidence; this acceptance does not relabel it as a new full rerun.

Next science priority is the separately frozen paid material-turnover/composition
feasibility/opportunity comparison. [Pass17 intake](RESEARCH-INTAKE-PASS17.md)
sharpens producer/removal, specific-material/generic-resource rescue and eventual
descendant reconstruction comparisons. Pass18 main472ab24c was discovered at
final integration check; its full notes95..99/ledger and exact green CI were
reviewed. Component survival, relationship loss and descendant reconstruction
remain distinct; current plan incorporates this without rerunning or altering
the accepted counter. Next engineering step is an independently
audited finite stochastic-state adapter once its immutable scientific law/state
schema is selected, including PRNG/object-ID continuity. Keep the unchanged AL01
checkpoint implementation as an existing reference rather than claim a second
new discovery. Backup/power-loss/isolation gates and separate unattended approval
remain outstanding; no continuous world is enabled by this receipt.
