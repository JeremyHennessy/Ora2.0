# EVIDENCE-01 — prospective complete evidence storage gate

2026-10-09. Preserve TRACE-01's failed aggregate16MiB claim and all original bytes.
No physics change, component resampling, controller, world, observer or pilot.
This is trusted laboratory-writer accounting, not an OS disk quota or protection
against arbitrary malicious writers, concurrent pathname races or physical failure.

The gate introduces a guarded binary stream which reserves growth BEFORE every
write. Seeking to patch ZIP headers must not double-charge existing bytes; sparse
growth counts its full logical extent. Never refund a failed/partial write, overwrite
an old file, remove failures, follow a symlink/reparse point or allow path traversal.
Each phase and the combined staging limit must pass atomically before mutation.
Future simulations must use this writer or a separately verified enforced quota;
merely checking folder sizes after execution is insufficient.

One fresh D: case has four immutable limits: raw64MiB (source, copied original
ledger/replay/forgeries), archive32MiB, restore64MiB, failure8MiB; combined144MiB.
Failure accounting is separately reserved so a raw rejection can be preserved.
A64KiB receipt reservation is paid before writing the self-describing receipt.
All reservations, including unwritten tail bytes after I/O failure, remain charged.
Input historical files are read-only; their storage outside this fresh case is
not reclaimed or described as passing the original TRACE-01 limit.

The acceptance supervisor has a separate64MiB metadata/source/test/log envelope;
reserve this allowance before any execution, alongside the144MiB case and an
additional8MiB sealed verification/archive/restoration envelope: combined216MiB
new D: staging. Known source extraction uses listed ZIP sizes; captured process
outputs each max1MiB, fixed five subprocess slots and authored tests max4MiB.
No unconstrained subprocess may write into these envelopes. The finite harness
checks actual bytes against each reservation and preserves any discrepancy.
Copies added for final Git-history/CI/off-drive handoff need their own prospective
finite manifest reservation; they cannot silently share this acceptance allowance.

Before execution commit exact writer, separate filesystem interpreter and tests.
Author fixtures cover phase/combined boundary refusal before creating/changing
bytes; ZIP header patch/reopen/readback; oversized sparse write; partial-write
reservation retention; extra-file/forged-total rejection; unsafe paths and links.
One complete case copies all392 sealed original TRACE-01 members plus its seal,
preserves their checksums, archives every copied member through the guarded stream,
restores through guarded per-member streams and independently reinterprets all24
historical traces. No panel is generated. Also preserve an intentional refused
raw-phase write in the separately charged failure phase.

Success: every copied/restored historical byte matches, separate price/trace audit
unchanged, phase and combined prewrite accounting passes, a complete independently
enumerated filesystem matches receipt reservations, and forged accounting or extra
files reject. Invalid limits/writer/audit failures stop the gate and remain retained;
do not expand limits after observing failure. Existing operator lock,5GB floor and
512MiB/60CPU/four-process/300wall caps per finite subprocess apply. Keep all temp,
raw, archives and restores on D:; no new world or AppContainer profile.

Close this operational gap before freezing an informative generic paid encounter/
trace/action experiment under unseen changes. It does not repair the original
TRACE-01 run or provide scientific evidence of learning.
