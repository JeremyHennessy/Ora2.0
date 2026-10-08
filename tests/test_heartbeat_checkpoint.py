import copy
from datetime import datetime, timedelta
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from experiments import heartbeat_checkpoint as worker
from experiments import heartbeat_checkpoint_audit as audit

REVISION = "a" * 40


def bytes_tree(output):
    return {str(p.relative_to(output)): p.read_bytes() for p in output.rglob("*") if p.is_file()}


def cli(output, *extra):
    return [sys.executable, "-m", "experiments.heartbeat_checkpoint", "--output-dir", str(output),
            "--world-id", "counter", "--source-revision", REVISION, *extra]


def subprocess_run(args):
    return subprocess.run(args, capture_output=True, text=True, timeout=30)


def rechain(output, frames, checkpoint_index=-1):
    chain = "0" * 64
    for index, frame in enumerate(frames):
        frame["seq"] = index
        frame["previous_sha256"] = chain
        frame["state_sha256"] = audit.digest(frame["state"])
        frame["frame_sha256"] = audit.digest({k: v for k, v in frame.items() if k != "frame_sha256"})
        chain = frame["frame_sha256"]
    (output / "frames.jsonl").write_bytes(("".join(audit.canonical(f) + "\n" for f in frames)).encode())
    (output / "checkpoint.json").write_bytes((audit.canonical(frames[checkpoint_index]) + "\n").encode())


class HeartbeatCheckpointTests(unittest.TestCase):
    def test_actual_exit_boundaries_resume_exact_states_and_prefix(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            reference = root / "reference"
            worker.run(reference, "counter", REVISION)
            expected = audit.inspect(reference)["states"]
            for point, code in worker.FAULTS.items():
                with self.subTest(point=point):
                    output = root / point
                    result = subprocess_run(cli(output, "--fault-tick", "5", "--fault-point", point))
                    self.assertEqual(result.returncode, code, result.stderr)
                    prefix = (output / "frames.jsonl").read_bytes()
                    before = bytes_tree(output)
                    inspection = audit.inspect(output)
                    self.assertEqual(before, bytes_tree(output))
                    self.assertEqual(inspection["report"]["verified_simulation_tick"], 4 if point == "pre_commit" else 5)
                    self.assertEqual(inspection["report"]["checkpoint_current"], point in ("pre_commit", "post_checkpoint"))
                    self.assertEqual(subprocess_run(cli(output, "--resume")).returncode, 0)
                    self.assertTrue((output / "frames.jsonl").read_bytes().startswith(prefix))
                    self.assertEqual(audit.inspect(output)["states"], expected)
                    self.assertEqual(audit.inspect(output)["report"]["epoch"], 1)

    def test_repeated_exits_same_identity(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "world"
            for tick, point, resume in ((5, "pre_commit", False), (6, "post_journal", True), (7, "post_pending", True)):
                prefix = (output / "frames.jsonl").read_bytes() if resume else b""
                args = cli(output, "--fault-tick", str(tick), "--fault-point", point)
                if resume:
                    args += ["--resume"]
                self.assertEqual(subprocess_run(args).returncode, worker.FAULTS[point])
                self.assertTrue((output / "frames.jsonl").read_bytes().startswith(prefix))
                audit.inspect(output)
            self.assertEqual(subprocess_run(cli(output, "--resume")).returncode, 0)
            evidence = audit.inspect(output)
            self.assertEqual(evidence["report"]["epoch"], 3)
            self.assertEqual([s["simulation_tick"] for s in evidence["states"]], list(range(13)))
            self.assertEqual(evidence["states"][-1]["work"], 0)

    def test_pause_quota_empty_and_terminal_idempotence(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name, work, cap, pause, endpoint in (("pause", 12, 32, 5, 12), ("quota", 20, 7, None, 7), ("empty", 0, 32, None, 0)):
                output = root / name
                worker.run(output, "counter", REVISION, work, cap, pause_after=pause)
                if pause:
                    self.assertEqual(audit.inspect(output)["report"]["reported_status"], "paused")
                worker.run(output, "counter", REVISION, work, cap, resume=True)
                evidence = audit.inspect(output)
                self.assertEqual(evidence["report"]["verified_simulation_tick"], endpoint)
                self.assertEqual(evidence["report"]["reported_status"], "stopped")
                before = bytes_tree(output)
                worker.run(output, "counter", REVISION, work, cap, resume=True)
                self.assertEqual(bytes_tree(output), before)
            for point in worker.FAULTS:
                output = root / ("quota-" + point)
                result = subprocess_run(cli(output, "--work", "20", "--max-ticks", "7", "--fault-tick", "7", "--fault-point", point))
                self.assertEqual(result.returncode, worker.FAULTS[point])
                worker.run(output, "counter", REVISION, 20, 7, resume=True)
                self.assertEqual([s["simulation_tick"] for s in audit.inspect(output)["states"]], list(range(8)))

    def test_missing_and_lagging_checkpoint_rebuild_not_pending_trust(self):
        with tempfile.TemporaryDirectory() as temporary:
            for missing in (False, True):
                output = Path(temporary) / str(missing)
                worker.run(output, "counter", REVISION, pause_after=5)
                frames = audit.inspect(output)["frames"]
                if missing:
                    (output / "checkpoint.json").unlink()
                else:
                    (output / "checkpoint.json").write_text(audit.canonical(frames[2]))
                (output / "checkpoint.pending").write_bytes(b"untrusted garbage")
                self.assertFalse(audit.inspect(output)["report"]["checkpoint_current"])
                worker.run(output, "counter", REVISION, resume=True)
                self.assertTrue(audit.inspect(output)["report"]["checkpoint_current"])
                self.assertEqual(audit.inspect(output)["report"]["verified_simulation_tick"], 12)

    def test_rejected_resumes_do_not_mutate(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name in ("config", "revision", "world", "python", "source", "tail", "checkpoint-ahead", "checkpoint-wrong", "checkpoint-null", "checkpoint-corrupt", "genesis", "manifest"):
                output = root / name
                worker.run(output, "counter", REVISION, pause_after=5)
                frames = audit.inspect(output)["frames"]
                args = {}
                if name == "config":
                    args["work"] = 13
                elif name == "revision":
                    args["revision"] = "b" * 40
                elif name == "world":
                    args["world_id"] = "replacement"
                elif name in ("python", "source"):
                    manifest = json.loads((output / "manifest.json").read_bytes())
                    manifest["identity"]["python" if name == "python" else "worker_sha256"] = "0" if name == "python" else "0" * 64
                    manifest["identity"]["run_id"] = audit.digest({k: v for k, v in manifest["identity"].items() if k != "run_id"})
                    (output / "manifest.json").write_text(audit.canonical(manifest))
                elif name == "tail":
                    with (output / "frames.jsonl").open("ab") as stream:
                        stream.write(b'{"partial":')
                elif name.startswith("checkpoint"):
                    value = copy.deepcopy(frames[-1])
                    if name == "checkpoint-ahead":
                        value["seq"] += 1
                    elif name == "checkpoint-wrong":
                        value["state"]["work"] += 1
                    raw = "null" if name == "checkpoint-null" else "{" if name == "checkpoint-corrupt" else audit.canonical(value)
                    (output / "checkpoint.json").write_text(raw)
                elif name == "genesis":
                    (output / "frames.jsonl").write_bytes(b"")
                elif name == "manifest":
                    (output / "manifest.json").write_text('{"schema":"heartbeat02-v1","schema":"duplicate"}')
                before = bytes_tree(output)
                with self.subTest(name=name), self.assertRaises((ValueError, KeyError)):
                    worker.run(output, args.get("world_id", "counter"), args.get("revision", REVISION), work=args.get("work", 12), resume=True)
                self.assertEqual(bytes_tree(output), before)

    def test_rehashed_semantic_forgeries_and_stale_read_only(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name in ("skip", "double", "timer", "energy", "bool", "epoch", "false-stop", "after-stop", "backward", "identity"):
                output = root / name
                worker.run(output, "counter", REVISION)
                frames = audit.inspect(output)["frames"]
                if name == "skip":
                    frames.pop(3)
                elif name == "double":
                    frames.insert(3, copy.deepcopy(frames[3]))
                elif name == "timer":
                    frames[3]["state"]["work"] += 1
                    frames[3]["state"]["heat"] -= 1
                elif name == "energy":
                    frames[3]["state"]["heat"] += 1
                elif name == "bool":
                    frames[1]["state"]["simulation_tick"] = True
                elif name == "epoch":
                    frames[3]["epoch"] = 1
                elif name == "false-stop":
                    frames[3]["status"], frames[3]["reason"] = "stopped", "exhausted"
                elif name == "after-stop":
                    frames.append(copy.deepcopy(frames[-1]))
                elif name == "backward":
                    frames[3]["last_heartbeat"] = (datetime.fromisoformat(frames[2]["last_heartbeat"]) - timedelta(seconds=1)).isoformat()
                elif name == "identity":
                    frames[3]["state"]["run_id"] = "b" * 64
                rechain(output, frames)
                with self.subTest(name=name), self.assertRaises(ValueError):
                    audit.inspect(output)
            output = root / "stale"
            self.assertEqual(subprocess_run(cli(output, "--fault-tick", "5", "--fault-point", "post_journal")).returncode, 78)
            before = bytes_tree(output)
            moment = json.loads((output / "frames.jsonl").read_text().splitlines()[-1])["last_heartbeat"]
            current = (datetime.fromisoformat(moment) + timedelta(seconds=6)).isoformat()
            evidence = audit.inspect(output, current=current)
            self.assertEqual(evidence["report"]["observed_status"], "stale")
            self.assertFalse(evidence["report"]["checkpoint_current"])
            self.assertEqual(evidence["report"]["verified_simulation_tick"], 5)
            self.assertEqual(bytes_tree(output), before)

    def test_real_competing_resume_process_rejected_without_mutation(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "world"
            worker.run(output, "counter", REVISION, pause_after=5)
            before = bytes_tree(output)
            holder = "import sys; from pathlib import Path; from experiments.heartbeat_checkpoint import writer_lock;\nwith writer_lock(Path(sys.argv[1])):\n print('locked',flush=True); sys.stdin.readline()"
            with subprocess.Popen([sys.executable, "-c", holder, str(output)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) as process:
                try:
                    self.assertEqual(process.stdout.readline().strip(), "locked")
                    result = subprocess_run(cli(output, "--resume"))
                    self.assertEqual(result.returncode, 2)
                    # Windows byte locks also block reads of the locked byte.
                    self.assertEqual({k: v for k, v in before.items() if k != "writer.lock"},
                                     {p.name: p.read_bytes() for p in output.iterdir() if p.name != "writer.lock"})
                finally:
                    process.communicate("release\n", timeout=10)
            self.assertEqual(before, bytes_tree(output))
            worker.run(output, "counter", REVISION, resume=True)
            self.assertEqual(audit.inspect(output)["report"]["verified_simulation_tick"], 12)

    def test_finite_resume_cap_and_invalid_controls_without_mutation(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "world"
            worker.run(output, "counter", REVISION, 40, 100, pause_after=1)
            for tick in range(2, 34):
                worker.run(output, "counter", REVISION, 40, 100, resume=True, pause_after=tick)
            self.assertEqual(audit.inspect(output)["report"]["epoch"], 32)
            before = bytes_tree(output)
            with self.assertRaises(ValueError):
                worker.run(output, "counter", REVISION, 40, 100, resume=True)
            self.assertEqual(before, bytes_tree(output))
            for config in ({"work": True}, {"max_ticks": 0}, {"fault_tick": 5}, {"fault_point": "post_journal"}, {"pause_after": 13}):
                with self.subTest(config=config), self.assertRaises(ValueError):
                    worker.run(output, "counter", REVISION, resume=True, **config)
                self.assertEqual(before, bytes_tree(output))


if __name__ == "__main__":
    unittest.main()
