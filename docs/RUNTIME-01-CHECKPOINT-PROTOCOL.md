# RUNTIME-01 — Bounded checkpoint, journal and crash-recovery protocol

**Preregistered engineering test (2026-10-08).** This is an **infrastructure** experiment, not an artificial organism, new biology result, autonomous runtime or claimed continuous simulation. Complete this gate before starting unattended digital evolution. No paid hosting, subscriptions, metered services, LLM, OpenAI API, Docker, WSL, or background cloud machine.

## Source and handoff

- GitHub engineering baseline: Ora2.0 `be423cf1958591a6dd3e93115796231ef5f862c5`. Existing AL01-CAL, AL02, AL03, AL07 and CLOSURE source and outcomes must **not** be edited.
- Local Codex **reported** Windows 11 25H2, Dell XPS 8950 / i7-12700K / 128 GB RAM / RTX 3070, `D:\OraLab` operator-controlled directory and Python 3.12.10, with 90 original tests passed, exact AL01-CAL replay and local archive restoration. **Cloud ChatGPT has not accessed or verified that desktop.**
- Both local repositories were clean at their reported handoff Git revisions. GitHub `main` has advanced since then. Apply reviewed Git changes only with the **existing manual** lab helper; never turn on auto pull, unreviewed execution, a self-hosted GitHub Actions runner, or GitHub Actions access to the desktop.

## Why AL01-CAL as a fixture

`experiments/chemical_calibration.py` already exports `Protocol`, `Reactor`, `tick`, `assert_valid` and uses seeded `random.Random`. RUNTIME-01 **imports** that code but does not alter its calibrated science. The pilot evolves a *single* reactor by exactly `N` ordinary fixed-`variant` ticks, from `S=35, A=10, B=10, W=0`; unlike AL01-CAL's 4-branch, damage-after-warmup research design, this is a **new recovery fixture only**, not a replay of the 29/32 scientific result.

### Immutable run identity

Choose a unique directory for each run under `D:\OraLab\runs\checkpoint-pilot-<run-id>`. Record at creation:
- SHA-256 of the exact AL01-CAL source module and checkpoint runner;
- exact 40-hex-character reviewed Git commit, Python version and declared model parameters;
- seed, variant (`intact`, `feedback-knockout`, `inert`, `starved`), integer step horizon `N`, checkpoint cadence, manifest format/version;
- canonical JSON manifest hash. Once committed, **mismatch refuses** to resume. No overwrite, silent reinitialization or “best effort” state repair.

Fixture acceptance: `seed=1000`, `variant=intact`, `steps=120`, `checkpoint interval=10`. Other development-only seeds may be used for unit tests. Do not change this acceptance sample after viewing outcomes.

## Persistence contract

1. Exactly **one** host-side writer per run directory (cross-platform OS file lock, auto-released when a process exits).
2. Simulation time is **the numeric tick counter**; machine clock, UI and heartbeats cannot advance world state.
3. Each computed tick is first validated by AL01 molecule conservation, then represented as **one canonical JSONL journal record** with monotone sequence, previous record hash, manifest identity, full state counters and PRNG-state checksum. Append, flush and **fsync journal** before calling the transition committed. Do not silently skip or duplicate transitions.
4. Snapshot contains state, entire Python Mersenne-Twister PRNG state, current journal chain hash, source/manifest identity and integrity hash. Write a temporary file, flush/fsync, atomically `os.replace` the checkpoint. Call this **process-crash atomicity** only; actual sudden power loss, controller cache flush, hardware fault tolerance and Windows filesystem guarantees still require separate evaluation.
5. Recovery rejects truncated/unparseable journal, broken hash chain, wrong or missing steps, incompatible interpreter/source, invalid/duplicated checkpoint, invalid molecule ledger, and any discrepancy between journal and checkpoint.
6. Resume **from last valid checkpoint** and *deterministically replay only the committed journal suffix* using the frozen source to validate its state and PRNG checksums. A tick computed but **not journal committed** at a crash is replayed on restart. A journal-committed tick cannot be executed twice in durable history.
7. A completed run has immutable final receipt with source, seed, final tick, state, PRNG and journal-head hashes. Rerunning the same command must verify the completion and leave all authoritative data **byte-identical**.
8. All scripts are one-shot, manually invoked and CPU-only. No networking, Git writes, new model runner, arbitrary-code virtual instructions, service scheduler, observer authority or desktop auto-deploy.

## Fault injection acceptance

In separate *fresh* directories, produce a full uninterrupted 120-step control and these **deliberately interrupted subprocess** cases:
- Kill just after computing step 37, **before** journal commit; resume using checkpoint + committed journal.
- Kill just after journal fsync at step 43, **before** periodic checkpoint; resume and replay journal tail.
- Kill after checkpoint replace at step 50, before completion receipt; resume cleanly.
- For every case, final state, RNG hash, event count, monotone step sequence, journal hash and canonical receipt must equal the uninterrupted control **byte-for-byte** (except explicitly separate local operator reports outside the authoritative run).
- A second concurrent writer must fail without modifying state. Mismatched Git SHA/source/Python/seed/horizon must fail closed.
- Corrupt a *copy* of the journal and another copy of checkpoint; detect errors, produce no “recovered” success, do not mutate original run.
- Test AL01 conservation on every resumed step, final run idempotence and deterministic re-execution using `--verify-only`.

**Important:** `--fault-step`/fault-stage are test-only operator interventions, not an autonomous fault service or a normal execution schedule.

## Tests and success gates

**GH acceptance (not desktop acceptance):** new deterministic fixture/unit tests plus all existing repository tests pass on pinned Python **3.12.10** in a read-only GitHub-hosted job, including subprocess crash injections, corruption/mismatch tests, last-valid-checkpoint replay and complete output receipts.

**Local Codex acceptance (independent and mandatory):** after manual review/pinned checkout only, run identical bounded tests using `D:\OraLab\tools\Python312\python.exe` and `D:\OraLab\src\Ora2.0.venv` as actually verified by Codex. Run test pilot entirely on D:, explicitly interrupt/restart a subprocess, repeat from a separate fresh directory, compare hashes, verify local helper's 5-minute limits and D: free-space/operator lock, and preserve run receipt and external-reviewed SHA. **Do not use the GPU or alter BIOS/power settings** for this test. No self-hosted runner.

**Do NOT call this milestone verified on desktop based solely on GitHub CI.** Windows file locks, subprocess termination, disk flushing, actual permissions and storage behavior need local evidence. The local Codex may adjust only platform-level plumbing under separately reviewed changes, and must preserve original experiments.

## Explicitly out of scope

Continuous organism/process, a 24/7 service, watchdog, time-based heartbeats, scheduler, GUI observer upgrade, backoff/retry automation, a remote/cloud command channel, an OpenAI API model, source/self-modifying code, external user data, network actions, GPU acceleration and secure independent off-drive backups.

D: archives protect against some mistaken deletion but **not D: physical failure**. A separate physical/offline backup location remains an independently tracked deficiency. Never report verified drive-failure recovery on the basis of two copies on D:.

**Pass outcome means:** one *bounded deterministic simulation* can resume after tested **process exits** using a validated checkpoint and durable event suffix. It is **not** proof of crash-safe persistence after machine power loss or evidence of living digital organization.
