"""SQLite boundary checks;synthetic fixtures only,no models or live stores."""
import sys,sqlite3,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments.ora_live_task_bounds_v1 import task_bounds


class Bounds(unittest.TestCase):
    def db(self,counts):
        db=sqlite3.connect(':memory:');self.addCleanup(db.close)
        db.execute('CREATE TABLE tasks(state TEXT)')
        for state,count in counts.items():db.executemany('INSERT INTO tasks VALUES(?)',[(state,)]*count)
        return db

    def test_128_done_plus_pending_is_valid(self):
        self.assertEqual(task_bounds(self.db({'done':128,'pending':1}))['total'],129)

    def test_full_existing_two_bounds_are_valid(self):
        v=task_bounds(self.db({'done':128,'pending':127,'running':1}));self.assertEqual(v['total'],256)

    def test_done_bound_not_relaxed(self):
        with self.assertRaises(ValueError):task_bounds(self.db({'done':129}))

    def test_pending_and_running_share_one_bound(self):
        with self.assertRaises(ValueError):task_bounds(self.db({'pending':128,'running':1}))

    def test_unknown_state_refused(self):
        with self.assertRaises(ValueError):task_bounds(self.db({'mystery':1}))

    def test_empty_and_completed_only(self):
        self.assertEqual(task_bounds(self.db({}))['total'],0)
        self.assertEqual(task_bounds(self.db({'done':128}))['done'],128)

    def test_full_checker_parses_without_live_import(self):
        import ast
        ast.parse((Path(__file__).resolve().parents[1]/'experiments/ora_runtime_health_review_v8.py').read_bytes())


if __name__=='__main__':unittest.main()
