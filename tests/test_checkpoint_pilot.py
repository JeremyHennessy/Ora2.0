"""RUNTIME-01 recovery, corruption and native abrupt-subprocess tests.

No local user's D: drive, paid service, cloud instance, or private data needed.
Local Codex must independently repeat them on Windows/Python 3.12.10.
"""
from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from experiments import chemical_calibration as cal
from experiments.checkpoint_pilot import (
    IntegrityError, canonical, digest, make_identity, pack_rng,
    run_pilot, writer_lock,
)

REVISION = "a" * 40


def local(folder, *, steps=60, cadence=10, seed=1000, revision=REVISION,
          verify_only=False):
    return run_pilot(
        folder, seed=seed, variant="intact", steps=steps,
        checkpoint_every=cadence, revision=revision,
        verify_only=verify_only,
    )


def command(folder, *, steps=60, cadence=10, fault_step=None, fault_point=None):
    parts = [
        sys.executable, "-m", "experiments.checkpoint_pilot",
        "--run-dir", str(folder), "--revision", REVISION,
        "--seed", "1000", "--variant", "intact",
        "--steps", str(steps), "--checkpoint-every", str(cadence),
    ]
    if fault_step is not None:
        parts.extend(("--fault-step", str(fault_step),
                      "--fault-point", fault_point))
    return parts


def saved_bytes(folder):
    return {
        name: (folder / name).read_bytes() for name in
        ("manifest.json", "checkpoint.json", "journal.jsonl", "receipt.json")
    }


class DeterministicFixtureTests(unittest.TestCase):
    def test_matches_existing_AL01_transition_code_not_new_physics(self):
        with tempfile.TemporaryDirectory() as td:
            result = local(Path(td), steps=12, cadence=5)
            state = cal.Reactor(35, 10, 10)
            rng = random.Random(1000)
            for _ in range(12):
                cal.tick(state, rng, cal.Protocol(), "intact", 55)
            self.assertEqual(result["final_state"], asdict(state))
            self.assertEqual(result["final_rng_sha256"], digest(pack_rng(rng)))
            self.assertEqual(result["final_step"], 12)
            self.assertEqual(result["journal_events"], 12)
            self.assertEqual(cal.assert_valid(state, 55), 0)

    def test_completed_run_is_immutable_and_idempotent(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            a = local(root, steps=22, cadence=5)
            before = saved_bytes(root)
            b = local(root, steps=22, cadence=5)
            self.assertEqual(a, b)
            self.assertEqual(saved_bytes(root), before)
            self.assertEqual(local(root, steps=22, cadence=5,
                                   verify_only=True), a)
            self.assertEqual(saved_bytes(root), before)

    def test_step_zero_checkpoints_are_not_treated_as_completed_runs(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            # Fault at the very first step after computation but before commit.
            p = subprocess.run(
                command(root, steps=10, fault_step=1, fault_point="pre_commit"),
                cwd=Path(__file__).resolve().parents[1], capture_output=True,
                text=True, check=False, timeout=40,
            )
            self.assertEqual(p.returncode, 77, p.stderr)
            manifest = json.loads((root / "manifest.json").read_text())
            cp = json.loads((root / "checkpoint.json").read_text())
            self.assertEqual(cp["body"]["step"], 0)
            self.assertTrue(manifest["sha256"])
            self.assertEqual((root / "journal.jsonl").read_bytes(), b"")
            with self.assertRaisesRegex(IntegrityError, "No finalized receipt"):
                local(root, steps=10, verify_only=True)
            self.assertEqual(local(root, steps=10)["final_step"], 10)

    def test_revision_or_settings_mismatch_never_overwrites(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            local(root, steps=15, cadence=5)
            before = saved_bytes(root)
            with self.assertRaisesRegex(IntegrityError, "Immutable run identity"):
                local(root, steps=15, cadence=5, revision="b"*40)
            with self.assertRaisesRegex(IntegrityError, "Immutable run identity"):
                local(root, steps=16, cadence=5)
            with self.assertRaisesRegex(IntegrityError, "Immutable run identity"):
                local(root, steps=15, cadence=5, seed=1001)
            self.assertEqual(saved_bytes(root), before)

    def test_python_patch_or_runner_identity_mismatch_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            local(root, steps=10)
            with patch("experiments.checkpoint_pilot.platform.python_version",
                       return_value="999.0.0"):
                with self.assertRaisesRegex(IntegrityError, "Immutable run identity"):
                    local(root, steps=10)

    def test_missing_or_partial_bootstrap_must_not_reseed_silently(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            with self.assertRaisesRegex(IntegrityError, "no committed run manifest"):
                local(root, steps=12, verify_only=True)
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "journal.jsonl").write_text("")
            with self.assertRaisesRegex(IntegrityError, "Incomplete/unrecognized"):
                local(root, steps=12)

    def test_journal_records_monotonic_and_hash_chained(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            receipt = local(root, steps=31, cadence=7)
            records = [json.loads(line) for line in
                       (root / "journal.jsonl").read_text().splitlines()]
            self.assertEqual(len(records), 31)
            self.assertEqual([r["body"]["step"] for r in records],
                             list(range(1, 32)))
            self.assertEqual(
                [r["body"]["previous_hash"] for r in records[1:]],
                [r["sha256"] for r in records[:-1]]
            )
            self.assertEqual(records[-1]["sha256"], receipt["journal_head"])


class AbruptCrashProcessTests(unittest.TestCase):
    def test_three_separate_native_process_exit_points_recover_exact_baseline(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            cold = base / "uninterrupted"
            receipt = local(cold)
            expected = saved_bytes(cold)
            for label, step, point, exit_code in [
                ("before_commit", 37, "pre_commit", 77),
                ("after_journal", 43, "post_journal", 78),
                ("after_checkpoint", 50, "post_checkpoint", 79),
            ]:
                with self.subTest(failure=label):
                    root = base / label
                    killed = subprocess.run(
                        command(root, fault_step=step, fault_point=point),
                        cwd=Path(__file__).resolve().parents[1],
                        capture_output=True, text=True,
                        check=False, timeout=40,
                    )
                    self.assertEqual(killed.returncode, exit_code, killed.stderr)
                    self.assertFalse((root / "receipt.json").exists())
                    # Missing volatile state is reconstructed from last atomic
                    # checkpoint plus the committed journal suffix, and audited.
                    restored = local(root)
                    self.assertEqual(restored, receipt)
                    self.assertEqual(saved_bytes(root), expected)
                    self.assertEqual(local(root, verify_only=True), receipt)

    def test_retry_on_completed_run_has_no_new_journal_events(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            subprocess.run(command(root), capture_output=True, check=True,
                           cwd=Path(__file__).resolve().parents[1], timeout=40)
            before = saved_bytes(root)
            subprocess.run(command(root), capture_output=True, check=True,
                           cwd=Path(__file__).resolve().parents[1], timeout=40)
            self.assertEqual(before, saved_bytes(root))


class CorruptionAndLockTests(unittest.TestCase):
    def test_partial_trailing_journal_record_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            local(root, steps=12)
            path = root / "journal.jsonl"
            path.write_bytes(path.read_bytes()[:-1])
            with self.assertRaisesRegex(IntegrityError, "Truncated journal tail"):
                local(root, steps=12, verify_only=True)

    def test_corrupted_history_refused_even_when_recent_checkpoint_valid(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            local(root, steps=12)
            path = root / "journal.jsonl"
            data = path.read_text()
            path.write_text("X" + data[1:], encoding="utf-8")
            with self.assertRaisesRegex(IntegrityError, "Invalid journal JSON"):
                local(root, steps=12, verify_only=True)

    def test_edited_checkpoint_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            local(root, steps=12)
            cp = root / "checkpoint.json"
            d = json.loads(cp.read_text())
            d["body"]["state"]["a"] += 1
            cp.write_text(canonical(d)+"\n", encoding="utf-8")
            with self.assertRaisesRegex(IntegrityError, "Checkpoint checksum"):
                local(root, steps=12, verify_only=True)

    def test_genesis_rng_does_not_accept_rehashed_seed_tamper(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            crashed = subprocess.run(
                command(root, steps=10, fault_step=1, fault_point="pre_commit"),
                cwd=Path(__file__).resolve().parents[1],
                capture_output=True, check=False, timeout=40,
            )
            self.assertEqual(crashed.returncode, 77)
            cp_path = root / "checkpoint.json"
            envelope = json.loads(cp_path.read_text())
            envelope["body"]["rng_state"][1][0] += 1
            # Recompute ordinary SHA256 to ensure checks do not just trust an
            # internally consistent but forged step-zero checkpoint.
            envelope["sha256"] = digest(envelope["body"])
            cp_path.write_text(canonical(envelope) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(IntegrityError, "Genesis PRNG snapshot"):
                local(root, steps=10)

    def test_wrong_journal_suffix_even_if_attacker_rehashes_one_record_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            killed = subprocess.run(
                command(root, fault_step=43, fault_point="post_journal"),
                cwd=Path(__file__).resolve().parents[1], capture_output=True,
                check=False, timeout=40,
            )
            self.assertEqual(killed.returncode, 78)
            file = root / "journal.jsonl"
            rows = [json.loads(x) for x in file.read_text().splitlines()]
            # At a checkpoint every 10 steps, only the suffix (41:43) will be
            # deterministically replayed. A forged internally hashed record
            # must not pass merely because the JSON hash is valid.
            row = rows[-1]
            row["body"]["state"]["a"] += 1
            row["body"]["state_sha256"] = digest(row["body"]["state"])
            row["sha256"] = digest(row["body"])
            file.write_text("".join(canonical(r)+"\n" for r in rows))
            with self.assertRaisesRegex(IntegrityError, "replay diverged"):
                local(root)

    def test_file_lock_blocks_second_writer_and_releases_for_restart(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            with writer_lock(root):
                with self.assertRaisesRegex(IntegrityError, "active writer"):
                    local(root, steps=12)
            self.assertEqual(local(root, steps=12)["final_step"], 12)

    def test_bad_shas_and_unbounded_horizons_are_not_allowed(self):
        with self.assertRaises(ValueError):
            make_identity(0, "intact", 12, 5, "unspecified")
        with self.assertRaises(ValueError):
            make_identity(0, "intact", 20000, 5, REVISION)
        with self.assertRaises(ValueError):
            make_identity(0, "intact", 10, 11, REVISION)


if __name__ == "__main__":
    unittest.main()
