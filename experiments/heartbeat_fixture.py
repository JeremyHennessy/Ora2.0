"""Explicitly launched finite energy-counter telemetry; no resume or service."""
import argparse
import hashlib
import json
import os
from pathlib import Path
from datetime import datetime, timezone


def encode(x):
    return json.dumps(x, sort_keys=True, separators=(",", ":"))


def sha(x):
    return hashlib.sha256(encode(x).encode()).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def run(output, world_id, revision, work=12, max_ticks=32, pause_after=None):
    if not isinstance(world_id, str) or not world_id or len(revision) != 40 or any(c not in "0123456789abcdef" for c in revision):
        raise ValueError("Immutable world ID/exact source required")
    if type(work) is not int or not 0 <= work <= 1000 or type(max_ticks) is not int or not 1 <= max_ticks <= 1000 or pause_after is not None and (type(pause_after) is not int or not 1 <= pause_after <= max_ticks):
        raise ValueError("Finite configuration required")
    config = {"work": work, "max_ticks": max_ticks, "pause_after": pause_after}
    identity = {"world_id": world_id, "source_revision": revision, "config_sha256": sha(config)}
    identity["run_id"] = sha(identity)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)  # Exclusive first-writer admission.
    lock = output / "writer.lock"
    with lock.open("x", encoding="utf-8") as stream:
        stream.write(encode({"pid": os.getpid(), **identity}) + "\n")
    state = {**identity, "simulation_tick": 0, "work": work, "heat": 0}
    chain = "0" * 64

    def frame(status, reason):
        nonlocal chain
        value = {"schema": "heartbeat01-v1", "config": config, "state": state.copy(), "state_sha256": sha(state),
                 "last_heartbeat": now(), "status": status, "reason": reason, "previous_sha256": chain}
        value["frame_sha256"] = sha(value)
        with (output / "frames.jsonl").open("a", encoding="utf-8", newline="\n") as journal:
            journal.write(encode(value) + "\n")
            journal.flush()
            os.fsync(journal.fileno())
        pending = output / "latest.pending"
        with pending.open("w", encoding="utf-8", newline="\n") as snapshot:
            snapshot.write(encode(value) + "\n")
            snapshot.flush()
            os.fsync(snapshot.fileno())
        pending.replace(output / "latest.json")
        chain = value["frame_sha256"]
        return value

    try:
        frame("running", "ready")
        while state["work"] > 0 and state["simulation_tick"] < max_ticks:
            state["work"] -= 1
            state["heat"] += 1
            state["simulation_tick"] += 1
            frame("running", "advanced")
            if pause_after is not None and state["simulation_tick"] == pause_after:
                return frame("paused", "operator_pause")
        return frame("stopped", "exhausted" if state["work"] == 0 else "tick_limit")
    except Exception:
        # Best effort only; a storage failure may prevent writing a failed frame.
        # A stale/inconsistent journal must not be presented as a live worker.
        frame("failed", "worker_error")
        raise
    finally:
        lock.unlink(missing_ok=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output-dir", required=True)
    p.add_argument("--world-id", required=True)
    p.add_argument("--source-revision", required=True)
    p.add_argument("--work", type=int, default=12)
    p.add_argument("--max-ticks", type=int, default=32)
    p.add_argument("--pause-after", type=int)
    a = p.parse_args()
    run(a.output_dir, a.world_id, a.source_revision, a.work, a.max_ticks, a.pause_after)
