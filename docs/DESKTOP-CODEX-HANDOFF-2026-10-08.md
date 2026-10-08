# Desktop Codex handoff — Ora2.0 RUNTIME-01

**Historical commissioning instructions — now locally reported PASS.** Local Codex completed these RUNTIME-01 Windows acceptance tests at source `205e0030de07986ef4244f38f01890bdf62d5a10` with Python 3.12.10 (126 tests, controlled exit 77/78/79, exact resumed files, failures rejected, on-D restoration, operator safeguards). Cloud ChatGPT did not inspect the D: report; see [recorded Codex verification receipt](RUNTIME-01-WINDOWS-ACCEPTANCE-2026-10-08.md). **Do not re-run the commissioning instructions unnecessarily.** They remain here for provenance and later regression testing.

**2026-10-08 · Operator-controlled Windows execution, not a request for unattended deployment.** This is the actionable next desktop stage, based on the user's reported local Codex setup plus a separately verified GitHub-hosted checkpoint prototype. Cloud ChatGPT **has not opened, scanned or commanded** the user's computer or any file under D:.

## 1. Do not repeat setup

The user/local Codex reports an existing lab:
- Windows 11 Home 25H2, Dell XPS 8950, Intel i7-12700K (20 logical), 128 GB RAM, RTX 3070 (8 GB); GPU not required.
- Authoritative project storage **D:\OraLab** on an approximately 1 TB HDD; C: 1 TB NVMe is not the authoritative lab.
- Python **3.12.10** at **D:\OraLab\tools\Python312**; virtual environment **D:\OraLab\src\Ora2.0.venv**.
- Working clones in **D:\OraLab\src\Ora2.0** and **D:\OraLab\src\AI-Research** (private). Both clean at handoff; local revisions were Ora2.0 **851270664802c0146d2998921bc746b96fceaac9** and AI-Research **37ec45027e2bfd62030fb9c6c1840294c35f366a**.
- Manually operated **D:\OraLab\tools\oralab.py** and **D:\OraLab\README.txt**. Launchers **Open Lab.cmd**, **Lab Status.cmd**, **Run Calibration.cmd**, **Fetch Research Updates.cmd**, **Apply Reviewed Updates.cmd** exist.
- Bounded original AL01-CAL tested with 128 records / 7,680 events, 29/32 recovery under the intended intact catalyst; all controls 0/32; exact repeat, SHA, copy/restore evidence stored at **D:\OraLab\runs\al01-cal-20261008T144038067238Z-85127066**. Those are local Codex **reported** facts, not independently verified remotely.
- No Ollama, Docker, WSL, paid hosting, metered API, OpenAI API, persistent agent process or self-hosted GitHub Actions runner required.

**Do not reinstall** tools, remove local configuration, change BIOS/Windows power plan, alter unrelated software or auto-fetch/execute GitHub changes.

## 2. What changed remotely — manual review is required

At the start of this stage, GitHub Ora2.0 main was **be423cf1958591a6dd3e93115796231ef5f862c5** (17 commits ahead of local handoff; no branch divergence); AI-Research main was **1ea95c4bd0eb883f03e93f1e0912d16aacd5a108** (11 commits ahead). The new RUNTIME-01 development lives on GitHub branch **runtime/checkpoint-pilot-20261008**, built without editing existing AL01/AL02/AL03/AL07/CLOSURE sources.

**These are historical comparison receipts.** Check current remote SHA and GitHub workflow statuses again when local work starts; refs can change as research continues.

The reviewed source includes:
- [Frozen acceptance protocol](RUNTIME-01-CHECKPOINT-PROTOCOL.md).
- **experiments/checkpoint_pilot.py**: fixed AL01 reactor, immutable source identity, append-only hash-chained full-state journal, atomic checkpoint (includes RNG), process-locking, deterministic suffix replay and completion verification.
- **tests/test_checkpoint_pilot.py**: native abrupt process exits, no duplicate ticks, corruption and source mismatch rejection, deterministic replay and lock tests.
- GitHub-hosted **.github/workflows/runtime01.yml** (Python 3.12.10) is permitted to test the repository itself but **cannot connect to the desktop**.
- Updated [LOCAL-RUNTIME](LOCAL-RUNTIME.md). No Git commit is automatically executed on D:.

Before applying updates, manually use the **existing** fetch / apply-reviewed-update workflow, inspect changed files, verify the selected commit, and ensure **git status is clean**. Do **not** substitute git pull + auto-run for manual approval. AI-Research is a read-only scientific source for this stage; do not execute unknown research paper code.

## 3. Review these safety and operation boundaries first

1. Open **D:\OraLab\README.txt** and **D:\OraLab\tools\oralab.py** to verify its existing operator lock, 5 GB free-space check, per-command **5-minute** timeout, snapshot verification, backup manifest and output-only-on-D behavior.
2. Adapt/wrap RUNTIME-01 with those existing local-only safeguards **if necessary**. Cloud GitHub does not inspect this helper. Avoid making unreviewed changes to either repository: document local helper differences separately and propose GitHub patch review if needed.
3. The new pilot has its **own run-local OS writer lock**. That is not a hardened sandbox or replacement for the already reported global `oralab.py` operator lock.
4. No network or external tool calls are issued by the pilot; however, local execution of Python from a Git clone **is not a hardened process sandbox**. Use the existing least-privilege lab account/filesystem restrictions, don't run unreviewed PRs.
5. Each test uses a **brand-new run directory** under `D:\OraLab\runs`, never the original AL01 result folder. The pilot itself writes its checkpoint and journal inside that run-specific folder, not directly into the current reserved `D:\OraLab\checkpoints` or `D:\OraLab\state`.
6. The remote GH Linux proof is **not** evidence of Windows msvcrt file-lock behavior, Windows atomic rename behavior, Windows power-failure durability, a recovery daemon or persistent life. No off-D independent backup yet exists.

## 4. Manual PowerShell acceptance script (review before execution)

Run from a PowerShell terminal opened under the existing D: lab setup. This is a **finite, offline test**, not a scheduled job. The commands below assume the reported venv is still present and the reviewed source is checked out:

```powershell
$repo = 'D:\OraLab\src\Ora2.0'
$python = 'D:\OraLab\src\Ora2.0.venv\Scripts\python.exe'
Set-Location $repo
git status --short
$revision = (git rev-parse HEAD).Trim()
& $python --version
& $python -W error::ResourceWarning -m unittest discover -s tests -v

# Do NOT reuse previously approved AL01-CAL or other historical folders.
$root = 'D:\OraLab\runs\runtime01-local-check-20261008'
$shared = @('--revision', $revision, '--seed', '1000',
            '--variant', 'intact', '--steps', '120',
            '--checkpoint-every', '10')

# Cold uninterrupted reference, separate folder.
& $python -m experiments.checkpoint_pilot --run-dir "$root\cold" @shared
& $python -m experiments.checkpoint_pilot --run-dir "$root\cold" @shared --verify-only

# Each fault is a NEW run and is intended to abruptly exit with 77 / 78 / 79.
& $python -m experiments.checkpoint_pilot --run-dir "$root\precommit" @shared --fault-step 37 --fault-point pre_commit
if ($LASTEXITCODE -ne 77) { throw 'Expected deliberate process exit 77' }
& $python -m experiments.checkpoint_pilot --run-dir "$root\precommit" @shared
& $python -m experiments.checkpoint_pilot --run-dir "$root\precommit" @shared --verify-only

& $python -m experiments.checkpoint_pilot --run-dir "$root\afterjournal" @shared --fault-step 43 --fault-point post_journal
if ($LASTEXITCODE -ne 78) { throw 'Expected deliberate process exit 78' }
& $python -m experiments.checkpoint_pilot --run-dir "$root\afterjournal" @shared
& $python -m experiments.checkpoint_pilot --run-dir "$root\afterjournal" @shared --verify-only

& $python -m experiments.checkpoint_pilot --run-dir "$root\aftercheckpoint" @shared --fault-step 50 --fault-point post_checkpoint
if ($LASTEXITCODE -ne 79) { throw 'Expected deliberate process exit 79' }
& $python -m experiments.checkpoint_pilot --run-dir "$root\aftercheckpoint" @shared
& $python -m experiments.checkpoint_pilot --run-dir "$root\aftercheckpoint" @shared --verify-only

# All authoritative files must have identical hashes ACROSS these four
# folders on this one Windows machine with the same reviewed source.
$files = @('manifest.json','journal.jsonl','checkpoint.json','receipt.json')
foreach ($runName in @('precommit','afterjournal','aftercheckpoint')) {
    foreach ($file in $files) {
        $expected = (Get-FileHash "$root\cold\$file" -Algorithm SHA256).Hash
        $actual = (Get-FileHash "$root\$runName\$file" -Algorithm SHA256).Hash
        if ($expected -ne $actual) {
            throw "Mismatch: $runName / $file"
        }
    }
}
'RUNTIME-01 PASS: bounded Windows process exit/restart is deterministic'
```

**Operator caution:** The script uses a fixed folder name as an illustrative *new* test directory. Before running, choose a unique run ID that does not exist, and verify 5 GB free D: space. The script does **not** independently enforce `oralab.py`'s global operator lock or 5-minute timeout; local Codex must wrap it under those established protections. The code in the repo applies its own per-run writer lock and an upper limit of 10,000 ticks, but that is **not** a whole-machine resource quota.

**Cross-OS hashes:** Linux-vs-Windows manifest bytes may differ because the manifest records platform identity; the required comparison is *four Windows runs on the same local reviewed source*, not byte equality of Windows and Linux archive files. If different run configurations are used, equivalence is no longer the valid acceptance claim.

## 5. Local Codex validation beyond the happy path

In **copies** of the completed synthetic run only, verify:
- truncated or modified `journal.jsonl` is rejected (no silent repair);
- missing or altered `checkpoint.json` is rejected;
- a wrong `--revision`, source hash, Python version or changed seed/horizon refuses resume;
- an unfinished interrupted run refuses `--verify-only` until recovery completes;
- two simultaneous writers to the same pilot directory cannot both proceed;
- a completed run re-verifies as idempotent without adding a step;
- a copy/restore of the *checkpoint-pilot run directory* is verified after restore using unchanged reviewed code;
- the original **AL01-CAL** scientific experiment still passes its 29/32/0/0 calibration under the same source revision after these tests, without modifying its historical data.

Check Windows filesystem behavior under controlled **process** termination. Do **not** claim power-loss durability unless a separately approved and fully backed-up physical test occurs. Never jeopardize existing lab storage to demonstrate a power failure.

## 6. Desktop acceptance matrix

| Test / evidence | Pass condition | Where verified |
| --- | --- | --- |
| Git/source/venv | Reviewed exact commit, clean tree, Python 3.12.10 | Local Codex |
| Regression | All original and new tests pass, **126 expected at reviewed RUNTIME-01 branch** | GitHub already passed; repeat locally |
| Exact cold run | 120 journal steps, zero AL01 ledger residual, final verified receipt | Local Codex |
| Precommit crash (37) | Exit 77; restart equals uninterrupted run byte-for-byte | Local Codex |
| Post-journal crash (43) | Exit 78; journal suffix replay; no duplicated transition | Local Codex |
| Post-checkpoint crash (50) | Exit 79; resume from validated snapshot | Local Codex |
| Mismatch/corrupt data | Fail closed; no automatic reset, truncation, rescue | Local Codex |
| Single writer | Second concurrent attempt rejected; OS lock released after crash | Local Codex |
| Full source/copy audit | Immutable manifest, exact source SHA, journal chain, final RNG/state hashes | Local Codex |
| Restore from D: archive | Verified restoration on copy, not off-drive redundancy | Local Codex |
| Integration with existing operator controls | 5 GB, timeout, global one-operation rule still enforced | Local Codex |
| Auto-run restrictions | No self-hosted Actions runner, no scheduled services, no unattended Git execution | Both; locally confirmed |
| Durable backup against D: failure | **NOT YET AVAILABLE; remains open risk** | Future external backup |
| Unattended/real-time continuous simulation | **NOT IMPLEMENTED** | Future separate stage |

**Any failed required Windows test blocks promotion to persistent runtime.** Record the precise source SHA, Python version, run IDs, original and restored hashes, expected fault codes, and failed checks. Do not mask a failed test with a rerun that overwrites its previous result.

## 7. What to return to the Ora2.0 development chat

Give a concise verification receipt containing:
1. reviewed Git SHA, `git status --short` result, Python executable/version and D: free space;
2. pass/fail and total tests, cold and each crash/recovery exit code;
3. final journal and receipt hashes from cold/three restarts and archived restore;
4. any material Windows-only deviations, code patch/PR links if made, and which are unmerged;
5. evidence that existing `oralab.py` operator lock, free-space and time limit still apply;
6. **separate outstanding blockers:** no independent off-D backup, no hard power-cut recovery, no 24/7 worker, no hardened sandbox or entity autonomy.

Do not paste secrets, private repo credentials, account IDs, private hostnames, file-system access tokens or a full personal hardware inventory into a public GitHub issue. Local Codex can attach a redacted, checksum-indexed receipt to the secure lab history and summarize it to the chat.

## 8. Next stage only after local pass

Once Windows crash/restart and exact archive restoration are verified, choose **one** experiment for optional checkpoint integration, and preregister its state/replay semantics; do **not** infer that AL02 heredity, AL03 ecology or CLOSURE chemistry are resumable merely because the AL01 one-reactor fixture is. An always-on host, autonomous world self-maintenance, real power-loss tests, GPU use and networked observer are **separate future decisions**.

The independent scientific priority remains the [CLOSURE-02 cost-controlled boundary-function question](CLOSURE-02-RESEARCH-DESIGN.md), but it does not justify bypassing the missing reliability gate or adding a paid service.
