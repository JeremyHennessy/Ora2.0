"""RUNTIME-01: bounded, manually invoked AL01-CAL checkpoint/restart pilot.

This is an engineering fixture, NOT an organism or autonomous runtime. It
imports the unchanged AL01-CAL reactor and tick law. No network access, external
model, GitHub interaction, scheduled execution or host-code generation.
See docs/RUNTIME-01-CHECKPOINT-PROTOCOL.md.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from dataclasses import asdict, fields
import hashlib
import json
import os
from pathlib import Path
import platform
import random
import re
import sys
import uuid

from experiments import chemical_calibration as cal

FORMAT = "ora2-runtime01-v1"
ZERO_HASH = "0" * 64
MAX_STEPS = 10000
ALLOWED_FAULTS = ("pre_commit", "post_journal", "post_checkpoint")


class IntegrityError(ValueError):
    """Run data corrupt, incomplete, source-mismatched or nonreplayable."""


def canonical(value: object) -> str:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )


def digest(value: object) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pack_rng(rng: random.Random) -> list:
    version, words, gaussian = rng.getstate()
    return [version, list(words), gaussian]


def unpack_rng(value: object) -> random.Random:
    if not isinstance(value, list) or len(value) != 3:
        raise IntegrityError("Invalid PRNG snapshot shape")
    if not isinstance(value[1], list) or len(value[1]) != 625:
        raise IntegrityError("Invalid PRNG state word count")
    if not isinstance(value[0], int) or not all(
        isinstance(word, int) for word in value[1]
    ):
        raise IntegrityError("Invalid PRNG state word type")
    generator = random.Random()
    try:
        generator.setstate((value[0], tuple(value[1]), value[2]))
    except (ValueError, TypeError) as exc:
        raise IntegrityError("PRNG snapshot cannot be restored") from exc
    return generator


def validate_reactor(payload: object, starting_mass: int) -> cal.Reactor:
    if not isinstance(payload, dict):
        raise IntegrityError("Reactor payload must be object")
    names = {f.name for f in fields(cal.Reactor)}
    if set(payload) != names or any(
        not isinstance(payload[name], int) or isinstance(payload[name], bool)
        for name in names
    ):
        raise IntegrityError("Reactor record schema/type mismatch")
    state = cal.Reactor(**payload)
    if state.steps < 0 or min(asdict(state).values()) < 0:
        raise IntegrityError("Invalid negative reactor counter")
    try:
        cal.assert_valid(state, starting_mass)
    except AssertionError as exc:
        raise IntegrityError(f"Reactor conservation invalid: {exc}") from exc
    return state


def make_identity(
    seed: int, variant: str, total_steps: int, checkpoint_every: int,
    revision: str,
) -> dict:
    if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
        raise ValueError("Seed must be a nonnegative integer")
    if variant not in cal.VARIANTS:
        raise ValueError("Unrecognized AL01 intervention")
    if not (isinstance(total_steps, int) and
            1 <= total_steps <= MAX_STEPS):
        raise ValueError(f"Pilot must have 1..{MAX_STEPS} bounded steps")
    if not (isinstance(checkpoint_every, int)
            and 1 <= checkpoint_every <= total_steps):
        raise ValueError("Invalid checkpoint cadence")
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("Exact lowercase Git commit SHA-1 required as revision")
    return {
        "schema": FORMAT,
        "seed": seed,
        "variant": variant,
        "total_steps": total_steps,
        "checkpoint_every": checkpoint_every,
        "revision": revision,
        "python": platform.python_version(),
        "platform": platform.system(),
        "al01_source_sha256": hash_file(Path(cal.__file__)),
        "runner_source_sha256": hash_file(Path(__file__)),
        "protocol": asdict(cal.Protocol()),
        "claim_limit": "bounded AL01-calibration fixture, not a living organism",
    }


def initial_state(identity: dict) -> tuple[cal.Reactor, random.Random, int]:
    p = cal.Protocol(**identity["protocol"])
    state = cal.Reactor(p.initial_s, p.initial_a, p.initial_b)
    mass = state.mass
    gen = random.Random(identity["seed"])
    cal.assert_valid(state, mass)
    return state, gen, mass


def fsync_directory(path: Path) -> None:
    """Best-effort directory metadata barrier: not a power-loss guarantee."""
    if os.name == "nt":
        # Windows Python cannot fsync directory handles with standard os.open.
        return
    try:
        fd = os.open(str(path), os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    except OSError:
        pass


def write_exact(handle, raw: bytes) -> None:
    """Never acknowledge or promote a partial successful authoritative write."""
    count = handle.write(raw)
    if type(count) is not int or count != len(raw):
        raise OSError("Incomplete authoritative write")


def atomic_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp-" + uuid.uuid4().hex)
    raw = (canonical(payload) + "\n").encode("utf-8")
    try:
        with temporary.open("xb") as handle:
            write_exact(handle, raw)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        fsync_directory(path.parent)
    finally:
        if temporary.exists():
            temporary.unlink()


@contextmanager
def writer_lock(folder: Path):
    """Best effort cross-platform single local writer, not a security boundary."""
    folder.mkdir(parents=True, exist_ok=True)
    lock_path = folder / ".writer.lock"
    with lock_path.open("a+b") as handle:
        if lock_path.stat().st_size == 0:
            handle.write(b"1")
            handle.flush()
            os.fsync(handle.fileno())
        handle.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise IntegrityError("Run directory already has an active writer") from exc
        try:
            yield
        finally:
            handle.seek(0)
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def wrapped(body: dict) -> dict:
    return {"body": body, "sha256": digest(body)}


def read_wrapped(path: Path, label: str) -> dict:
    try:
        data = json.loads(path.read_bytes())
    except (OSError, UnicodeError, ValueError) as exc:
        raise IntegrityError(f"{label} missing or invalid JSON") from exc
    if not isinstance(data, dict) or set(data) != {"body", "sha256"}:
        raise IntegrityError(f"{label} missing envelope fields")
    if data["sha256"] != digest(data["body"]):
        raise IntegrityError(f"{label} checksum mismatch")
    if not isinstance(data["body"], dict):
        raise IntegrityError(f"{label} payload must be object")
    return data


def read_journal(path: Path, identity_hash: str) -> list[dict]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise IntegrityError("Missing journal") from exc
    if raw and not raw.endswith(b"\n"):
        raise IntegrityError("Truncated journal tail (manual review required)")
    lines = raw.splitlines()
    records = []
    previous_hash = ZERO_HASH
    for index, raw_line in enumerate(lines, start=1):
        try:
            row = json.loads(raw_line)
        except (UnicodeError, ValueError) as exc:
            raise IntegrityError(f"Invalid journal JSON at step {index}") from exc
        if not isinstance(row, dict) or set(row) != {"body", "sha256"}:
            raise IntegrityError(f"Malformed journal envelope at step {index}")
        body = row["body"]
        if not isinstance(body, dict) or set(body) != {
            "step", "previous_hash", "manifest_sha256",
            "state", "state_sha256", "rng_sha256",
        }:
            raise IntegrityError(f"Journal record schema failure step {index}")
        if (body["step"] != index or
            body["previous_hash"] != previous_hash or
            body["manifest_sha256"] != identity_hash or
            row["sha256"] != digest(body) or
            body["state_sha256"] != digest(body["state"])):
            raise IntegrityError(f"Journal chain/hash mismatch at step {index}")
        previous_hash = row["sha256"]
        records.append(row)
    return records


def checkpoint_body(
    state: cal.Reactor, rng: random.Random, head_hash: str,
    identity_hash: str,
) -> dict:
    return {
        "step": state.steps, "state": asdict(state),
        "rng_state": pack_rng(rng), "journal_head": head_hash,
        "manifest_sha256": identity_hash,
    }


def begin_run(folder: Path, identity: dict) -> dict:
    unexpected = {
        p.name for p in folder.iterdir() if p.name != ".writer.lock"
    }
    if unexpected:
        raise IntegrityError(
            "Incomplete/unrecognized run directory without manifest; "
            "review manually, never silently re-seed"
        )
    manifest = wrapped(identity)
    state, rng, _ = initial_state(identity)
    # Bootstrap is committed by manifest LAST. Incomplete bootstraps fail closed.
    journal = folder / "journal.jsonl"
    with journal.open("xb") as handle:
        handle.flush()
        os.fsync(handle.fileno())
    atomic_json(
        folder / "checkpoint.json",
        wrapped(checkpoint_body(state, rng, ZERO_HASH, manifest["sha256"])),
    )
    atomic_json(folder / "manifest.json", manifest)
    return manifest


def restored(
    folder: Path, expected_identity: dict,
    *, full_verify: bool,
) -> tuple[dict, cal.Reactor, random.Random, list[dict], str, int]:
    manifest = read_wrapped(folder / "manifest.json", "Run manifest")
    if manifest["body"] != expected_identity:
        raise IntegrityError(
            "Immutable run identity changed (Git code, Python, seed, "
            "variant, horizon, checkpoint cadence or commit revision)"
        )
    records = read_journal(folder / "journal.jsonl", manifest["sha256"])
    if len(records) > expected_identity["total_steps"]:
        raise IntegrityError("Journal exceeds immutable bounded horizon")
    cp = read_wrapped(folder / "checkpoint.json", "Checkpoint")["body"]
    if set(cp) != {"step", "state", "rng_state",
                   "journal_head", "manifest_sha256"}:
        raise IntegrityError("Checkpoint schema mismatch")
    if cp["manifest_sha256"] != manifest["sha256"]:
        raise IntegrityError("Checkpoint points to different run manifest")
    checkpoint_step = cp["step"]
    if (not isinstance(checkpoint_step, int) or checkpoint_step < 0
        or checkpoint_step > len(records)):
        raise IntegrityError("Checkpoint step ahead of committed journal")
    expected_head = (
        records[checkpoint_step - 1]["sha256"] if checkpoint_step else ZERO_HASH
    )
    if expected_head != cp["journal_head"]:
        raise IntegrityError("Checkpoint journal-head mismatch")
    initial_state_for_mass, genesis_rng, mass = initial_state(expected_identity)
    if checkpoint_step == 0:
        if cp["state"] != asdict(initial_state_for_mass):
            raise IntegrityError("Genesis checkpoint state modified")
        if cp["rng_state"] != pack_rng(genesis_rng):
            raise IntegrityError("Genesis PRNG snapshot does not match declared seed")
    else:
        if cp["state"] != records[checkpoint_step - 1]["body"]["state"]:
            raise IntegrityError("Checkpoint state differs from committed journal")
    state = validate_reactor(cp["state"], mass)
    if state.steps != checkpoint_step:
        raise IntegrityError("Checkpoint step and reactor clock disagree")
    rng = unpack_rng(cp["rng_state"])
    if checkpoint_step and digest(pack_rng(rng)) != (
        records[checkpoint_step-1]["body"]["rng_sha256"]
    ):
        raise IntegrityError("Checkpoint PRNG state differs from journal")

    # Load last atomic checkpoint, then replay only the committed suffix.
    for row in records[checkpoint_step:]:
        cal.tick(state, rng, cal.Protocol(**expected_identity["protocol"]),
                 expected_identity["variant"], mass)
        if (
            row["body"]["state"] != asdict(state) or
            row["body"]["state_sha256"] != digest(asdict(state)) or
            row["body"]["rng_sha256"] != digest(pack_rng(rng))
        ):
            raise IntegrityError(
                f"Checkpoint-based journal replay diverged at step {state.steps}"
            )

    if full_verify:
        # Additional independent from-genesis validation of *all* steps, not
        # used to construct normal recovery; detection of corrupt early history.
        fresh, independent_rng, _ = initial_state(expected_identity)
        for row in records:
            cal.tick(fresh, independent_rng,
                     cal.Protocol(**expected_identity["protocol"]),
                     expected_identity["variant"], mass)
            if (
                row["body"]["state"] != asdict(fresh) or
                row["body"]["rng_sha256"] != digest(pack_rng(independent_rng))
            ):
                raise IntegrityError(
                    f"Full from-genesis audit diverged at {fresh.steps}"
                )
        if asdict(fresh) != asdict(state) or pack_rng(independent_rng) != pack_rng(rng):
            raise IntegrityError("Full audit differs from checkpoint-based replay")

    end_hash = records[-1]["sha256"] if records else ZERO_HASH
    return manifest, state, rng, records, end_hash, mass


def completion_body(
    manifest_hash: str, state: cal.Reactor,
    rng: random.Random, head_hash: str, source_revision: str,
) -> dict:
    return {
        "manifest_sha256": manifest_hash,
        "source_revision": source_revision,
        "final_step": state.steps,
        "final_state": asdict(state),
        "final_state_sha256": digest(asdict(state)),
        "final_rng_sha256": digest(pack_rng(rng)),
        "journal_head": head_hash,
        "journal_events": state.steps,
        "result_type": "bounded_recovery_fixture_not_artificial_life",
    }


def validate_receipt(
    folder: Path, manifest: dict, state: cal.Reactor,
    rng: random.Random, chain_head: str, revision: str,
) -> dict:
    receipt = read_wrapped(folder / "receipt.json", "Final receipt")
    expected = completion_body(
        manifest["sha256"], state, rng, chain_head, revision
    )
    if receipt["body"] != expected:
        raise IntegrityError("Final receipt differs from independently replayed state")
    return receipt


def record_step(
    folder: Path, manifest: dict, state: cal.Reactor,
    rng: random.Random, previous_head: str,
) -> str:
    state_payload = asdict(state)
    body = {
        "step": state.steps,
        "previous_hash": previous_head,
        "manifest_sha256": manifest["sha256"],
        "state": state_payload,
        "state_sha256": digest(state_payload),
        "rng_sha256": digest(pack_rng(rng)),
    }
    entry = wrapped(body)
    with (folder / "journal.jsonl").open("ab") as handle:
        write_exact(handle, (canonical(entry) + "\n").encode("utf-8"))
        handle.flush()
        os.fsync(handle.fileno())
    return entry["sha256"]


def run_pilot(
    folder: Path, *, seed: int, variant: str, steps: int,
    checkpoint_every: int, revision: str,
    verify_only: bool = False,
    fault_step: int | None = None,
    fault_point: str | None = None,
) -> dict:
    if fault_step is not None:
        if not 1 <= fault_step <= steps or fault_point not in ALLOWED_FAULTS:
            raise ValueError("Fault step/point invalid")
        if fault_point == "post_checkpoint" and (
            fault_step % checkpoint_every and fault_step != steps
        ):
            raise ValueError("Checkpoint fault must coincide with checkpoint step")
    elif fault_point is not None:
        raise ValueError("Fault point without step")
    folder = Path(folder)
    identity = make_identity(seed, variant, steps, checkpoint_every, revision)
    with writer_lock(folder):
        if not (folder / "manifest.json").exists():
            if verify_only:
                raise IntegrityError("Cannot verify: no committed run manifest")
            begin_run(folder, identity)
        manifest, state, rng, history, chain, mass = restored(
            folder, identity, full_verify=verify_only
        )
        complete = folder / "receipt.json"
        if complete.exists():
            if state.steps != steps:
                raise IntegrityError("Receipt exists for an unfinished run")
            if not verify_only:
                # Even normal repeated execution verifies its complete history.
                restored(folder, identity, full_verify=True)
            receipt = validate_receipt(folder, manifest, state, rng, chain, revision)
            return receipt["body"]
        if verify_only:
            raise IntegrityError("No finalized receipt: run is incomplete")
        if state.steps >= steps:
            # Crash after final checkpoint, before final receipt.
            pass
        for t in range(state.steps + 1, steps + 1):
            cal.tick(state, rng, cal.Protocol(**identity["protocol"]),
                     variant, mass)
            if fault_step == t and fault_point == "pre_commit":
                os._exit(77)  # test-only deliberate abrupt process exit
            chain = record_step(folder, manifest, state, rng, chain)
            if fault_step == t and fault_point == "post_journal":
                os._exit(78)
            if t % checkpoint_every == 0 or t == steps:
                atomic_json(
                    folder / "checkpoint.json",
                    wrapped(checkpoint_body(state, rng, chain, manifest["sha256"])),
                )
                if fault_step == t and fault_point == "post_checkpoint":
                    os._exit(79)
        # Independently replay from genesis before promoting any final receipt.
        manifest, state, rng, history, chain, mass = restored(
            folder, identity, full_verify=True
        )
        if state.steps != steps or len(history) != steps:
            raise IntegrityError("Completed run has incorrect journal length")
        receipt = wrapped(completion_body(
            manifest["sha256"], state, rng, chain, revision
        ))
        atomic_json(complete, receipt)
        return receipt["body"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--revision", required=True,
                        help="Exactly reviewed 40-digit lower-case Git commit SHA")
    parser.add_argument("--seed", type=int, default=1000)
    parser.add_argument("--variant", choices=cal.VARIANTS, default="intact")
    parser.add_argument("--steps", type=int, default=120)
    parser.add_argument("--checkpoint-every", type=int, default=10)
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--fault-step", type=int)
    parser.add_argument("--fault-point", choices=ALLOWED_FAULTS)
    args = parser.parse_args(argv)
    try:
        outcome = run_pilot(
            args.run_dir, seed=args.seed, variant=args.variant,
            steps=args.steps, checkpoint_every=args.checkpoint_every,
            revision=args.revision, verify_only=args.verify_only,
            fault_step=args.fault_step, fault_point=args.fault_point,
        )
    except (ValueError, IntegrityError, AssertionError) as exc:
        parser.exit(2, f"RUNTIME-01 refused operation: {exc}\n")
    print(canonical({
        "run_dir": str(args.run_dir),
        "final_step": outcome["final_step"],
        "final_state_sha256": outcome["final_state_sha256"],
        "final_rng_sha256": outcome["final_rng_sha256"],
        "journal_head": outcome["journal_head"],
        "status": "verified bounded process-recovery fixture only",
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
