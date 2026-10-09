# ISOLATION-01 — bounded Windows capability acceptance

2026-10-09. Frozen contract e74b345f; accepted execution 22dd90d6. Engineering
only: zero scientific worlds. Existing Python 3.12.10 copied into a disposable
D: runtime, without reinstalling or changing installed-runtime permissions.

## What passed

Two independent trial blocks, ten cases: two ordinary controls, two confined
workers and six fail-closed setup cases. Parent inspected the suspended workers'
actual Windows tokens, unique package SID and zero capability count before user
code; configured/read back the existing Job Object caps before resuming. Workers
had 128 MiB committed-job memory, five seconds CPU, ten seconds wall and one/two
concurrent process slots for confined/control cases. This is not a physical
memory-peak claim. Outer supervisor capped the finite panel and regression run.

| Attempt | Ordinary control, both trials | Confined, both trials |
|---|---|---|
| Workspace read/write | Succeeded | Succeeded |
| Outside canary read/write | Succeeded; parent observed write | Permission denied, errno 13; canary unchanged |
| Parent VM-write process handle, no memory write | Succeeded | Access denied, WinError 5 |
| Harmless Python child | Executed; child marker present | Quota denial, WinError 1816; no child marker |
| Parent-owned local TCP listener | Connected; parent received probe | One-second timeout; parent accepted zero connections |

The TCP observation is local loopback denial under zero network capabilities,
not an empirical test of every network route/protocol. Both unrestricted controls
proved the listener reachable. No external destination was contacted.

Missing executable failed creation (WinError 2). Injected job-assignment and token
gate failures terminated still-suspended children with exit 125. No user-code
marker, report, connection, canary change or ResumeThread occurred in those six
cases. Injection tests handling of setup errors, not kernel fault tolerance.

All four executing workers exited zero. Parent independently checked stopped
processes after handle/job closure; unique profile cleanup returned success.
The separate auditor accepted the complete matrix, source/runtime hashes, raw
reports, allowed file contents, child markers, canary effects, listener observations,
tokens and cap readbacks. A recomputed-hash report claiming an outside read leak
was rejected semantically. The source-pinned local regression suite attempted
19 tests: 18 passed, one expected non-Windows-only skip.

## Preserved failures and correction

First native attempt a75f918 stopped during workspace low-integrity labeling:
inherited Modify rights lacked owner WRITE_OWNER. Corrected only explicit owner
rights on newly created test folders; existing installation and laboratory ACLs
unchanged. Failed archive retained and all 323 sealed files restored on D:.

Second attempt 5c89353 ran the capability matrix but failed audit because the
auditor incorrectly treated Job Object TotalProcesses as successful execution.
Windows [counts rejected associations](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_basic_accounting_information);
retained handles can also retain active accounting after process exit. Preserved
raw counters and stopped checks; added independent child markers. Python file
errors report errno 13; loopback rejection here reports timeout rather than a
native socket access error. Acceptance uses the frozen contract's actual denied
operations; no restriction was relaxed. All 338 second-attempt files restored.

Accepted raw parent evidence SHA256:
3530e318e7861fb2d76a036834a0dd3f26559fee1a9ca32b118518ecc7425ccf.
Source archive SHA256:
7f89146d54577b707d543f2f338d07b35661465e4f1b6aa6871137d23e6d1f96.
Private operator evidence includes failed and accepted archives, native errors,
ACL command logs, exact process exits, runtime copies, raw worker reports,
source revisions, baseline preservation and archive restoration.
Accepted archive SHA256:
f09211dfbbbdc84411fbe28f4e5d266b227f624c0810a92dfadf700a72f20fab.
All 400 accepted sealed files restored; 265 shared tracked files stayed unchanged.
Earlier failure archive hashes: 19bb301e5d13453542ff92339d2467a19440a686b3958c36ff376bc6c1a4d036
and 81312cb6c961bfe692ff0ba1606298380c328cc01e3aa03f177214b50b819044.

## Scope and next gate

This verifies a disposable capability prototype on this Windows host. Ordinary
AppContainer access to selected Windows resources and its profile remains;
no complete filesystem allowlist, hostile escape assessment, LPAC, arbitrary
executable support, reliable disk quota, physical power-loss/full-host recovery,
production-world isolation or unattended runtime is demonstrated. No global
firewall, service, existing profile, observer, source history or scientific law
changed. Unique profile metadata is Windows-owned; active lab files stay on D:.

Next: separately precommit bounded actual-world checkpoint/resume composition
inside confinement, verifying exact identity, RNG/noise, ancestry and all state,
rejected setup and read-only observation. Preserve existing recovery baselines;
do not migrate an approved world or activate a persistent pilot. Science remains
at RECYCLE-01's negative unscreened realization; future local resource/reaction
coupling needs a distinct full-cost prospective candidate. AI-Research main
fef0a523 / Pass 29 unchanged, with transmission, benefit and partner-resupply
claims kept separate; no unproven mechanism installed. Observer remains paused.
