# Bounded task and memory service

This is new service infrastructure. It stores supplied observations and retrieves
them by exact key. Optional Ollama mode produces untrusted proposals and accepts
separately authenticated operator corrections. It does not update model weights,
discover a policy, run PILOT74 worlds, or establish a scientific learning result.
Scientific admission and unattended startup remain disabled.

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
data and cannot start processes or execute code. Default mode has no model calls.
The optional mode below permits only the fixed local Ollama API.
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
reserve at least 32 MiB including two rotating 4 MiB snapshots, two bounded
transport logs, temporary files and filesystem overhead. SQLite FULL durability
requests OS flushes; device failure still needs off-device backups.
`forget` removes the current key; recent task receipts retain their original
content until receipt eviction. This is not secure erasure.

Use the outside supervisor for a reviewed run:

```powershell
python -B -m experiments.ora_supervised_service_v1 D:/OraLab/state/ora-service --seconds 60 --slice-seconds 15 --max-restarts 2
```

Each worker starts suspended inside a Windows Job: 256 MiB, 10 seconds user CPU,
two concurrent processes, 1 MiB captured output, and an external slice deadline.
The supervisor owns the Job until zero active processes and pipe EOF. It renews
successful slices, backs off 1/2/4 seconds on failures, and stops after at most
three configured crash retries, 64 attempts, or one hour. STOP is checked outside
the worker too; an interrupted transaction rolls back. No boot task is installed.
The supervisor holds its own exclusive lock, writes one bounded receipt, and keeps
two rotating transport logs and two integrity-checked snapshots. Corruption stops
execution. Restoration is deliberately manual: restoring an old submission cursor
could replay external work, so no automatic rollback is safe without reconciliation.

For Ollama mode, an operator separately provisions a plain 32-byte `feedback.key`
and `ollama.json` containing only `{"model":"gpt-oss:20b"}`. Restrict the directory
to the trusted operator account. The secret never enters a prompt or a log. The
service and operator share a local-account trust boundary; this is not a sandbox
against malicious software already running as that account.

In this mode only `ask`, `recall`, and `approve` tasks are enabled. `ask` first
checks the exact trusted memory key; a hit returns stored knowledge without a model
call. A miss calls literal `127.0.0.1:11434/api/generate` with no proxy, redirects
or tools, requested CPU-only generation, 2048 context, 128 output tokens,
a 50-second socket timeout and a 64 KiB
response cap. Model text is quarantined among at most 16 proposals. It cannot
write trusted memory, sign feedback, or submit tasks. Context is limited to the
explicit prompt; no directory scanning or private memory dump occurs.

After reviewing a proposal's answer and hash, publish an explicit correction:

```powershell
python -B -m experiments.ora_feedback_operator_v1 DIRECTORY NEXT_SEQUENCE MEMORY_KEY PROPOSAL_SHA256 CORRECTED_VALUE
```

The signature binds task sequence, key, proposal hash and corrected text. Modified,
replayed or expired feedback is refused. Approval, memory update and task completion
commit together. Feedback is learning through retained corrected knowledge, not
model retraining. Original prompts, proposals and recent receipts remain in the
bounded database until eviction; `forget` is not available through an unsigned
model-mode task.

The existing Ollama server is a separate process outside the service Job. Request
limits and `keep_alive=0` request bounded generation/unloading but do not enforce
server RAM/GPU limits or guarantee cancellation after client death. Its resource
and cancellation policy must be settled before unattended activation. The native
26-role fixture uses the real G with scripted W/C and no Worlds; it is separate
from admission of the production scientific controller. Remaining gates include
an integrated soak, fault handling during model calls, backup reconciliation, and
deliberate continuous-startup configuration after these limits are verified.

For a genuinely cold installed `gpt-oss:20b`, explicitly run the separate preparation
stage before starting feedback work:

```powershell
python -B -m experiments.ora_ollama_prepare_v1
```

It requests an empty-prompt, CPU-only load with a 60-second keep-alive, under a
separate client Job (64 MiB, 5 seconds client CPU, 125 seconds outside wall deadline).
The HTTP timeout is 120 seconds. No task or trusted memory is produced. Start the
supervised service promptly after successful preparation; model generation requests
still retain the ordinary bounded task deadline. These client limits do not cap
the shared Ollama server itself. The cold-stage command is explicit and is not
silently repeated on every failed task.

The first ongoing task source combines all three requested lanes. While the
supervisor runs, start a bounded producer with explicitly selected Ora files:

```powershell
python -B -m experiments.ora_mixed_stream_v1 DIRECTORY --seconds 60 --practice 2 --file experiments/ora_ollama_prepare_v1.py
```

The producer itself runs inside a 128 MiB/10-second CPU Job with an outside wall
deadline. It offers at most 32 arithmetic tasks and four selected files per run.
Practice uses a supplied Python addition reference and signs the reference answer
as `verified-arithmetic-v1`; it never uses the model's guess as its own answer key.
This is a supplied exercise curriculum, not a discovered policy or scientific
advantage. Repeated exact keys can use retained corrected knowledge.

Selected files must be plain files inside this Ora checkout, at most 3800 bytes
each. There is no recursive scan or silent truncation. Project findings remain
untrusted proposals awaiting the operator correction command. Manual corrections
and automatic sources share `mailbox.lock`; an unconsumed operator task cannot be
overwritten. The producer stops at its deadline and leaves published unfinished
work recoverable. Its finite run can be renewed deliberately after reviewing the
receipt; no scheduler or boot installation is implicit. Feedback provenance is
retained alongside each memory as `operator` or `verified-arithmetic-v1`.

An owned-server alternative is now provided by `ora_owned_ollama_v1.OwnedOllama`.
It launches the installed Ollama binary and its inherited runner tree suspended
inside a dedicated Job on `127.0.0.1:11435`: 24 GiB combined committed RAM, 20%
CPU hard rate, 900 aggregate user-CPU seconds, eight concurrent processes, a
finite outside wall deadline, and kill-on-close. CPU-rate and ordinary limits
must read back exactly before resume. The user's server on 11434 is untouched.

GPU backends are disabled in the child environment and requests force `num_gpu=0`.
Preparation and model checks require zero reported VRAM and at most one loaded
model. These are CPU-only configuration and observation checks, not an OS GPU
memory quota. Cloud use is disabled; only existing local models are used.

Use `{"model":"gpt-oss:20b","port":11435}` in an owned session. Every generation
authenticates the listener PID and exact process birth against the live owner's
marker before sending a prompt; it never falls back to 11434. The context owns
its model Job until all descendants have exited and output reaches EOF. Its
server STOP is separate from the task service's operator STOP. Controls retain
a bounded output prefix and native result for each of up to four finite epochs.
This component does not install unattended startup or replace the user's shared
server. A longer owned-server soak and model-death recovery must qualify it before
continuous activation.

Explicit corruption recovery is available as:

```powershell
python -B -m experiments.ora_memory_restore_v1 DIRECTORY SNAPSHOT_PATH SNAPSHOT_SHA256 KNOWN_PRODUCER_CURSOR
```

The cursor must come from the producer's independently known latest submission,
not a guess derived from an old snapshot. The command requires a complete snapshot
at exactly that cursor, no active supervisor/worker/producer, no newer mailbox,
and no unreconciled SQLite journal/WAL/SHM. It verifies the digest, size and database
integrity, refuses to replace a healthy primary, and retains one corrupt primary.
An unfinished or older snapshot is refused. Existing unknown recovery files are
never overwritten. This remains explicit operator recovery, not automatic rollback.
