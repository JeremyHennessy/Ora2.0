# Dedicated Computer — Runtime and Integration Plan

**Status:** plan only. No local-machine access has been granted or configured, and no continuous organism process is running.

## Responsibility split

- **GitHub:** source code, reviewed changes, small fixtures, reproducibility manifests, research notes, CI and optional static observer.
- **Dedicated computer:** isolated experiments, resource-heavy workloads, durable run state, checkpoints, local telemetry.
- **AI-Research:** primary-source research and evidence synthesis, **not** a source of unverified training claims.
- **Observer:** read-only visualization and diagnostics. The observer must not own, synthesize, or silently alter experiment state.

## Hardware inventory needed when the machine is available

- OS/version, CPU model/core count, RAM capacity, storage type/capacity and free space.
- GPU model(s) and VRAM, if any; CUDA/ROCm availability if relevant.
- Machine/network isolation, power/restart behavior, available backup disk, local user privileges.
- Intended frequency of experiments and desired concurrent workloads.

Start CPU-only with deterministic small experiments where feasible. Memory and disk capacity help with large experiment histories; a GPU is justified only by measured neural workloads.

## Initial machine layout (conceptual)

- src/: reviewed repository checkout (version-pinned).
- runs/: isolated run IDs and immutable configuration manifests.
- state/: current runtime snapshot and append-only event journal.
- checkpoints/: versioned and validated restart points.
- archives/: compressed results and external backup copies.
- observer/: read-only telemetry generated from validated state.

These are logical storage roles, not files to create until the machine is commissioned.

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

## Recommended commissioning sequence

1. Agree on machine hardware/OS and privacy requirements.
2. Confirm repository visibility and select a narrowly scoped access/deployment route.
3. Build and validate a small deterministic harness **before** enabling long-running work.
4. Set up restricted runtime, storage quotas, checkpoints and integrity tests.
5. Run a restart/restore rehearsal using a non-production experiment.
6. Start bounded background experiments and separately expose read-only telemetry.
7. Expand resources only after the actual workload justifies it.

## Local-versus-cloud decision

A dedicated local workstation or server is an excellent first always-on environment when power, cooling, networking, security and backups are adequate. Cloud or GPU rental may eventually be useful for burst workloads, but it is not a prerequisite for the first artificial-life experiments.
