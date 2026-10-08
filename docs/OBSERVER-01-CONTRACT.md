# OBSERVER-01 — repair heterogeneous local receipt display

2026-10-08. Before implementation: local oralab.status assumes every manifest
has run_id/status/source_revision. Read-only inventory found 26 of 27 manifests
use newer revision-based receipt formats; the old page is stale. Fix this
concrete schema mismatch without changing scientific histories or launcher UI.

Pure standard-library module collects immediate run manifests, bounded to 1MiB
each/1,024 entries, rejecting symlink/reparse inputs and duplicate JSON keys.
Malformed/unsupported receipts become visible error rows, not missing outcomes
or crashes. Normalize run ID from explicit run_id or containing directory;
source from source_revision or revision. Keep the complete original receipt,
hash/path, reported status, tests, source and origin of fallback labels.
Unknown/invalid source/status remains unknown; passing a reported test suite
does not independently audit an experiment or establish science/health.

Read-only inventory and HTML rendering must never modify run evidence or execute
source, fetch updates, follow run-defined paths, import a simulation, resume it
or infer a running process from heartbeat/status. Escape every displayed value.
Reports retain the existing local page title/theme/table and Lab Status.cmd
interaction; show original checkout heads separately from receipt source heads.
Explain bounded checkpoint evidence is reported, continuous operation disabled,
and backup/power-loss/isolation unverified. No network server or UI redesign.

Before deployment reproduce the original failure with copies under a disposable
laboratory root, verify mixed legacy/new/malformed receipts, HTML injection,
source/status ambiguity, bounded reads, read-only hashes and stable replay.
Archive the prior oralab.py and status/index snapshots. Manual reviewed deployment
may copy the pinned observer module to tools and replace only oralab.status with
a delegation; all calibration/fetch/update/lock/recovery code stays byte-identical.
Back up the exact prior bytes, check deployed hashes, exercise existing status
command, prove no manifest/archive/clone/config changes, and preserve restoration.
Source update is manual and reviewed, never an auto-executed GitHub commit.
