# RUNTIME-01 — Windows process-restart acceptance (Codex-reported)

**Receipt date:** 2026-10-08. **Evidence status: externally reported local verification**, not a cloud-independent reading of the Windows filesystem, execution log, ZIP contents, or checksum manifest.

## Source identity

- Reviewed Ora2.0 Git commit: `205e0030de07986ef4244f38f01890bdf62d5a10` (this revision also independently confirmed as `main` in GitHub when the report was received).
- Reported Windows Python: **3.12.10**, existing isolated D: environment. Clean local Git working tree.
- Independently verified GitHub hosted-CI workflows at that same source SHA: `37803993259` (RUNTIME-01, 126 tests) and `37803993335` (regression), both successful. GitHub is **not Windows** and does **not** prove local facts.
- Local operator files and proof remain on D: under `runs/runtime01-verification-20261008T125751-205e0030/`, specifically `REPORT.md`, `verification.json`, and an evidence ZIP under `archives/`. Full checksums and raw files are **not imported into this public repository**.

## Local Codex's test report (not independently replayed here)

| Requirement | Codex-reported observation | Assessment |
| --- | --- | --- |
| Python environment | 3.12.10; previous installation used | Reported pass |
| Git source / local working tree | Exact reviewed SHA, clean tree | Reported pass |
| Regression | 126/126 tests, exit 0 | Reported pass |
| Fault at step 37 | Deliberate exit 77; resumed/verified with 0 | Reported pass |
| Fault at step 43 | Deliberate exit 78; resumed/verified with 0 | Reported pass |
| Fault at step 50 | Deliberate exit 79; resumed/verified with 0 | Reported pass |
| Byte-identical authoritative output | All four run files matched cold uninterrupted Windows reference for every resumed case | Reported pass |
| Corruption / wrong source / simultaneous writer | Rejected with exit 2, no unexpected mutation | Reported pass |
| Local archive restoration | On-D recovery and verification | Reported pass |
| Existing operator safeguards | Operator lock, minimum-space rejection, actual 300-second timeout | Reported pass |
| Windows-specific failures | None reported | Reported pass |

The report was supplied by the user in conversation. The cloud assistant **cannot open `D:\OraLab` or verify the absolute Windows paths**. No independent local checksums were pasted into this conversation, so this note makes no claim to have reproduced or validated their actual values.

## Scope of demonstrated behavior

**Accepted for the next bounded step, conditional on Codex's report being accurate:** a manually launched, process-exit-recoverable AL01 *single-reactor test fixture*, with byte-identity checks on the same desktop/storage device. Historical failed outcomes and scientific experiments remain unchanged.

**Still missing:**
- Independent physical/off-D backup and test restoration after losing D:;
- actual sudden machine power-loss / unclean controller cache recovery evidence;
- hardened process/container/OS privilege isolation;
- manual approval before new Git commits can run locally;
- generic checkpoint adapters for AL02 heredity, AL03 ecology or CLOSURE spatial worlds;
- a continuous, unattended organism runtime or any claim of digital life.

**Decision:** complete RUNTIME-01 as a *bounded process-exit recovery gate*, not as a general persistent-runtime deployment. Do **not** enable a GitHub self-hosted runner, automatic pull/apply, scheduler, browser-agent control of the local computer or continuous simulation. The next justified scientific step is an **independently preregistered CLOSURE-02 functional boundary test** with new seeds, cost/flux controls and no misleading shell-based survival score.

This receipt is separate from the approved local Codex files. Do not overwrite or delete them, or expose sensitive local logs in a public PR.
