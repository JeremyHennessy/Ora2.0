"""Manually launched finite counter with audited checkpoint/journal resume."""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform

from experiments.heartbeat_checkpoint_audit import inspect, validate_config

FAULTS = {"pre_commit": 77, "post_journal": 78, "post_pending": 79, "post_checkpoint": 80}


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def sha(value):
    return hashlib.sha256(encode(value).encode()).hexdigest()


@contextmanager
def writer_lock(output, create=False):
    # Stable file: never unlink it and create a second independently locked inode.
    path = output / "writer.lock"
    if create:
        with path.open("xb") as stream:
            stream.write(b"L")
            stream.flush()
            os.fsync(stream.fileno())
    with path.open("r+b") as stream:
        if path.stat().st_size != 1:
            raise ValueError("Invalid lock file")
        stream.seek(0)
        if os.name == "nt":
            import msvcrt
            msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            stream.seek(0)
            if os.name == "nt":
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def identity_for(world_id, revision, config):
    if not isinstance(world_id, str) or not 1 <= len(world_id) <= 200 or not isinstance(revision, str) or len(revision) != 40 or any(c not in "0123456789abcdef" for c in revision):
        raise ValueError("World ID and exact lowercase source revision required")
    base = Path(__file__).parent
    identity = {"world_id": world_id, "source_revision": revision, "config_sha256": sha(config),
                "python": platform.python_version(),
                "worker_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                "auditor_sha256": hashlib.sha256((base / "heartbeat_checkpoint_audit.py").read_bytes()).hexdigest()}
    identity["run_id"] = sha(identity)
    return identity


def write_file(path, value):
    with path.open("wb") as stream:
        stream.write((encode(value) + "\n").encode())
        stream.flush()
        os.fsync(stream.fileno())


def run(output, world_id, revision, work=12, max_ticks=32, resume=False,
        pause_after=None, fault_tick=None, fault_point=None):
    config = {"work": work, "max_ticks": max_ticks}
    validate_config(config)
    identity = identity_for(world_id, revision, config)
    if pause_after is not None and (type(pause_after) is not int or not 1 <= pause_after <= min(work, max_ticks)):
        raise ValueError("Pause within finite reachable horizon required")
    if (fault_tick is None) != (fault_point is None) or fault_point is not None and (fault_point not in FAULTS or type(fault_tick) is not int or not 1 <= fault_tick <= min(work, max_ticks)):
        raise ValueError("Fault point and reachable tick must be paired")
    output = Path(output)
    if not resume:
        output.mkdir(parents=True, exist_ok=False)
    with writer_lock(output, create=not resume):
        if resume:
            evidence = inspect(output, revision)
            if encode(evidence["manifest"]["config"]) != encode(config) or encode(evidence["manifest"]["identity"]) != encode(identity):
                raise ValueError("World/source/configuration mismatch")
            last = evidence["frames"][-1]
            state, epoch, seq, chain = last["state"].copy(), last["epoch"], last["seq"] + 1, last["frame_sha256"]
            if last["status"] != "stopped" and epoch >= 32:
                raise ValueError("Finite resume cap")
            if last["status"] != "stopped" and any(t is not None and t <= state["simulation_tick"] for t in (pause_after, fault_tick)):
                raise ValueError("Invocation controls must target a future tick")
            # Validation completed before any mutation; pending is never trusted.
            if not evidence["report"]["checkpoint_current"]:
                write_file(output / "checkpoint.pending", last)
                (output / "checkpoint.pending").replace(output / "checkpoint.json")
            if last["status"] == "stopped":
                return last
            epoch += 1
        else:
            write_file(output / "manifest.json", {"schema": "heartbeat02-v1", "config": config, "identity": identity})
            state = {"run_id": identity["run_id"], "simulation_tick": 0, "work": work, "heat": 0}
            epoch, seq, chain = 0, 0, "0" * 64

        def fault(point, advancing):
            if advancing and state["simulation_tick"] == fault_tick and point == fault_point:
                os._exit(FAULTS[point])  # Actual process exit: no Python cleanup.

        def frame(status, reason, advancing=False):
            nonlocal seq, chain
            value = {"schema": "heartbeat02-v1", "seq": seq, "epoch": epoch, "state": state.copy(),
                     "state_sha256": sha(state), "last_heartbeat": datetime.now(timezone.utc).isoformat(),
                     "status": status, "reason": reason, "previous_sha256": chain}
            value["frame_sha256"] = sha(value)
            fault("pre_commit", advancing)
            with (output / "frames.jsonl").open("ab") as journal:
                journal.write((encode(value) + "\n").encode())
                journal.flush()
                os.fsync(journal.fileno())
            fault("post_journal", advancing)
            write_file(output / "checkpoint.pending", value)
            fault("post_pending", advancing)
            (output / "checkpoint.pending").replace(output / "checkpoint.json")
            fault("post_checkpoint", advancing)
            seq, chain = seq + 1, value["frame_sha256"]
            return value

        frame("running", "resumed" if resume else "ready")
        while state["work"] > 0 and state["simulation_tick"] < max_ticks:
            state = {**state, "simulation_tick": state["simulation_tick"] + 1,
                     "work": state["work"] - 1, "heat": state["heat"] + 1}
            frame("running", "advanced", advancing=True)
            if state["simulation_tick"] == pause_after:
                return frame("paused", "operator_pause")
        return frame("stopped", "exhausted" if state["work"] == 0 else "tick_limit")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--world-id", required=True)
    parser.add_argument("--source-revision", required=True)
    parser.add_argument("--work", type=int, default=12)
    parser.add_argument("--max-ticks", type=int, default=32)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--pause-after", type=int)
    parser.add_argument("--fault-tick", type=int)
    parser.add_argument("--fault-point", choices=FAULTS)
    args = parser.parse_args()
    try:
        run(args.output_dir, args.world_id, args.source_revision, args.work, args.max_ticks,
            args.resume, args.pause_after, args.fault_tick, args.fault_point)
    except (ValueError, OSError, KeyError, TypeError) as exc:
        parser.exit(2, f"Rejected run: {exc}\n")
