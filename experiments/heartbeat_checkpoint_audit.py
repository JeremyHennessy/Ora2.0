"""Independent read-only audit of finite heartbeat02 counter continuity."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key")
        result[key] = value
    return result


def decode(raw):
    return json.loads(raw, object_pairs_hook=unique_object)


def utc(value):
    moment = datetime.fromisoformat(value)
    if moment.tzinfo is None or moment.utcoffset().total_seconds() != 0:
        raise ValueError("UTC timestamp required")
    return moment


def hex_string(value, length):
    return isinstance(value, str) and len(value) == length and all(c in "0123456789abcdef" for c in value)


def validate_config(config):
    if not isinstance(config, dict) or set(config) != {"work", "max_ticks"}:
        raise ValueError("Finite configuration schema")
    if type(config["work"]) is not int or not 0 <= config["work"] <= 1000 or type(config["max_ticks"]) is not int or not 1 <= config["max_ticks"] <= 1000:
        raise ValueError("Finite configuration bounds")


def source_hashes():
    base = Path(__file__).parent
    return {name: hashlib.sha256((base / filename).read_bytes()).hexdigest()
            for name, filename in (("worker_sha256", "heartbeat_checkpoint.py"),
                                   ("auditor_sha256", "heartbeat_checkpoint_audit.py"))}


def read_small(path):
    with path.open("rb") as stream:
        raw = stream.read(4 * 1024 * 1024 + 1)
    if len(raw) > 4 * 1024 * 1024:
        raise ValueError("Oversized evidence")
    return raw


def inspect(output, revision=None, current=None, stale_seconds=5):
    if type(stale_seconds) not in (int, float) or not 0 < stale_seconds < float("inf"):
        raise ValueError("Finite positive stale threshold")
    output = Path(output)
    manifest = decode(read_small(output / "manifest.json"))
    if not isinstance(manifest, dict) or set(manifest) != {"schema", "config", "identity"} or manifest["schema"] != "heartbeat02-v1":
        raise ValueError("Manifest schema")
    config, identity = manifest["config"], manifest["identity"]
    validate_config(config)
    keys = {"world_id", "source_revision", "config_sha256", "worker_sha256", "auditor_sha256", "python", "run_id"}
    if not isinstance(identity, dict) or set(identity) != keys or not isinstance(identity["world_id"], str) or not 1 <= len(identity["world_id"]) <= 200:
        raise ValueError("World identity schema")
    if not hex_string(identity["source_revision"], 40) or any(not hex_string(identity[k], 64) for k in ("config_sha256", "worker_sha256", "auditor_sha256", "run_id")):
        raise ValueError("Exact source and hashes required")
    if identity["config_sha256"] != digest(config) or identity["run_id"] != digest({k: v for k, v in identity.items() if k != "run_id"}):
        raise ValueError("Identity digest mismatch")
    if revision is not None and identity["source_revision"] != revision:
        raise ValueError("Source revision mismatch")
    if identity["python"] != platform.python_version() or any(identity[k] != v for k, v in source_hashes().items()):
        raise ValueError("Source files or Python mismatch")
    raw = read_small(output / "frames.jsonl")
    if not raw or not raw.endswith(b"\n"):
        raise ValueError("Missing genesis or partial journal; manual review required")
    frames = [decode(line) for line in raw.splitlines()]
    if not 1 <= len(frames) <= 1100:
        raise ValueError("Finite frame cap")
    previous, chain, previous_time = None, "0" * 64, None
    states = []
    frame_keys = {"schema", "seq", "epoch", "state", "state_sha256", "last_heartbeat", "status", "reason", "previous_sha256", "frame_sha256"}
    for index, frame in enumerate(frames):
        if not isinstance(frame, dict) or set(frame) != frame_keys or frame["schema"] != "heartbeat02-v1" or type(frame["seq"]) is not int or frame["seq"] != index:
            raise ValueError("Frame schema/sequence")
        if type(frame["epoch"]) is not int or not 0 <= frame["epoch"] <= 32:
            raise ValueError("Invocation epoch")
        state = frame["state"]
        if not isinstance(state, dict) or set(state) != {"run_id", "simulation_tick", "work", "heat"} or state["run_id"] != identity["run_id"]:
            raise ValueError("State identity/schema")
        if any(type(state[k]) is not int or state[k] < 0 for k in ("simulation_tick", "work", "heat")) or state["work"] + state["heat"] != config["work"]:
            raise ValueError("Counter conservation")
        if frame["state_sha256"] != digest(state) or frame["previous_sha256"] != chain or frame["frame_sha256"] != digest({k: v for k, v in frame.items() if k != "frame_sha256"}):
            raise ValueError("Hash chain")
        moment = utc(frame["last_heartbeat"])
        if previous_time is not None and moment < previous_time:
            raise ValueError("Backward heartbeat")
        status, reason = frame["status"], frame["reason"]
        if previous is None:
            if frame["epoch"] != 0 or (status, reason) != ("running", "ready") or state != {"run_id": identity["run_id"], "simulation_tick": 0, "work": config["work"], "heat": 0}:
                raise ValueError("Invalid genesis")
            states.append(state)
        else:
            old = previous["state"]
            if previous["status"] == "stopped":
                raise ValueError("History after terminal")
            if (status, reason) == ("running", "resumed"):
                if canonical(state) != canonical(old) or frame["epoch"] != previous["epoch"] + 1:
                    raise ValueError("Resume changed state/epoch")
            else:
                if frame["epoch"] != previous["epoch"] or previous["status"] != "running":
                    raise ValueError("Advance/status without admitted running epoch")
                if (status, reason) == ("running", "advanced"):
                    expected = {**old, "simulation_tick": old["simulation_tick"] + 1, "work": old["work"] - 1, "heat": old["heat"] + 1}
                    if old["work"] == 0 or old["simulation_tick"] >= config["max_ticks"] or canonical(state) != canonical(expected):
                        raise ValueError("Skipped/double/timer-only tick")
                    states.append(state)
                else:
                    permitted = ((status, reason) == ("paused", "operator_pause") or
                                 (status, reason) == ("stopped", "exhausted") and state["work"] == 0 or
                                 (status, reason) == ("stopped", "tick_limit") and state["work"] > 0 and state["simulation_tick"] == config["max_ticks"])
                    if not permitted or canonical(state) != canonical(old):
                        raise ValueError("False lifecycle/state-only transition")
        previous, chain, previous_time = frame, frame["frame_sha256"], moment
    checkpoint_path = output / "checkpoint.json"
    checkpoint = decode(read_small(checkpoint_path)) if checkpoint_path.exists() else None
    if checkpoint_path.exists():
        seq = checkpoint.get("seq") if isinstance(checkpoint, dict) else None
        if type(seq) is not int or not 0 <= seq < len(frames) or canonical(checkpoint) != canonical(frames[seq]):
            raise ValueError("Checkpoint not a committed prefix")
    current_time = datetime.now(timezone.utc) if current is None else utc(current)
    age = (current_time - previous_time).total_seconds()
    if age < 0:
        raise ValueError("Future heartbeat")
    status = frames[-1]["status"]
    observed = "stale" if status == "running" and age > stale_seconds else "reported_running" if status == "running" else status
    report = {**identity, "verified_simulation_tick": previous["state"]["simulation_tick"],
              "verified_state_sha256": digest(previous["state"]), "verified_frames": len(frames),
              "epoch": previous["epoch"], "reported_status": status, "observed_status": observed,
              "reason": previous["reason"], "heartbeat_age_seconds": age, "process_health": "unverified",
              "checkpoint_seq": None if checkpoint is None else checkpoint["seq"],
              "checkpoint_current": checkpoint is not None and checkpoint["seq"] == len(frames) - 1,
              "learning_claim": False, "population_continuity_verified": False}
    return {"manifest": manifest, "frames": frames, "states": states, "report": report}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--source-revision", required=True)
    parser.add_argument("--current-utc")
    args = parser.parse_args()
    try:
        print(json.dumps(inspect(args.input_dir, args.source_revision, args.current_utc)["report"], indent=2))
    except (ValueError, OSError, KeyError, TypeError) as exc:
        parser.exit(2, f"Rejected evidence: {exc}\n")
