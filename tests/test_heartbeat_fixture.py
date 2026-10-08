import copy
import json
from pathlib import Path
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from datetime import timedelta
from experiments import heartbeat_fixture as worker
from experiments import heartbeat_observer as observer


def rewrite(path, frames):
    chain = "0"*64
    for f in frames:
        f["state_sha256"] = observer.digest(f["state"])
        f["previous_sha256"] = chain
        f["frame_sha256"] = observer.digest({k:v for k,v in f.items() if k != "frame_sha256"})
        chain = f["frame_sha256"]
    (path/"frames.jsonl").write_text("".join(observer.canonical(f)+"\n" for f in frames), encoding="utf-8")
    (path/"latest.json").write_text(observer.canonical(frames[-1])+"\n", encoding="utf-8")


class HeartbeatTests(unittest.TestCase):
    def test_two_simultaneous_writers_admit_exactly_one_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            path, barrier = Path(tmp)/"competing", Barrier(2)
            def launch(name):
                barrier.wait(timeout=10)
                return worker.run(path,name,"a"*40,4,4)
            with ThreadPoolExecutor(max_workers=2) as pool:
                futures = [pool.submit(launch,name) for name in ("one","two")]
                admitted, rejected = [], 0
                for future in futures:
                    try:
                        admitted.append(future.result(timeout=20))
                    except FileExistsError:
                        rejected += 1
            self.assertEqual((len(admitted),rejected),(1,1))
            report = observer.inspect(path)
            self.assertEqual(report["world_id"],admitted[0]["state"]["world_id"])
            self.assertEqual(report["verified_simulation_tick"],4)

    def test_energy_pause_quota_identity_and_read_only_observer(self):
        with tempfile.TemporaryDirectory() as tmp:
            for name, work, ticks, pause, final, status in (("energy",12,32,None,12,"stopped"),("pause",12,32,5,5,"paused"),("quota",20,7,None,7,"stopped"),("empty",0,32,None,0,"stopped")):
                path = Path(tmp)/name
                last = worker.run(path,name,"a"*40,work,ticks,pause)
                before = {p.name:p.read_bytes() for p in path.iterdir()}
                report = observer.inspect(path,last["last_heartbeat"])
                self.assertEqual(report["verified_simulation_tick"],final)
                self.assertEqual(report["observed_status"],status)
                self.assertEqual(before,{p.name:p.read_bytes() for p in path.iterdir()})
                self.assertFalse((path/"writer.lock").exists())
                with self.assertRaises(FileExistsError):
                    worker.run(path,name,"a"*40)

    def test_stale_running_and_recent_frame_are_not_process_health(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/"run"
            worker.run(path,"world","a"*40,12,32)
            frames = [json.loads(x) for x in (path/"frames.jsonl").read_text().splitlines()][:2]
            rewrite(path,frames)
            moment = observer.timestamp(frames[-1]["last_heartbeat"])
            report = observer.inspect(path,(moment+timedelta(seconds=6)).isoformat())
            self.assertEqual(report["observed_status"],"stale")
            self.assertEqual(report["verified_simulation_tick"],1)
            self.assertEqual(observer.inspect(path,moment.isoformat())["process_health"],"unverified")

    def test_coherently_rehashed_timer_energy_and_identity_forgeries(self):
        for change in ("timer", "skip", "energy", "identity", "boolean", "false_stop", "config", "backward"):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp)/"run"
                worker.run(path,"world","a"*40)
                frames = [json.loads(x) for x in (path/"frames.jsonl").read_text().splitlines()]
                if change == "timer":
                    frames[1]["state"] = copy.deepcopy(frames[0]["state"])
                elif change == "skip":
                    frames[1]["state"]["simulation_tick"] = 2
                elif change == "energy":
                    frames[1]["state"]["work"] += 1
                elif change == "identity":
                    frames[1]["state"]["world_id"] = "replacement"
                elif change == "boolean":
                    frames[1]["state"]["simulation_tick"] = True
                elif change == "false_stop":
                    frames[1].update(status="stopped",reason="exhausted")
                elif change == "config":
                    frames[1]["config"] = {**frames[1]["config"],"work":100}
                else:
                    frames[1]["last_heartbeat"] = "2000-01-01T00:00:00+00:00"
                rewrite(path,frames)
                with self.assertRaises(ValueError):
                    observer.inspect(path)

    def test_corruption_mismatched_snapshot_and_future_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/"run"
            last = worker.run(path,"world","a"*40)
            original = (path/"latest.json").read_bytes()
            bad = json.loads(original)
            bad["status"] = "running"
            (path/"latest.json").write_text(json.dumps(bad),encoding="utf-8")
            with self.assertRaises(ValueError):
                observer.inspect(path)
            (path/"latest.json").write_bytes(original)
            with self.assertRaises(ValueError):
                observer.inspect(path,"2000-01-01T00:00:00+00:00")
            with (path/"frames.jsonl").open("ab") as f:
                f.write(b"corrupt")
            with self.assertRaises(ValueError):
                observer.inspect(path)


if __name__ == "__main__":
    unittest.main()
