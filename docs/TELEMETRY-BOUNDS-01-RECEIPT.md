# TELEMETRY-BOUNDS-01 — bound checksums before replay

Pre-fix0e25a4de62f8faef5951eaaa5efd9c957bba3e06 reproduces an oversized
manifest opening before replay's evidence limits. Repair5166698362b41325bc8e85a41f9bef77ba266339
limits checksum enumeration, per-file and aggregate reads; streaming growth
is bounded. All included files still contribute SHA256; writer.lock is excluded
as before. Links/reparse and nonregular files are refused. No UI/law changes.

Eight native/portable bounds and existing telemetry tests pass. The separate
audit on33439b60ab28c1fdf6becfe82abe164aa1a74b68 creates a real4,194,305-byte
manifest and checks refusal before content opening, unchanged bytes and inactive
unknown status. Existing native fixture independently replays three ticks,
rejects12 cache corruptions, recognizes two advances, inactive same-frame and
stopped states, and confirms read-only observations.

Evidence under `D:/OraLab/runs/telemetry-bounds01-*-20261010`; every complete
archive has checksum-verified readback. The first independent audit's final size
field mistakenly reported a reused world-directory variable as0. Preserve that
receipt; corrected audit-v2 isolates fixture scope and asserts the actual size.
Its actual refusal and native checks were unaffected. No oversized source is
executed; no new scientific world law, live deployment or persistent pilot.
These reader limits are application bounds, not hardened filesystem confinement
or a process memory-peak guarantee. Full-host and physical durability stay open.
