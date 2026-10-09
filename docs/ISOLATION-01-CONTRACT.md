# ISOLATION-01 — disposable Windows capability gate

Prospective engineering contract, 2026-10-09. No scientific worlds or services.
Preserve RESOURCE-02/HEARTBEAT recovery, observer and historical experiment files.

## Mechanism and scope

Launch a copy of the existing Python 3.12 runtime as a Windows AppContainer with
zero capability SIDs, no inherited handles, a minimal explicit environment and
a suspended primary thread. Before resuming it, independently inspect its kernel
token and assign/read back the existing Job Object limits. There is no fallback
to ordinary execution. A unique disposable profile is created and deleted through
Windows APIs; Windows owns its profile metadata. Laboratory files, copied runtime,
temporary files and evidence stay on D:. No installed-runtime ACL, firewall,
service, loopback exemption, dependency or existing profile is modified.

Only new disposable runtime (read/execute) and workspace (modify, low integrity)
receive the unique package SID. A new external canary has a protected DACL for
the current user, SYSTEM and Administrators. It contains generated test data,
never existing personal/laboratory data. Ordinary AppContainers still have access
to some Windows resources and their own profile; this is not a VM, a complete
filesystem allowlist, a security proof or production hardened runtime.

Reference: Microsoft [AppContainer launch](https://learn.microsoft.com/en-us/windows/win32/secauthz/implementing-an-appcontainer),
[isolation](https://learn.microsoft.com/en-us/windows/win32/secauthz/appcontainer-isolation),
[profile cleanup](https://learn.microsoft.com/en-us/windows/win32/api/userenv/nf-userenv-deleteappcontainerprofile).

## Frozen finite matrix and independent observations

Two trials, each with an ordinary control and a confined worker. Both attempt:
read/write the allowed workspace, read/write the external canary, TCP connection
to a parent-owned IPv4 loopback listener, open the parent for VM-write rights
(without writing memory), and start a harmless Python child. Control job allows
two processes; confined job allows one. No external network destination is used.

Parent checks token IsAppContainer, package SID and capability count before resume;
ordinary control is non-AppContainer. Job readback must match 128 MiB committed
job memory, five seconds CPU, kill-on-close and process limit 2/1. Ten-second wall
limit per launch; 300-second panel limit, 5 GB free-space floor, 256 MiB panel disk
ceiling, exclusive existing operator lock. Do not interpret Windows' reported peak
memory as a demonstrated physical-memory peak bound.

Control must read/write canary, connect to listener, open parent and run child.
Confined worker must read/write its workspace, fail external read/write with
access denied, fail TCP connection, fail parent VM-write handle and fail child
launch. Parent verifies canary unchanged during confinement, zero accepted confined
connections, one accepted control connection, and process stopped after closure.
Preserve raw worker reports, parent observations, native errors, exact source,
runtime-copy hashes, ACL output, exits and elapsed time. A separate auditor checks
every case, hashes, matrix completeness and source identity.

Each trial also exercises three fail-closed cases: nonexistent executable (real
creation failure), injected job-assignment failure and injected token-gate failure
while the child remains suspended. No user code marker may be written; any created
child must terminate, and no ResumeThread may occur. Injections test launcher
failure handling, not hardware/kernel malfunction. Any unexpected capability,
gate, outcome, timeout, missing control or cleanup failure falsifies acceptance.

## Claims and follow-on gate

Passing supports only this controlled local capability matrix on this Windows
host. Local TCP denial plus zero network capabilities is not an empirical audit
of every network protocol/adapter. There is no hostile escape assessment, LPAC,
arbitrary executable support, reliable disk quota enforcement, production-world
composition, physical power-loss or full-host recovery claim. Existing job caps
and recovery evidence retain their original limits. After capability acceptance,
the next engineering step is a separately bounded actual finite-world checkpoint /
resume composition inside confinement, including rejected setup and read-only
observation. An unattended persistent pilot still requires separate gates and
human authorization.
