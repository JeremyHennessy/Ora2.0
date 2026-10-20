# Bounded task and memory service

This is new service infrastructure. It stores supplied observations and retrieves
them by exact key. It does not update Ollama model weights, discover a policy, run
PILOT74 worlds, or establish a scientific learning result. Guardian admission and
unattended startup remain disabled.

Run a supervised slice from the repository:

```powershell
python -B -m experiments.ora_task_store_v1 D:/OraLab/state/ora-service --seconds 60 --max-tasks 1000
```

The service owns this directory exclusively. A producer writes a JSON array of
1–16 tasks to a temporary file, closes it, then atomically replaces `inbox.json`.
The inbox is at most 64 KiB. Example:

```json
[{"sequence":1,"kind":"remember","key":"preferred_colour","value":"blue"}]
```

Use consecutive positive sequence numbers across restarts. Supported kinds are
`remember`, `recall`, and `forget`; the latter two require an empty value. Text is
data and cannot start processes, call models, access the network, or execute code.
The producer must wait for processing before replacing the single inbox. Pending
tasks and receipts are in `memory.sqlite3`; no concurrent second service may open
the store. An invalid inbox stops the service with an error; fix it before restart.
Replaying a retained ID with changed content is refused. An expired receipt is
reported as expired and cannot recreate a task. This is a bounded mailbox, not an
unbounded event log or a multi-producer broker.

Create `STOP` in the directory to stop between transactions. Slices also stop at
their time/task bounds. Remove `STOP` before a deliberate restart. A crash releases
the OS owner lock; SQLite rolls back uncommitted work and requeues claimed tasks.
Memory update, result receipt, and task completion commit in one transaction.
Recovery uses the current database, without replaying all past experience.

Limits: 128 pending tasks, 256 remembered keys, 128 recent receipts, 128-byte keys,
4096-byte values, 4 MiB database. Oldest updated memory is evicted first. The
rollback journal is transient, bounded by database pages plus SQLite metadata;
reserve at least 10 MiB for the service directory and additional filesystem space.
SQLite FULL durability requests OS flushes; device failure still needs backups.
`forget` removes the current key; recent task receipts retain their original
content until receipt eviction. This is not secure erasure.

Next integration gates: native G/W/C complete protocol execution, resource-contained
service launcher with restart backoff, explicit producer/feedback contract,
bounded backups and corruption recovery, then Ollama integration with trusted
feedback distinguished from generated guesses. Do not autoactivate startup until
those gates pass. A longer live service rehearsal must record its actual bounds
and outcomes separately from the historical scientific fixtures.
