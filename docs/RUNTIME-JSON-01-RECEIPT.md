# RUNTIME-JSON-01: reject ambiguous recovery records

This fixes an evidenced application integrity defect. It does not change the
digital universe law, historical trajectories, observer UI or activation gates.

The test-only revision `8e93c2f11220b9a9333bf0fae65b1a2982ee899f` accepts
eight conflicting duplicate-name records: manifest payload/envelope, checkpoint
step/checksum, receipt final step, and journal step/state/checksum. Ordinary JSON
decoding silently keeps the last value, so the existing envelope hashes and
replay can pass. The new pair hook rejects duplicate names at every nesting
level before checksum verification. Fixed implementation is
`b089071eed26b131564d9139ddd21568cbe75e8a`.

Twenty focused checks pass in separate native bounded invocations: two new
checks, sixteen existing checkpoint/recovery checks, and two short-write checks.
The eight corruption cases reject without rewriting any file. Valid completed
four-step histories replay exactly. A separate parser inspects raw pair lists,
confirms one duplicate per corrupted record and verifies that ordinary parsing
still produces valid checksums. It does not import the worker's decoder.
Archived-source scoped checks pass again after D: restoration and after C:
flush/readback and restoration to D:. This is readable-copy evidence only.

Failures preserved: the first combined regression invocation hit its registered
30-second cap (exit124). Five temporary files remained; the original ledger's
filesystem denominator was incomplete. The separate forensic census records
109595 actual bytes, all file hashes and this limitation; it does not retroactively
claim prewrite accounting. Tests were split without changing code, test cases or
resource limits. The first independent wrapper completed its corruption proof
and backup but failed to save its ledger because it imported an older Budget
API. A fresh corrected wrapper closes the ledger; both attempts remain preserved.

Evidence: `D:/OraLab/runs/runtime-json01-before-20261011`,
`D:/OraLab/runs/runtime-json01-after-20261011` (timeout),
`D:/OraLab/runs/runtime-json01-after-v2-20261011`, and
`D:/OraLab/runs/runtime-json01-independent-v2-20261011`.
The independent archive also contains the original timeout evidence. Existing
records are never normalized or rewritten. Archived runtimes retain their exact
source identity; this fix is not permission to resume old records using changed
code. An ambiguous archive requires manual review, never automatic key choice.

No new scientific result or net useful work was measured. Stage3 remains
unchanged. Independent-host recovery, physical power-loss durability, production
confinement and separately approved pilot activation remain unresolved.
