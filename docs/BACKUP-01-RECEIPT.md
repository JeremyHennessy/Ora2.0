# BACKUP-01 — verified independent-drive copy and continuation

## What was completed

The [acceptance contract](BACKUP-01-CONTRACT.md) was frozen at `b4206fc` before
capture/copy/restoration. Live read-only Windows inventory established distinct
physical disks: laboratory SATA disk1, backup NVMe disk0, both NTFS and online.
The human-selected backup root was new, non-reparse and had adequate space.
Active work, staging, restored repositories and the finite world stayed on the
laboratory drive; the other drive stores backups only. No unattended service.

The initial capture preserves40 previously sealed laboratory evidence archives,
including failed attempts and completed integration receipts, exact STORAGE-01
source/snapshot ZIPs, two all-ref Git history bundles, laboratory helpers/launchers/
workspace configuration and approved observer files/recording.110 payload files,
205,881,799 bytes, plus the private manifest were copied to a fresh directory.
Credentials, Git configuration, environments and tool installations were excluded.
The capture's published checkpoints were Ora remote main `0e00d279` and research
remote main `bfbd53c7`; original local research and reviewed local integration were
also preserved privately. Later commits/evidence are outside this snapshot cutoff.
Unpublished local observer and development history remains private in the backup.

## Verification

All111 copied files passed independent PowerShell SHA256/size readback and later
Python SHA256/size verification;42 ZIPs passed complete CRC checks. Both Git bundles
verified, were restored as new bare repositories and passed full object checks.
No fetched research code was executed. The existing operator lock,5GB free-space
floor and300-second per-process deadline remained in force.

The exact reviewed `c9a3fb49` source archive was read from the backup drive;
all211 extracted source files matched the earlier source. Existing Python3.12.10
restored the trusted snapshot into a fresh laboratory directory and independently
verified tick5. Explicit resume retained the original identity and completed tick32.
All33 complete canonical states matched the original independent reference,
including objects, ancestry, resource/work provenance, PRNG and noise cursor.
The exact captured manifest and journal prefix survived. The existing read-only
observer CLI and independent replay passed without modifying the world.

Nine recorded repository/restore/resume/observer subprocesses exited0. The99
guarded historical/shared inputs, captured source files, original evidence and
approved observer files remained unchanged. Both original checkouts stayed clean.
The new private acceptance archive contains22 files and passed byte-exact same-
drive evidence restoration. No backup acceptance failure occurred. Private paths,
physical inventory, exact hashes, manifests, process logs, helper source and raw
restored-world files are retained locally. No natural science sample was consumed.

## What this proves and leaves open

An actual copy on a different physical disk can be read back and used to continue
this finite world's original history exactly. This closes the tested independent-
drive backup gate; earlier same-drive receipts retain their original limitations.
It does not prove complete rebuilding with the laboratory disk absent: Python/
tools still reside there. Both disks share the computer, power and security context;
offline/off-host disaster protection is a separate need.

No physical power-loss/device failure, short-write/fsync/replace syscall fault,
directory-durability guarantee, hostile writer, hardened filesystem/network/process
isolation or strict peak-memory bound was tested. No continuous runtime or pilot
was activated. Snapshot survival is engineering reliability, not self-maintenance,
autonomous origin, reproduction, inheritance, adaptation or evolution.

Next engineering work should separately precommit low-level I/O failure behavior
and restricted process execution. The scientific priority remains a distinct,
finite-accounted generic-startup feasibility candidate with independent controls;
preserve the existing supplied-founder negative baselines and all reserved samples.
