# RESOURCE-02 — fixture implementation correction before acceptance

2026-10-08. Original contract fbc830e and original implementation
0d4f2e365590c0acd01062d83c8ed162ac8cf0e7 remain immutable. Initial focused
checks had two errors: the non-Windows test changed os.name before constructing
a pathlib path on Windows, and the CPU contrast did not satisfy its frozen
stop criterion. No acceptance is inferred from that failed suite.

An independently preserved original-source single CPU diagnostic did stop at
aggregate user CPU 1.0 s, exit 124, tick 5, valid lagged checkpoint, no wall
timeout. This successful repeat does not erase the original failed contrast.
The complete original-source fixed panel is also being preserved separately.

Prospectively correct the portability test to create its path before changing
os.name. The CPU pressure loop currently asks process_time on every arithmetic
operation. That clock includes kernel CPU, whereas the registered job limit
measures user CPU. Clock-query overhead can therefore dominate the intended
arithmetic pressure. The precise original failing iteration's CPU breakdown
was not retained by its temporary unit-test directory and is unresolved.

Keep the 1.5-worker-process-CPU-second pressure, all caps, world, boundary,
controls and acceptance thresholds unchanged. Batch 10,000 arithmetic operations
between clock queries in both CPU arms so pressure predominantly exercises
arithmetic rather than clock calls; do not increase the registered duration.
This is a prospective authored engineering-fixture correction, not a favorable
change to scientific law, resources or success criteria. Independently test the
corrected implementation from clean exact source and preserve the original
failure log, source archive and diagnostic/full-panel evidence in acceptance.
No exact user CPU ceiling or general scheduling guarantee follows.
