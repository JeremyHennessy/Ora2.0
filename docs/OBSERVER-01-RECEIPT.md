# OBSERVER-01 — existing local status command displays current receipts

2026-10-08. [Contract](OBSERVER-01-CONTRACT.md) precommit 9fe789ea; pinned source
6a68c21ba3ab0731b8dff637214e53a4bc3cc91d, Windows Python 3.12.10.
Read-only inventory showed 26 of 27 original manifests lacked old required fields.
The existing local page was stale. Before changing the tool, the original
oralab.status failure was reproduced on a disposable copy with a real new receipt:
exit 1, `KeyError: 'run_id'`. That expected failure and original bytes are archived.

## Verified repair and manual deployment

The new standard-library observer accepts original source_revision/run_id and
new revision/directory-label receipts. It preserves the complete source receipt,
hash, reported status, tests and label origin. Malformed/duplicate-key/ambiguous
source receipts remain visible error/unknown rows. Reads are limited to 1MiB per
receipt and 1,024 immediate entries; linked/reparse inputs reject. Every displayed
value is escaped; receipt-defined paths/code are not followed or executed.
Process health and independent scientific verification remain unverified.

268 Windows regression tests and eight focused science/observer methods passed.
Fixture checks covered mixed legacy/current/failed records, malformed JSON,
conflicting sources, HTML injection, bounded input and synthetic reparse flags,
unchanged inputs and exact page replay with a fixed report time. This is not a
hostile-filesystem race or hardened-sandbox security assessment.

After pinned acceptance, manually copied the exact reviewed observer module to
`D:\OraLab\tools\laboratory_status.py` and changed only oralab.status to delegate
to it. Its other calibration/fetch/update/locking/recovery code remains byte-
identical. `Lab Status.cmd`, page title/theme/table interaction and original
checkout/environment configuration remain preserved. No remote code auto-executed.
Deployed existing status command exited0; **28 receipts display**, including 3
historical failed receipts, 24 passed and 1 verified. No failed outcome was hidden
or edited. A final refresh checked every displayed receipt hash against its
current input. Local preserved checkout heads are shown separately from receipt
source versions; the page does not fetch remote updates or resume simulations.

Source module deployed SHA256:
`01d8c9927114db763f670e69f36464150035744910564bfde685e95839678f34`.
Updated wrapper SHA256:
`6617cc5a70a974d8bde78fca6c3c5b7292b6c4d926179f96c20473e1ae908982`.
Before/after wrapper, module and observer snapshots, original failure, fixture,
deployed command logs and historical input checksums preserved with the
[ENERGY-01 acceptance archive](ENERGY-01-RECEIPT.md): 28 files restored exactly on D:.
Original clones remain clean at Ora 205e0030 and AI-Research 37ec4502.

Additional read-only archive correspondence review: 23 existing archives hashed,
18 restoration receipts with archive_sha256 matched an actual archive, zero
unmatched reports. This verifies checksum correspondence, not new scientific
reexecution or off-drive restoration. Report preserved separately at
`D:\OraLab\runs\energy01-development\historical-archive-review.json`.

## Next engineering priority and remaining gates

Precommit/test a supervised finite process resource-cap wrapper: CPU/memory,
child-process tree and timeout/termination evidence around a bounded reference
fixture. Resource limits must not be described as filesystem/network isolation;
independent restricted execution remains a separate gate. Continue identifying
an independent off-D backup/restore target and physical power-loss/storage-fault
verification. None of those was established by this observer repair. No
continuous/external runtime, service, runner, API or automatic update was enabled.
