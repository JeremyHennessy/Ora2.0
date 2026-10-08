"""Read-only independent validation; telemetry is not proof of process health."""
import argparse
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone


def canonical(x):
    return json.dumps(x, sort_keys=True, separators=(",", ":"))


def digest(x):
    return hashlib.sha256(canonical(x).encode()).hexdigest()


def timestamp(x):
    value = datetime.fromisoformat(x)
    if value.tzinfo is None or value.utcoffset().total_seconds() != 0:
        raise ValueError("UTC timestamp required")
    return value


def inspect(output, current=None, stale_seconds=5):
    if type(stale_seconds) not in (int, float) or stale_seconds <= 0:
        raise ValueError("Positive stale threshold required")
    output = Path(output)
    raw = (output / "frames.jsonl").read_bytes()
    if len(raw) > 4 * 1024 * 1024 or not raw.endswith(b"\n"):
        raise ValueError("Incomplete/oversized telemetry")
    frames = [json.loads(line) for line in raw.decode().splitlines()]
    if not frames or len(frames) > 1002:
        raise ValueError("Finite frame cap")
    config = frames[0]["config"]
    if set(config) != {"work", "max_ticks", "pause_after"} or type(config["work"]) is not int or not 0 <= config["work"] <= 1000 or type(config["max_ticks"]) is not int or not 1 <= config["max_ticks"] <= 1000:
        raise ValueError("Configuration")
    pause = config["pause_after"]
    if pause is not None and (type(pause) is not int or not 1 <= pause <= config["max_ticks"]):
        raise ValueError("Pause configuration")
    first_state = frames[0]["state"]
    identity = {k: first_state[k] for k in ("world_id", "source_revision", "config_sha256")}
    revision = identity["source_revision"]
    if not isinstance(identity["world_id"], str) or not identity["world_id"] or len(revision) != 40 or any(c not in "0123456789abcdef" for c in revision) or identity["config_sha256"] != digest(config):
        raise ValueError("Immutable identity")
    identity["run_id"] = digest(identity)
    previous, chain, previous_time, terminal = None, "0" * 64, None, False
    for index, frame in enumerate(frames):
        if set(frame) != {"schema", "config", "state", "state_sha256", "last_heartbeat", "status", "reason", "previous_sha256", "frame_sha256"} or frame["schema"] != "heartbeat01-v1" or canonical(frame["config"]) != canonical(config):
            raise ValueError("Frame schema/config changed")
        state = frame["state"]
        if set(state) != set(identity) | {"simulation_tick", "work", "heat"} or any(state[k] != v for k,v in identity.items()):
            raise ValueError("World/source/config identity changed")
        if any(type(state[k]) is not int or state[k] < 0 for k in ("simulation_tick", "work", "heat")) or state["work"] + state["heat"] != config["work"]:
            raise ValueError("Counter energy ledger")
        if frame["state_sha256"] != digest(state) or frame["previous_sha256"] != chain or frame["frame_sha256"] != digest({k:v for k,v in frame.items() if k != "frame_sha256"}):
            raise ValueError("Invalid hash chain")
        moment = timestamp(frame["last_heartbeat"])
        if previous_time and moment < previous_time:
            raise ValueError("Backward heartbeat")
        if terminal:
            raise ValueError("Transition after terminal status")
        status, reason = frame["status"], frame["reason"]
        if index == 0:
            if state["simulation_tick"] != 0 or state["work"] != config["work"] or state["heat"] != 0 or (status,reason) != ("running","ready"):
                raise ValueError("Invalid tick0")
        elif status == "running":
            if reason != "advanced" or previous["work"] == 0 or previous["simulation_tick"] >= config["max_ticks"] or previous["simulation_tick"] == pause:
                raise ValueError("Unpermitted advance")
            expected = {**previous, "simulation_tick": previous["simulation_tick"]+1, "work": previous["work"]-1, "heat": previous["heat"]+1}
            if canonical(state) != canonical(expected):
                raise ValueError("Timer-only/doubled/skipped transition")
        else:
            if canonical(state) != canonical(previous):
                raise ValueError("Status-only frame changed state")
            permitted = (status == "paused" and reason == "operator_pause" and state["simulation_tick"] == pause or
                         status == "stopped" and reason == "exhausted" and state["work"] == 0 or
                         status == "stopped" and reason == "tick_limit" and state["work"] > 0 and state["simulation_tick"] == config["max_ticks"] or
                         status == "failed" and reason == "worker_error")
            if not permitted:
                raise ValueError("False terminal status/reason")
            terminal = True
        previous, chain, previous_time = state, frame["frame_sha256"], moment
    latest = json.loads((output / "latest.json").read_text(encoding="utf-8"))
    if canonical(latest) != canonical(frames[-1]):
        raise ValueError("Journal/snapshot inconsistent; no current snapshot verified")
    current = datetime.now(timezone.utc) if current is None else timestamp(current)
    age = (current - previous_time).total_seconds()
    if age < 0:
        raise ValueError("Future heartbeat")
    status = frames[-1]["status"]
    observed = "stale" if status == "running" and age > stale_seconds else "reported_running" if status == "running" else status
    return {**identity, "verified_simulation_tick": previous["simulation_tick"], "verified_state_sha256": digest(previous),
            "reported_status": status, "observed_status": observed, "reason": frames[-1]["reason"],
            "heartbeat_age_seconds": age, "process_health": "unverified", "verified_frames": len(frames),
            "learning_claim": False, "resume_verified": False}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input-dir", required=True)
    p.add_argument("--current-utc")
    p.add_argument("--stale-seconds", type=float, default=5)
    a = p.parse_args()
    print(json.dumps(inspect(a.input_dir, a.current_utc, a.stale_seconds), indent=2))
