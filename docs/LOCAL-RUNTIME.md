# Dedicated Computer — Runtime and Integration Plan

**Status (2026-10-08):** Local Codex **reports RUNTIME-01 Windows process-exit/restart acceptance PASSED** at Ora2.0 commit `205e0030de07986ef4244f38f01890bdf62d5a10`, Python 3.12.10, with all 126 tests and the three crash points, exact byte replay and D: restore verified. This is **reported local evidence**, not a direct cloud inspection of D:. [See Codex-reported acceptance receipt](RUNTIME-01-WINDOWS-ACCEPTANCE-2026-10-08.md). Still no continuous digital organism, hardened sandbox, off-D backup, power-loss-tested restart or automatic code execution.

## Responsibility split

- **GitHub:** source code, reviewed changes, small fixtures, reproducibility manifests, research notes, CI and optional static observer.
- **Dedicated computer:** isolated experiments, resource-heavy workloads, durable run state, checkpoints, local telemetry.
- **AI-Research:** primary-source research and evidence synthesis, **not** a source of unverified training claims.
- **Observer:** read-only visualization and diagnostics. The observer must not own, synthesize, or silently alter experiment state.

## Machine inventory (local Codex handoff, not independently verified here)

- Windows 11 Home 25H2 (build 26200.9457), Dell XPS 8950, Intel i7-12700K / 20 logical processors, **128 GB RAM**.
- NVIDIA RTX 3070 (**8 GB VRAM**) present, **not needed or enabled for the current CPU-based experiment**.
- C: approximately 1 TB NVMe SSD; **D: approximately 1 TB mechanical disk** is the authoritative local lab drive.
- Git/GitHub Desktop/VS Code/Python extension installed; Python **3.12.10** at `D:\OraLab\tools\Python312`; virtual environment at `D:\OraLab\src\Ora2.0.venv`.
- Both Ora2.0 and the **private** AI-Research repos reportedly cloned with clean working trees at handoff; verify **reviewed HEAD** before applying subsequent GitHub work.
- No BIOS changes, paid services, model installs, self-hosted runner, direct inbound machine access or GPU requirements for the current gate.
- A distinct physical/offsite backup medium was **not available** at handoff. Copies elsewhere on D: will not survive mechanical D: failure.

## Reported current D: lab layout (not independently inspected)

- `src/`: Ora2.0 and AI-Research clones, plus a separate Ora2.0 Python virtual environment.
- `runs/`: historical experiment run folders, source snapshots and their checkable receipts. The **RUNTIME-01 pilot** also stores its own run-scoped checkpoint and journal here, separate from all scientific runs.
- `state/`: **operator lock only** at handoff; **not** a running organism state store.
- `checkpoints/`: reserved for a future verified continuous recovery system (empty/unverified, distinct from RUNTIME-01's run-local synthetic checkpoints).
- `archives/`: compressed experiment outputs and checksums (**local D: only**, not off-drive protection).
- `backups/`: on-D: restoration copies, Git bundles and configuration backups; cannot mitigate D: failure.
- `observer/`: generated read-only local reports; not a state authority.
- `logs/`: setup, hardware and restoration receipts; `tools/`: Python and existing manual `oralab.py` helper.

**Reported existing paths:** `D:\OraLab\README.txt`, `tools\oralab.py`, and manually launched `Open Lab.cmd`, `Lab Status.cmd`, `Run Calibration.cmd`, `Fetch Research Updates.cmd`, `Apply Reviewed Updates.cmd`.

The helper reportedly provides 5 GB minimum free space, a single-operator lock, five-minute command timeout, checked source archive and replay/restore. Its **source and effects have not been inspected from this chat**. Any new runtime operation must be manually reviewed and integrated with those safeguards by Codex; GitHub CI alone is not evidence that `oralab.py` invokes RUNTIME-01.

## Persistence and recovery contract

1. Simulation time is tracked as an internal step, not inferred from wall-clock heartbeats.
2. Only one authoritative writer changes an experiment's world state.
3. Journal transitions with run ID, sequence, input/config identity and checksums.
4. Write checkpoints atomically, then validate by reloading and replaying.
5. On crash/reboot, resume from the last valid checkpoint plus recoverable journal. Never silently re-seed and call it the same organism.
6. Provide an explicit operator pause, disk/CPU quotas, run budget, and shutdown/restart behavior.
7. Back up durable state separately from source code; verify restoration on a test copy.

These guarantees must be demonstrated by tests before they are described as operational.

## Security and remote access

- Use a dedicated unprivileged OS account with no access to personal files, unrelated repositories or sensitive LAN hosts.
- No public inbound machine access; use a restricted and auditable remote-management path.
- Keep credentials in the machine's protected secret store, never a public repository, GitHub issue, log, or chat message.
- The repository was **public at the time of this plan**. A public GitHub repository is not a safe place to enable a self-hosted Actions runner that might execute code from untrusted contributions. Do not install such a runner until repository visibility, workflow triggers, permission scopes and threat model have been reviewed.
- Prefer reviewed, signed or pinned code deployments rather than executing arbitrary pull requests or downloaded research code.
- The organism sandbox should have no external network, machine administration, or code deployment privileges by default.
- A repository URL or an offer of access alone does not create a direct computer connection from this conversation. A supported, explicitly configured integration will be needed.

## Commissioning evidence gates (current status)

1. **Locally reported complete:** hardware/OS inventory, D: layout, Git clones, Python environment and manual launchers; see [Desktop Codex handoff](DESKTOP-CODEX-HANDOFF-2026-10-08.md).
2. **Locally reported complete:** bounded AL01-CAL verification and archive-copy restoration, 90 tests with Python 3.12.10; not checkpoint recovery.
3. **GitHub-hosted pass:** RUNTIME-01 immutable source/journal/checkpoint replay and injected process termination, Python 3.12.10, 126 passing tests on approved source.
4. **Codex-reported local Windows pass:** the identical reviewed Git commit, 126 passing tests, intentional exits 77/78/79 with exact recovery, corruption and concurrent-writer rejection, restored archive, and operator lock/space/300s timeout checks. The local report and raw hashes remain on D:, **uninspected by cloud ChatGPT**. See [acceptance receipt](RUNTIME-01-WINDOWS-ACCEPTANCE-2026-10-08.md).
5. **Next implementation stage:** continue [CLOSURE-02](CLOSURE-02-PROTOCOL.md) as a **separate bounded scientific experiment** via reviewed GitHub changes. Do **not** generalize the AL01 one-reactor checkpoint schema to spatial/lineage worlds without new tests.
6. **Still not implemented/verified:** continuous worker, unattended scheduling, power-loss recovery, hardening of runtime isolation, real organism state, independently durable off-D backups. Do not activate these by implication.

## Local-versus-cloud decision

Use the existing **owned D:-based local workstation** for bounded, operator-reviewed experiments. Paid cloud/GPU rental, metered APIs, subscriptions and self-hosted public GitHub runners are **out of scope under the user's current requirements**. Do not enable always-on operation until Windows checkpoint-restart, least-privilege execution, stop controls and independent physical backups are addressed in separate evidence gates.
