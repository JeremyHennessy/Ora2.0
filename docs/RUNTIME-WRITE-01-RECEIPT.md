# RUNTIME-WRITE-01 — refuse partial authoritative writes

Engineering-only repair, October10. Contract and fault fixtures committed at
358c56f0183143e3bfec6ece3fafd61357a0a422 before reproduction. Both targeted
assertions fail there: atomic_json promotes a short checkpoint write and
record_step returns a new journal chain head after a short append. Real partial
bytes are written by the injected backend, not merely a forged return count.
This is a reproduced software acknowledgement defect, not a hardware-fault trial.

Minimal repair source7ad526376d8ce2ceeb784655d476116938c4bf97 checks the exact
integer return count before flushing/promoting/acknowledging authoritative writes.
It changes two call sites and adds one helper. All18 scoped tests pass under
the same finite bounds: both regressions, existing three abrupt-process exit
boundaries, exact AL01 state/PRNG replay, immutable completion, corruption refusal,
writer locking and source/configuration identity checks. No scientific transition,
seed, cost, success criterion, old dataset, observer UI or heartbeat implementation
changes. Historical worlds remain tied to their original source; changing runner
identity does not authorize relabelling or rewriting old evidence.

A separate byte-level worker uses a different short prefix (all but two bytes,
instead of half) on both pinned sources. Before repair, the previous checkpoint
is replaced and journal append is acknowledged. After repair, both writes raise;
the previous checkpoint remains byte-identical. Partial journal bytes remain
unchanged, restoration rejects the incomplete tail, and no final receipt appears.
No automatic tail deletion or invented recovery is introduced.

Evidence roots under `D:/OraLab/runs/`:

* `runtime-write01-before-20261010`: expected child exit1; two failed assertions.
* `runtime-write01-after-20261010`: child exit0;18 tests pass in29.263s.
* `runtime-write01-independent-20261010`: two independent byte workers exit0.

Each root has exact source/runner seals, process outputs, archives and restored
checks. Final self-accounting storage snapshots independently verify165,377,
168,983 and62,425 logical bytes respectively. Exclusive operator locking,
D: temporary files,5GiB floor,512MiB allocation,30CPU/30wall seconds and16
process slots applied to the regression runs; separate readers use5CPU/10wall.
This closes this acknowledgement defect, not physical power-loss durability,
fresh-OS/full-host recovery or production confinement. The proposed loss budget
and separate pilot approval remain [open runtime gates](RUNTIME-ACCEPTANCE-2026-10-10.md).

Science remains at the preserved SHELTER-01 conditional accounting result:
14/16 advantages but failed all-case admission, no natural worlds or Stage3
self-maintenance acceptance. Next science requires a complete accessible paid
formation/conversion/repair mechanism with viable simpler controls. AI-Research
Pass49/e3eb5e3 remains independent; neither repository gained a new research pass.
