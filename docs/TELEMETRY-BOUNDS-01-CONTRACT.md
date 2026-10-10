# TELEMETRY-BOUNDS-01 prospective regression

Freeze before tests; engineering only, existing files/fixtures, no UI or law changes.
Current telemetry hashes every file using unbounded read_bytes before the
independent journal auditor applies its bounds. Reproduce this bypass without
allocating large files: a manifest with a mocked over-limit stat must be refused
before content is opened. Preserve the failed baseline regression.

Repair only the checksum reader: finite enumeration (16 entries including lock),
16 MiB journal, 4 MiB other files, 32 MiB aggregate; 64 KiB streaming blocks,
preflight size checks and growth checks during reading. Reject links/reparse and
nonregular files rather than follow them. Exclude writer.lock as before.
Hash all remaining files so historical read-only comparisons retain their scope.
No filesystem confinement claim follows from these checks.

Tests: valid checksums/read-only behavior; oversize rejected before opening;
aggregate and entry bounds with tiny declared limits; bounded growth detection;
unchanged recorded/live/native fixture tests. Independent audit must use actual
oversize evidence and native fixture validation, preserve raw hashes and exits.
One laboratory writer; existing Python, pinned reviewed source, D: temporary
files; 512 MiB allocation,90 CPU seconds,16 process slots,120 wall seconds each.
Archive/readback under existing evidence budgets; no full-host/power-loss test.
